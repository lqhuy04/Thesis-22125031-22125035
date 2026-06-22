"""
aggregator.py — Aggregator Agent (simplified)

Đọc output từ technical_analysis_agent, tổng hợp và đưa ra quyết định Mua/Chờ.
Rule: total_score >= 3/5 → Mua, ngược lại → Chờ.

Confidence được tính deterministic trong Python (không để LLM tự sinh),
dựa trên các nguồn THỰC SỰ có dữ liệu, với trọng số bằng nhau:

  confidence = Σ (wᵢ * componentᵢ)   chỉ tính trên nguồn đang hoạt động
             ─────────────────────
                  Σ wᵢ              (renormalize trên nguồn đang hoạt động)

    technical_component   = technical_score / max_score
    fundamental_component = strong=1.0 / neutral=0.5 / weak=0.0
    article_component     = positive=1.0 / neutral=0.5 / negative=0.0

Nguồn bị người dùng tắt hoặc không có dữ liệu (has_*_data = false) sẽ bị LOẠI
khỏi công thức và trọng số của nó được chia đều lại cho các nguồn còn lại. Nhờ
vậy mỗi nguồn còn hoạt động dùng đủ dải [0,1] thay vì bị kéo về 0.5 bởi các ô
trung lập. Khi chỉ còn 1 nguồn → confidence = component của chính nguồn đó.

  Ngưỡng chấp nhận lệnh Mua: confidence >= CONFIDENCE_THRESHOLD (0.55)
"""

import json
import math
from typing import Literal
from pydantic import BaseModel, Field

from agentic_ai.service.openai_service import _get_openai_client
from agentic_ai.analyze.state import AgentState
from agentic_ai.analyze.horizon import enforce_price_boundaries

# Raised by the OpenAI SDK when structured parsing fails because the model hit
# the output token cap (finish_reason = "length"). Tuple fallback for older SDKs
# makes `except _LengthError` a no-op rather than a NameError.
try:
    from openai import LengthFinishReasonError as _LengthError
except ImportError:  # pragma: no cover
    _LengthError = ()

# Bound the aggregator output. Plenty for the 4 analysis fields + signals, while
# preventing a degenerate repetition loop from running to the model's 16k cap.
_MAX_OUTPUT_TOKENS = 3000


# ─────────────────────────────────────────────────────────────
# ⚙️ Confidence Config
# ─────────────────────────────────────────────────────────────

# Ngưỡng tối thiểu để chấp nhận lệnh Mua
CONFIDENCE_THRESHOLD = 0.55

# Tỷ lệ điểm kỹ thuật tối thiểu để cân nhắc Mua (3/5 = 0.6 — giữ tương thích khi bật đủ 5 chỉ số)
BUY_SCORE_RATIO = 0.6

# Trọng số từng nguồn (bằng nhau, tổng = 1.0)
CONFIDENCE_WEIGHTS = {
    "technical":   1 / 3,
    "fundamental": 1 / 3,
    "article":     1 / 3,
}

# Điểm trung lập khi nguồn thiếu dữ liệu (N/A)
_NA_SCORE = 0.5

# Các chuỗi đánh dấu "không có dữ liệu thực sự" cho fundamental/news.
# Dùng để tính cờ has_*_data, tránh để LLM tự đoán.
_NO_DATA_MARKERS = (
    "Người dùng đã tắt",
    "Tạm ngưng",
    "Không có dữ liệu",
    "Không có bài viết",
    "Không có tin tức",
)


def _has_content(text) -> bool:
    """True nếu text chứa nội dung phân tích thật (không phải câu báo thiếu dữ liệu)."""
    s = str(text).strip() if text is not None else ""
    if not s:
        return False
    return not any(marker in s for marker in _NO_DATA_MARKERS)

# Map nhãn → điểm
_FUNDAMENTAL_SCORE_MAP: dict[str, float] = {
    "strong":  1.0,
    "neutral": 0.5,
    "weak":    0.0,
    "N/A":     _NA_SCORE,
}

_ARTICLE_SCORE_MAP: dict[str, float] = {
    "positive": 1.0,
    "neutral":  0.5,
    "negative": 0.0,
    "N/A":      _NA_SCORE,
}


def _confidence_components(
    technical_score: int,
    fundamental_health: str,
    article_sentiment: str,
    technical_max_score: int = 5,
) -> tuple[float, float, float]:
    """
    Trả về 3 thành phần điểm chuẩn hóa [0.0, 1.0]:
      (technical_component, fundamental_component, article_component)

      technical_component   = technical_score / technical_max_score
      fundamental_component = _FUNDAMENTAL_SCORE_MAP[fundamental_health]
      article_component     = _ARTICLE_SCORE_MAP[article_sentiment]

    technical_max_score = số chỉ số kỹ thuật người dùng bật (mặc định 5).
    Nếu người dùng tắt hết chỉ số kỹ thuật (max = 0) → coi technical là trung lập (0.5).

    Khi nguồn thiếu dữ liệu (N/A) → dùng _NA_SCORE = 0.5 (trung lập).
    """
    if technical_max_score and technical_max_score > 0:
        technical_component = max(0.0, min(technical_score, technical_max_score)) / float(technical_max_score)
    else:
        technical_component = _NA_SCORE
    fundamental_component = _FUNDAMENTAL_SCORE_MAP.get(fundamental_health, _NA_SCORE)
    article_component     = _ARTICLE_SCORE_MAP.get(article_sentiment, _NA_SCORE)

    return technical_component, fundamental_component, article_component


def _effective_weights(
    has_technical: bool,
    has_fundamental: bool,
    has_article: bool,
) -> dict[str, float]:
    """
    Trọng số HIỆU DỤNG sau khi loại các nguồn người dùng tắt / không có dữ liệu.

    Trọng số gốc của các nguồn bị loại được chia đều lại (renormalize) cho các
    nguồn còn hoạt động, nên tổng trọng số hiệu dụng luôn = 1.0 khi có ≥ 1 nguồn.
    Nguồn bị loại có trọng số 0.0 → không đóng góp vào confidence.

    Nếu không nguồn nào hoạt động (về lý thuyết không xảy ra vì technical bắt
    buộc) → trả về toàn 0.0 (caller sẽ coi confidence là trung lập).
    """
    active = {
        "technical":   has_technical,
        "fundamental": has_fundamental,
        "article":     has_article,
    }
    raw_total = sum(CONFIDENCE_WEIGHTS[k] for k, on in active.items() if on)
    if raw_total <= 0:
        return {k: 0.0 for k in CONFIDENCE_WEIGHTS}
    return {
        k: (CONFIDENCE_WEIGHTS[k] / raw_total if active[k] else 0.0)
        for k in CONFIDENCE_WEIGHTS
    }


def _compute_confidence(
    technical_score: int,
    fundamental_health: str,
    article_sentiment: str,
    has_technical: bool,
    has_fundamental: bool,
    has_article: bool,
    technical_max_score: int = 5,
) -> tuple[float, dict[str, float]]:
    """
    Tính confidence score [0.0, 1.0] hoàn toàn bằng rule cứng, chỉ trên các nguồn
    THỰC SỰ có dữ liệu (has_* = true). Trọng số được renormalize trên nguồn hoạt
    động. Xem _confidence_components và _effective_weights.

    Trả về (confidence, effective_weights) để caller báo cáo lại trong breakdown.
    """
    technical_component, fundamental_component, article_component = _confidence_components(
        technical_score, fundamental_health, article_sentiment, technical_max_score
    )

    w = _effective_weights(has_technical, has_fundamental, has_article)
    if sum(w.values()) <= 0:
        # Không nguồn nào hoạt động → trung lập hoàn toàn.
        return _NA_SCORE, w

    score = (
        w["technical"]   * technical_component
        + w["fundamental"] * fundamental_component
        + w["article"]     * article_component
    )

    return round(score, 4), w


# ─────────────────────────────────────────────────────────────
# 📦 Structured Output Schema
# ─────────────────────────────────────────────────────────────

class AnalysisBreakdown(BaseModel):
    technical: str = Field(
        description=(
            "Phân tích kỹ thuật bằng tiếng Việt. Nếu has_technical_data = true: BẮT BUỘC đi qua từng "
            "chỉ số CÓ trong dữ liệu (RSI, MA, Bollinger Bands, MACD, KDJ), nêu Tích cực/Tiêu cực, lý do, "
            "dẫn chứng số liệu — KHÔNG được nói không có dữ liệu dù điểm thấp. "
            "Chỉ khi has_technical_data = false mới ghi: 'Không có dữ liệu phân tích kỹ thuật.'"
        )
    )
    fundamental: str = Field(
        description=(
            "Phân tích cơ bản bằng tiếng Việt. Nếu has_fundamental_data = true: BẮT BUỘC tóm tắt các nhóm "
            "chỉ số CÓ trong dữ liệu (định giá, sinh lời, tăng trưởng, sức khỏe tài chính, dòng tiền). "
            "Chỉ khi has_fundamental_data = false mới ghi: 'Không có dữ liệu phân tích cơ bản.'"
        )
    )
    news: str = Field(
        description=(
            "Phân tích tin tức bằng tiếng Việt: tóm tắt và nhắc tới thông tin nổi bật. "
            "Chỉ khi has_news_data = false mới ghi: 'Không có dữ liệu tin tức.'"
        )
    )
    summary: str = Field(
        description=(
            "Kết luận tổng hợp ĐỊNH TÍNH bằng tiếng Việt. TUYỆT ĐỐI KHÔNG nêu con số giá mua / "
            "chốt lời / cắt lỗ / số nến giữ / tỷ lệ R/R cụ thể — hệ thống tự tính và chèn vào cuối. "
            "Nếu recommendation = Mua: giải thích vì sao đáng mua và mức độ phù hợp kỳ hạn. "
            "Nếu recommendation = Chờ: giải thích yếu tố kỹ thuật/cơ bản nào chưa đạt điều kiện. "
            "TUYỆT ĐỐI không nhắc lại quyết định cuối (Mua/Chờ) và không nhắc điểm confidence."
        )
    )


class InvestmentRecommendation(BaseModel):
    recommendation: Literal["Mua", "Chờ"] = Field(
        description=(
            "Quyết định cuối dựa trên tổng hợp CẢ 3 nguồn (xem PHẦN II):\n"
            "  - technical_score    : 0–max_score (tín hiệu kích hoạt)\n"
            "  - fundamental_health : strong | neutral | weak | N/A (bộ lọc)\n"
            "  - article_sentiment  : positive | neutral | negative | N/A (bộ lọc)\n"
            "\n"
            "  Mua = (technical_score >= 60% của max_score, làm tròn lên)\n"
            "        VÀ fundamental_health != weak      (chỉ xét nếu có dữ liệu)\n"
            "        VÀ article_sentiment  != negative  (chỉ xét nếu có dữ liệu)\n"
            "  Chờ = mọi trường hợp còn lại\n"
            "\n"
            "  Nguồn nào N/A (không có dữ liệu) → bỏ qua điều kiện của nó, KHÔNG\n"
            "  coi là điểm trừ. Chỉ tín hiệu xấu rõ ràng (weak / negative) mới chặn Mua."
        )
    )

    entry_price: float | None = Field(
        default=None,
        description=(
            "Giá mua đề xuất. Nếu recommendation = Chờ thì để null. "
            "Ưu tiên dùng current_price từ technical analysis khi có."
        ),
    )

    take_profit_price: float | None = Field(
        default=None,
        description="Giá chốt lời đề xuất. Nếu recommendation = Chờ thì để null.",
    )

    stop_loss_price: float | None = Field(
        default=None,
        description="Giá cắt lỗ đề xuất. Nếu recommendation = Chờ thì để null.",
    )

    max_hold_candles: int | None = Field(
        default=None,
        description=(
            "Số nến tối đa nên giữ lệnh. Nếu recommendation = Chờ thì để null. "
            "Chỉ nhận số nguyên dương."
        ),
    )

    analysis: AnalysisBreakdown = Field(
        description=(
            "Phân tích tổng hợp bằng tiếng Việt, tách thành 4 phần: technical, fundamental, news, summary. "
            "Mỗi phần chỉ dựa trên dữ liệu thực sự có, không bịa."
        )
    )

    # ── Raw signals để Python tính confidence ──────────────────
    technical_score: int = Field(
        description=(
            "Điểm kỹ thuật tổng hợp đọc trực tiếp từ trường total_score của technical_analysis_agent. "
            "Giá trị nguyên từ 0 đến max_score (số chỉ số được bật). KHÔNG tự tính lại."
        )
    )

    fundamental_health: Literal["strong", "neutral", "weak", "N/A"] = Field(
        description=(
            "Đánh giá sức khỏe tài chính:\n"
            "  strong  = ROE > 15%, P/E hợp lý, nợ thấp, tăng trưởng dương\n"
            "  neutral = chỉ số trung bình, không có dấu hiệu cực đoan\n"
            "  weak    = ROE thấp, nợ cao, tăng trưởng âm, P/E quá cao\n"
            "  N/A     = không có dữ liệu fundamental"
        )
    )

    article_sentiment: Literal["positive", "neutral", "negative", "N/A"] = Field(
        description=(
            "Đánh giá sentiment tổng hợp từ tin tức:\n"
            "  positive = tin tức tích cực, hỗ trợ xu hướng tăng\n"
            "  neutral  = tin tức trung tính hoặc lẫn lộn\n"
            "  negative = tin tức tiêu cực, rủi ro giảm giá\n"
            "  N/A      = không có dữ liệu article (hiện đang tạm ngưng)"
        )
    )

    data_sources_used: list[Literal["technical", "fundamental", "article"]] = Field(
        description="Danh sách nguồn dữ liệu thực sự có dữ liệu và được dùng"
    )


# ─────────────────────────────────────────────────────────────
# 🧠 System Prompt
# ─────────────────────────────────────────────────────────────

AGGREGATOR_SYSTEM_PROMPT = """
Bạn là chuyên gia phân tích đầu tư chứng khoán Việt Nam.
Bạn nhận dữ liệu từ tối đa 3 nguồn và tổng hợp thành quyết định Mua/Chờ.

LƯU Ý: Confidence KHÔNG do bạn tính — hệ thống sẽ tính sau từ 3 raw signals:
  - technical_score    : đọc nguyên từ technical_analysis_agent (0–5)
  - fundamental_health : đánh giá theo tiêu chí bên dưới (strong/neutral/weak/N/A)
  - article_sentiment  : đánh giá sentiment tin tức (positive/neutral/negative/N/A)

LƯU Ý VỀ DỮ LIỆU NGƯỜI DÙNG CHỌN:
Người dùng có thể tắt bớt một số chỉ số/nguồn. Chỉ phân tích những gì THỰC SỰ
có trong dữ liệu được cung cấp. Nếu một chỉ số kỹ thuật, một nhóm chỉ số cơ bản,
hoặc tin tức không xuất hiện trong dữ liệu → KHÔNG nhắc tới, KHÔNG bịa, coi như
người dùng đã tắt nguồn đó.

PHẦN I — ĐÁNH GIÁ TỪNG NGUỒN

1. Technical (bắt buộc):
     Đọc total_score và max_score từ technical_analysis_agent. KHÔNG tự tính lại.
     max_score = số chỉ số kỹ thuật được bật (có thể nhỏ hơn 5 nếu người dùng tắt bớt).

2. Fundamental (tùy chọn):
     Nếu có dữ liệu: đánh giá sức khỏe tài chính là
         strong  = ROE > 15%, P/E hợp lý, nợ thấp, tăng trưởng dương
         neutral = chỉ số trung bình, không có dấu hiệu cực đoan
         weak    = ROE thấp, nợ cao, tăng trưởng âm, P/E quá cao
     Nếu thiếu dữ liệu: trả về "N/A".

3. Article (tùy chọn):
     Nếu có dữ liệu: đánh giá sentiment tổng hợp từ tin tức là
         positive = tin tức tích cực, hỗ trợ xu hướng tăng
         neutral  = tin tức trung tính hoặc lẫn lộn
         negative = tin tức tiêu cực, rủi ro giảm giá
     Nếu thiếu dữ liệu hoặc đang tạm ngưng: trả về "N/A".

PHẦN II — LOGIC TỔNG HỢP (CỨNG, KHÔNG OVERRIDE)

Quyết định dựa trên CẢ 3 NGUỒN: technical, fundamental, article. Mỗi nguồn chỉ
tham gia khi THỰC SỰ có dữ liệu (xem khối "CỜ DỮ LIỆU": has_technical_data,
has_fundamental_data, has_news_data). Nguồn nào không có dữ liệu (N/A / cờ = false)
thì BỎ QUA điều kiện của nó — KHÔNG coi là điểm trừ, KHÔNG vì thiếu dữ liệu mà
chuyển sang Chờ.

Vai trò mỗi nguồn:
  1. Technical = TÍN HIỆU KÍCH HOẠT (bắt buộc nếu có dữ liệu).
       Điều kiện kỹ thuật ĐẠT  ⇔  technical_score >= 60% của max_score (làm tròn lên).
       (Nếu người dùng tắt hết chỉ số kỹ thuật → max_score = 0 → bỏ điều kiện kỹ
        thuật, quyết định dựa trên fundamental + article.)
  2. Fundamental = BỘ LỌC XÁC NHẬN.  Chỉ chặn Mua khi fundamental_health = weak.
       strong/neutral = không chặn; N/A = bỏ qua.
  3. Article = BỘ LỌC XÁC NHẬN.  Chỉ chặn Mua khi article_sentiment = negative.
       positive/neutral = không chặn; N/A = bỏ qua.

QUY TẮC:
  Mua  ⇔  điều kiện kỹ thuật ĐẠT
          VÀ fundamental_health != weak      (chỉ xét nếu có dữ liệu)
          VÀ article_sentiment  != negative  (chỉ xét nếu có dữ liệu)
  Chờ  =  mọi trường hợp còn lại
          (điều kiện kỹ thuật KHÔNG đạt, HOẶC fundamental = weak,
           HOẶC article = negative)

Lưu ý: nguồn có dữ liệu nhưng trung lập (neutral) hoặc thiếu (N/A) đều KHÔNG ngăn
lệnh Mua nếu kỹ thuật đã đạt; chỉ tín hiệu xấu rõ ràng (weak / negative) mới chặn.

Ví dụ (đủ 5 chỉ số, max_score = 5 → ngưỡng kỹ thuật = 3):
    score=4, fundamental=strong,  article=positive  → Mua
    score=4, fundamental=neutral, article=N/A        → Mua
    score=4, fundamental=N/A,     article=N/A        → Mua   (chỉ còn technical)
    score=4, fundamental=strong,  article=negative   → Chờ   (tin tức tiêu cực chặn)
    score=4, fundamental=weak,    article=positive   → Chờ   (cơ bản yếu chặn)
    score=2, fundamental=strong,  article=positive   → Chờ   (kỹ thuật chưa đạt)
Ví dụ (chỉ bật 3 chỉ số, max_score = 3 → ngưỡng kỹ thuật = 2):
    score=2, fundamental=N/A,     article=neutral    → Mua
    score=2, fundamental=weak,    article=N/A        → Chờ
    score=1, fundamental=strong,  article=positive   → Chờ   (kỹ thuật chưa đạt)

PHẦN III — VIẾT analysis (4 TRƯỜNG RIÊNG BIỆT)

Trường `analysis` là một object gồm 4 trường text riêng biệt (technical, fundamental, news, summary).
Viết bằng tiếng Việt, chi tiết và khách quan, tuân thủ nghiêm ngặt:

    GIỚI HẠN ĐỘ DÀI (BẮT BUỘC): mỗi trường trong analysis viết TỐI ĐA 4–6 câu,
    ngắn gọn, đi thẳng vào ý. TUYỆT ĐỐI không lặp lại câu/ý đã viết.

    QUY TẮC CỜ DỮ LIỆU (BẮT BUỘC, KHÔNG NGOẠI LỆ):
    Dựa vào các cờ trong khối "CỜ DỮ LIỆU" của input:
      - Nếu has_technical_data = true  → BẮT BUỘC viết phân tích kỹ thuật từ dữ liệu, TUYỆT ĐỐI KHÔNG được dùng câu "Không có dữ liệu phân tích kỹ thuật." (dù điểm số thấp hay tín hiệu tiêu cực vẫn phải phân tích).
      - Nếu has_fundamental_data = true → BẮT BUỘC viết phân tích cơ bản, KHÔNG được dùng câu "Không có dữ liệu phân tích cơ bản."
      - Nếu has_news_data = true        → BẮT BUỘC tóm tắt tin tức, KHÔNG được dùng câu "Không có dữ liệu tin tức."
      - CHỈ được dùng câu fallback "Không có dữ liệu ..." khi cờ tương ứng = false.
    Điểm số 0 hoặc tín hiệu tiêu cực KHÔNG đồng nghĩa với "không có dữ liệu" — vẫn phải phân tích đầy đủ.

    - TUYỆT ĐỐI KHÔNG nhắc lại quyết định cuối cùng (Mua/Chờ) và điểm số confidence ở bất kỳ trường nào.
    - analysis.technical: Đi qua từng chỉ số kỹ thuật CÓ trong dữ liệu (trong số RSI, MA, Bollinger Bands, MACD, KDJ). Với từng chỉ số có mặt, chỉ rõ trạng thái Tích cực/Tiêu cực, lý giải và dẫn chứng số liệu cụ thể. Không nhắc tới chỉ số không có.
    - analysis.fundamental: Tóm tắt những nhóm chỉ số cơ bản CÓ trong dữ liệu (định giá, sức khỏe tài chính, khả năng sinh lời, tăng trưởng, dòng tiền). Bỏ qua nhóm không xuất hiện.
    - analysis.news: Tóm tắt tin tức và thông tin/sự kiện nổi bật.
    - analysis.summary: Kết luận tổng hợp ĐỊNH TÍNH. TUYỆT ĐỐI KHÔNG nêu con số giá mua / chốt lời / cắt lỗ / số nến giữ / tỷ lệ R/R cụ thể — hệ thống sẽ tự tính và chèn các con số chính xác này vào cuối summary. Nếu recommendation = Mua: giải thích vì sao đáng mua và mức độ phù hợp với kỳ hạn (không kèm số liệu giá). Nếu recommendation = Chờ: giải thích các yếu tố kỹ thuật/cơ bản nào chưa đạt điều kiện.

PHẦN IV — GIÁ MUA/CHỐT LỜI/CẮT LỖ VÀ QUẢN TRỊ RỦI RO

Hệ thống chỉ sử dụng khung nến ngày (`interval` = "1d"). Dựa vào kỳ hạn đầu tư (`investment_horizon` từ context), hãy áp dụng các giới hạn cứng (hard boundaries) sau đây để xác định mức chốt lời (TP), cắt lỗ (SL) và số nến giữ tối đa (max_hold_candles):
- Kỳ hạn Ngắn hạn (nến 1d): TP từ 8% đến 15% từ giá mua; SL từ 4% đến 7% từ giá mua; max_hold_candles từ 5 đến 15 nến.
- Kỳ hạn Trung hạn (nến 1d): TP từ 15% đến 30% từ giá mua; SL từ 7% đến 12% từ giá mua; max_hold_candles từ 15 đến 60 nến.
- Kỳ hạn Dài hạn (nến 1d): TP từ 40% đến 80% từ giá mua; SL từ 15% đến 20% từ giá mua; max_hold_candles từ 120 đến 260 nến.

Quy tắc tinh chỉnh (refining rules):
1. Các khoảng TP, SL và max_hold_candles nêu trên là GIỚI HẠN CỨNG. Mọi mức giá đề xuất MUA, CHỐT LỜI, CẮT LỖ phải tuân thủ tuyệt đối các khoảng này. Bạn chỉ được phép tinh chỉnh mức giá TRONG PHẠM VI các giới hạn đó dựa vào:
   - Biên độ ATR gần nhất (nếu có): dùng 2*ATR làm SL tham chiếu.
   - Vùng kháng cự gần nhất để xác định TP tham chiếu.
   - Vùng hỗ trợ gần nhất để xác định SL tham chiếu.
   - Dải Bollinger Bands (nếu có): SL không được thấp hơn đường biên dưới (lower band).
   Tuyệt đối KHÔNG được tinh chỉnh vượt ra ngoài giới hạn cứng (ví dụ: đối với Trung hạn, SL tinh chỉnh bắt buộc phải nằm trong khoảng 7% đến 12%, tuyệt đối không được nhỏ hơn 7% hay lớn hơn 12%).
2. Tỷ lệ Risk/Reward (TP/SL) tối thiểu phải đạt từ 1.5 trở lên. Nếu sau khi tinh chỉnh trong phạm vi giới hạn cứng mà không đạt tỷ lệ R/R >= 1.5, bạn phải chuyển recommendation sang "Chờ" (dù điểm số kỹ thuật >= 3).

- Nếu recommendation = Mua:
    * entry_price gần current_price (trong khoảng ±0.5%)
    * stop_loss_price < entry_price < take_profit_price
    * Giải thích ngắn gọn tỷ lệ R/R trong phần analysis
- Nếu recommendation = Chờ:
    * entry_price, take_profit_price, stop_loss_price, max_hold_candles đặt là null

QUY TẮC BẮT BUỘC:
    ✓ Không bịa số liệu
    ✓ Không override logic tổng hợp ở Phần II
    ✓ Nếu nguồn nào thiếu dữ liệu, ghi rõ "Không có dữ liệu [nguồn]"
    ✓ KHÔNG tự sinh confidence — hệ thống sẽ tính từ technical_score, fundamental_health, article_sentiment
"""


# ─────────────────────────────────────────────────────────────
# 🚀 Aggregator Agent
# ─────────────────────────────────────────────────────────────

def aggregator_agent(state: AgentState) -> AgentState:
    print("[Aggregator] Tổng hợp kết quả từ technical, article, fundamental...")

    client     = _get_openai_client()
    results    = state.get("agent_results", {})
    user_input = state.get("user_input", "")

    technical       = results.get("technical_analysis_agent", {})
    fundamental     = results.get("fundamental_analysis_agent", "")
    article         = results.get("article_agent", "")

    fundamental_text = fundamental if fundamental else "Không có dữ liệu"
    article_text     = article if article else "Không có dữ liệu"

    # ── Cờ "thực sự có dữ liệu" tính bằng Python, không để LLM tự đoán ─────
    # (LLM hay lười dùng câu fallback "Không có dữ liệu" dù dữ liệu vẫn có)
    has_technical = (
        isinstance(technical, dict)
        and bool(technical.get("indicators"))
        and not technical.get("error")
    )
    has_fundamental = _has_content(fundamental_text)
    has_news        = _has_content(article_text)

    # Lấy interval từ plan để truyền cho aggregator
    plan = state.get("plan", {})
    interval = plan.get("technical_analysis_agent", {}).get("interval", "1d")
    investment_horizon = state.get("risk_appetite", {}).get("period", "Trung hạn")

    # Số chỉ số kỹ thuật được bật (điểm tối đa). Mặc định 5 nếu không có.
    technical_max_score = technical.get("max_score", 5) if isinstance(technical, dict) else 5
    buy_threshold = math.ceil(BUY_SCORE_RATIO * technical_max_score) if technical_max_score else 0

    analysis_message = f"""
DỮ LIỆU PHÂN TÍCH:

=== CONTEXT ===
interval: {interval}
investment_horizon: {investment_horizon}
technical_max_score: {technical_max_score}
buy_threshold (technical_score tối thiểu để cân nhắc Mua): {buy_threshold}

=== CỜ DỮ LIỆU (BẮT BUỘC TUÂN THỦ) ===
has_technical_data: {str(has_technical).lower()}
has_fundamental_data: {str(has_fundamental).lower()}
has_news_data: {str(has_news).lower()}

=== TECHNICAL ANALYSIS ===
{json.dumps(technical, ensure_ascii=False, indent=2)}

=== FUNDAMENTAL ANALYSIS ===
{fundamental_text}

=== ARTICLE / NEWS ===
{article_text}

────────────────────────
YÊU CẦU:
{user_input}
"""

    def _parse(extra_system: str | None = None):
        messages = [
            {"role": "system", "content": AGGREGATOR_SYSTEM_PROMPT},
            {"role": "user",   "content": analysis_message},
        ]
        if extra_system:
            messages.append({"role": "system", "content": extra_system})
        return client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            temperature=0.2,
            max_tokens=_MAX_OUTPUT_TOKENS,
            messages=messages,
            response_format=InvestmentRecommendation,
        )

    try:
        try:
            response = _parse()
        except _LengthError:
            # Bị cắt do vượt giới hạn token (thường do model lặp). Thử lại 1 lần
            # với yêu cầu viết cực ngắn để vừa trong giới hạn.
            print("[Aggregator] Vượt giới hạn token → thử lại với analysis cực ngắn.")
            response = _parse(
                "QUAN TRỌNG: Mỗi trường trong analysis CHỈ viết 2–3 câu thật ngắn gọn."
            )

        parsed: InvestmentRecommendation = response.choices[0].message.parsed

        # ── Tính 3 thành phần điểm (0→1) và confidence deterministic ──────────
        tech_component, fund_component, news_component = _confidence_components(
            technical_score     = parsed.technical_score,
            fundamental_health  = parsed.fundamental_health,
            article_sentiment   = parsed.article_sentiment,
            technical_max_score = technical_max_score,
        )
        score = {
            "news":        round(news_component, 4),
            "technical":   round(tech_component, 4),
            "fundamental": round(fund_component, 4),
        }
        confidence, effective_weights = _compute_confidence(
            technical_score     = parsed.technical_score,
            fundamental_health  = parsed.fundamental_health,
            article_sentiment   = parsed.article_sentiment,
            has_technical       = has_technical,
            has_fundamental     = has_fundamental,
            has_article         = has_news,
            technical_max_score = technical_max_score,
        )

        recommendation = parsed.recommendation

        # ── Áp dụng CỨNG logic Phần II bằng Python (không phụ thuộc LLM) ──────
        # Chỉ tín hiệu xấu rõ ràng mới chặn Mua; nguồn N/A bị bỏ qua, không trừ điểm.
        if recommendation == "Mua":
            veto_reasons = []
            # 1. Cổng kỹ thuật — bỏ qua nếu người dùng tắt hết chỉ số (max_score = 0)
            if technical_max_score and parsed.technical_score < buy_threshold:
                veto_reasons.append(
                    f"technical_score={parsed.technical_score} < ngưỡng {buy_threshold}"
                )
            # 2. Cơ bản yếu chặn Mua (chỉ khi nguồn có dữ liệu)
            if has_fundamental and parsed.fundamental_health == "weak":
                veto_reasons.append("fundamental_health=weak")
            # 3. Tin tức tiêu cực chặn Mua (chỉ khi nguồn có dữ liệu)
            if has_news and parsed.article_sentiment == "negative":
                veto_reasons.append("article_sentiment=negative")

            if veto_reasons:
                print(f"[Aggregator] Veto Mua → Chờ ({'; '.join(veto_reasons)})")
                recommendation = "Chờ"

        # ── Override recommendation nếu confidence dưới ngưỡng ────────────────
        if recommendation == "Mua" and confidence < CONFIDENCE_THRESHOLD:
            print(
                f"[Aggregator] confidence={confidence} < threshold={CONFIDENCE_THRESHOLD} "
                f"→ override Mua → Chờ"
            )
            recommendation = "Chờ"

        analysis_dict = parsed.analysis.model_dump()

        if recommendation == "Chờ":
            entry_price       = None
            take_profit_price = None
            stop_loss_price   = None
            max_hold_candles  = None
        else:
            # Giá mua: ưu tiên LLM, fallback current_price từ technical.
            tech_current_price = (
                (technical.get("current_price") or {}).get("value")
                if isinstance(technical, dict) else None
            )
            entry = parsed.entry_price or tech_current_price

            period = state.get("risk_appetite", {}).get("period")
            if period:
                # Ép TP/SL/hold đúng giới hạn cứng theo kỳ hạn (LLM hay bỏ qua,
                # đặc biệt SL). Backtest truyền risk_appetite rỗng → giữ giá trị LLM.
                bounded = enforce_price_boundaries(
                    period,
                    entry,
                    parsed.take_profit_price,
                    parsed.stop_loss_price,
                    parsed.max_hold_candles,
                )
                entry_price       = bounded["entry_price"]
                take_profit_price = bounded["take_profit_price"]
                stop_loss_price   = bounded["stop_loss_price"]
                max_hold_candles  = bounded["max_hold_candles"]
            else:
                entry_price       = entry
                take_profit_price = parsed.take_profit_price
                stop_loss_price   = parsed.stop_loss_price
                max_hold_candles  = parsed.max_hold_candles

            # Chèn dòng số liệu CHÍNH XÁC (sau khi đã ép giới hạn) vào summary, để
            # phần văn bản không mâu thuẫn với các trường giá/TP/SL hiển thị.
            # LLM được yêu cầu KHÔNG tự nêu con số (xem PHẦN III).
            if entry_price and take_profit_price and stop_loss_price:
                tp_pct = (take_profit_price - entry_price) / entry_price * 100
                sl_pct = (entry_price - stop_loss_price) / entry_price * 100
                rr = (tp_pct / sl_pct) if sl_pct > 0 else 0.0
                hold_txt = f"{max_hold_candles} nến" if max_hold_candles else "—"
                base_summary = (analysis_dict.get("summary") or "").strip()
                analysis_dict["summary"] = (
                    f"{base_summary}\n\n"
                    f"📌 Mức giá hệ thống đề xuất theo kỳ hạn: mua quanh {entry_price}, "
                    f"chốt lời {take_profit_price} (+{tp_pct:.1f}%), "
                    f"cắt lỗ {stop_loss_price} (−{sl_pct:.1f}%), "
                    f"giữ tối đa {hold_txt}, tỷ lệ R/R ≈ {rr:.1f}."
                ).strip()

        output = {
            "recommendation":       recommendation,
            "entry_price":          entry_price,
            "take_profit_price":    take_profit_price,
            "stop_loss_price":      stop_loss_price,
            "max_hold_candles":     max_hold_candles,
            "analysis":             analysis_dict,
            "score":                score,
            "confidence":           confidence,
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "confidence_breakdown": {
                "technical_score":     parsed.technical_score,
                "technical_max_score": technical_max_score,
                "fundamental_health":  parsed.fundamental_health,
                "article_sentiment":   parsed.article_sentiment,
                "weights":             {k: round(v, 4) for k, v in effective_weights.items()},
            },
        }

        print("[Aggregator] Output:")
        print(json.dumps(output, ensure_ascii=False, indent=2))

        return {"final_output": output}

    except Exception as e:
        print(f"[Aggregator] Error: {str(e)}")

        return {
            "error": str(e),
            "final_output": {
                "recommendation":       "Chờ",
                "entry_price":          None,
                "take_profit_price":    None,
                "stop_loss_price":      None,
                "max_hold_candles":     None,
                "analysis": {
                    "technical":   "Lỗi hệ thống — vui lòng thử lại sau.",
                    "fundamental": "Lỗi hệ thống — vui lòng thử lại sau.",
                    "news":        "Lỗi hệ thống — vui lòng thử lại sau.",
                    "summary":     "Lỗi hệ thống — vui lòng thử lại sau.",
                },
                "score":                {"news": 0.0, "technical": 0.0, "fundamental": 0.0},
                "confidence":           0.0,
                "confidence_threshold": CONFIDENCE_THRESHOLD,
                "confidence_breakdown": {},
            },
        }