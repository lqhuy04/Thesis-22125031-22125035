"""
aggregator.py — Aggregator Agent (simplified)

Đọc output từ technical_analysis_agent, tổng hợp và đưa ra quyết định Mua/Chờ.
Rule: total_score >= 3/5 → Mua, ngược lại → Chờ.

Confidence được tính deterministic trong Python (không để LLM tự sinh),
dựa trên các nguồn THỰC SỰ có dữ liệu, với trọng số theo kỳ hạn đầu tư
(xem CONFIDENCE_WEIGHTS_BY_HORIZON: Ngắn hạn ưu tiên PTKT, Dài hạn ưu tiên PTCB):

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
from agentic_ai.analyze.horizon import enforce_price_boundaries, normalize_horizon
from agentic_ai.analyze.selection import get_selection

# Raised by the OpenAI SDK when structured parsing fails because the model hit
# the output token cap (finish_reason = "length"). Tuple fallback for older SDKs
# makes `except _LengthError` a no-op rather than a NameError.
try:
    from openai import LengthFinishReasonError as _LengthError
except ImportError:  # pragma: no cover
    _LengthError = ()

# Bound the aggregator output. Room for the 4 detailed analysis fields + signals,
# while preventing a degenerate repetition loop from running to the model's 16k cap.
_MAX_OUTPUT_TOKENS = 5000


# ─────────────────────────────────────────────────────────────
# ⚙️ Confidence Config
# ─────────────────────────────────────────────────────────────

# Ngưỡng tối thiểu để chấp nhận lệnh Mua
CONFIDENCE_THRESHOLD = 0.55

# Tỷ lệ điểm kỹ thuật tối thiểu để cân nhắc Mua (3/5 = 0.6 — giữ tương thích khi bật đủ 5 chỉ số)
BUY_SCORE_RATIO = 0.6

# Trọng số từng nguồn theo kỳ hạn đầu tư (mỗi hàng tổng = 1.0).
# Ngắn hạn ưu tiên PTKT (tín hiệu giá nhanh), dài hạn ưu tiên PTCB (nền tảng DN).
CONFIDENCE_WEIGHTS_BY_HORIZON = {
    "short": {"technical": 0.60, "fundamental": 0.10, "article": 0.30},
    "mid":   {"technical": 0.40, "fundamental": 0.40, "article": 0.20},
    "long":  {"technical": 0.15, "fundamental": 0.70, "article": 0.15},
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
    horizon: str = "mid",
    base_weights: dict[str, float] | None = None,
) -> dict[str, float]:
    """
    Trọng số HIỆU DỤNG sau khi loại các nguồn người dùng tắt / không có dữ liệu.

    Trọng số gốc lấy từ `base_weights` (do người dùng nhập thủ công qua
    data_selection.weight) nếu có, ngược lại mặc định theo kỳ hạn đầu tư
    (CONFIDENCE_WEIGHTS_BY_HORIZON). Trọng số của các nguồn bị loại được chia đều
    lại (renormalize) cho các nguồn còn hoạt động, nên tổng trọng số hiệu dụng
    luôn = 1.0 khi có ≥ 1 nguồn. Nguồn bị loại có trọng số 0.0 → không đóng góp
    vào confidence.

    Nếu không nguồn nào hoạt động (về lý thuyết không xảy ra vì technical bắt
    buộc) → trả về toàn 0.0 (caller sẽ coi confidence là trung lập).
    """
    weights = base_weights or CONFIDENCE_WEIGHTS_BY_HORIZON.get(horizon, CONFIDENCE_WEIGHTS_BY_HORIZON["mid"])
    active = {
        "technical":   has_technical,
        "fundamental": has_fundamental,
        "article":     has_article,
    }
    raw_total = sum(weights[k] for k, on in active.items() if on)
    if raw_total <= 0:
        return {k: 0.0 for k in weights}
    return {
        k: (weights[k] / raw_total if active[k] else 0.0)
        for k in weights
    }


def _compute_confidence(
    technical_score: int,
    fundamental_health: str,
    article_sentiment: str,
    has_technical: bool,
    has_fundamental: bool,
    has_article: bool,
    technical_max_score: int = 5,
    horizon: str = "mid",
    base_weights: dict[str, float] | None = None,
) -> tuple[float, dict[str, float]]:
    """
    Tính confidence score [0.0, 1.0] hoàn toàn bằng rule cứng, chỉ trên các nguồn
    THỰC SỰ có dữ liệu (has_* = true). Trọng số gốc lấy từ `base_weights` (thủ
    công) nếu có, ngược lại theo kỳ hạn đầu tư (horizon), và được renormalize
    trên nguồn hoạt động. Xem _confidence_components và _effective_weights.

    Trả về (confidence, effective_weights) để caller báo cáo lại trong breakdown.
    """
    technical_component, fundamental_component, article_component = _confidence_components(
        technical_score, fundamental_health, article_sentiment, technical_max_score
    )

    w = _effective_weights(has_technical, has_fundamental, has_article, horizon, base_weights)
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
            "Phân tích kỹ thuật CHI TIẾT bằng tiếng Việt. Nếu has_technical_data = true: BẮT BUỘC đi qua "
            "TỪNG chỉ số CÓ trong dữ liệu (RSI, MA, Bollinger Bands, MACD, KDJ), mỗi chỉ số 2–4 câu nêu: "
            "giá trị hiện tại (và kỳ trước nếu có), trạng thái Tích cực/Tiêu cực, VÌ SAO (ngưỡng + cơ chế), "
            "và hàm ý. Kết lại: chỉ số nào ỦNG HỘ, chỉ số nào CẢN TRỞ, vì sao tổng điểm như vậy. "
            "KHÔNG nói không có dữ liệu dù điểm thấp. "
            "Chỉ khi has_technical_data = false mới ghi: 'Không có dữ liệu phân tích kỹ thuật.'"
        )
    )
    fundamental: str = Field(
        description=(
            "Phân tích cơ bản CHI TIẾT bằng tiếng Việt theo PROMPT PTCB. Nếu has_fundamental_data = true: "
            "BẮT BUỘC đi lần lượt qua TỪNG nhóm chỉ số CÓ trong dữ liệu, MỖI NHÓM MỘT ĐOẠN RIÊNG biệt, mở đầu bằng ĐÚNG tên nhóm in đậm. "
            "\n"
            "DOANH NGHIỆP PHI TÀI CHÍNH: 5 nhóm theo thứ tự: **Khả năng thanh toán** → **Đòn bẩy tài chính** → **Hiệu quả hoạt động** "
            "→ **Khả năng sinh lời** → **Định giá**. "
            "NGÀNH TÀI CHÍNH (ngân hàng, bảo hiểm, dịch vụ tài chính - CAMELS): theo thứ tự: **C — An toàn vốn** → **A — Chất lượng tài sản** "
            "→ **M — Năng lực quản trị** → **E — Khả năng sinh lời** → **L — Thanh khoản** → **S — Độ nhạy rủi ro thị trường** → **Định giá**. "
            "\n"
            "BẮT BUỘC VỀ DỮ LIỆU: "
            "- CHỈ nhắc chỉ số THỰC SỰ có trong dữ liệu; TUYỆT ĐỐI KHÔNG bịa (không nhắc tổng tài sản, doanh thu, dòng tiền nếu không có). "
            "- Nếu CAGR = '—' hoặc không có, phải nói rõ 'không tính được CAGR do thiếu dữ liệu', không suy diễn. "
            "- Tôn trọng ghi chú 'chưa có CAR/NPL/NIM/LDR/CIR' trong dữ liệu ngành tài chính — nêu rõ hạn chế thay vì bịa. "
            "\n"
            "BẮT BUỘC VỀ CAGR: "
            "- Với 4 nhóm/cấu phần ĐẦU (trừ Định giá và S): PHẢI trích dẫn CAGR (dạng 'X%/năm') của ít nhất 1 chỉ số chính trong nhóm. "
            "- Giải thích ý nghĩa: CAGR dương = tăng/cải thiện, CAGR âm = giảm/suy giảm (đặc biệt: CAGR âm của số ngày tồn kho/phải thu = cải thiện). "
            "- TUYỆT ĐỐI không mô tả ngược (không viết 'giảm từ 1.26 xuống 1.40' khi CAGR dương). "
            "\n"
            "BẮT BUỘC VỀ SO SÁNH NGÀNH: "
            "- Áp dụng cho MỌI mã khi input có bảng 'So sánh với ngành'. "
            "- Trong TỪNG đoạn nhóm/cấu phần, PHẢI đối chiếu chỉ số chính của mã với trung vị ngành tương ứng: "
            "  CAO HƠN / THẤP HƠN / TƯƠNG ĐƯƠNG kèm con số cụ thể (vd 'ROE 18.7% so với trung vị ngành 12.4% → cao hơn'). "
            "- So CAGR mã với CAGR ngành để kết luận mã tăng nhanh/chậm hơn ngành. "
            "\n"
            "PHÂN TÍCH DUPONT (bắt buộc nếu có đủ dữ liệu): "
            "- Giải thích ROE = Biên LN ròng (%) × Vòng quay TS (lần) × Đòn bẩy TC (lần). "
            "- NÊU RÕ: (1) Thành phần nào đang đỡ ROE; (2) Công ty dùng chiến lược nào "
            "  (a) Vốn cao + lợi nhuận cao; (b) Nợ + hiệu quả khai thác tốt; (c) Nợ để bù lợi nhuận/hiệu quả thấp). "
            "- CAGR từng thành phần 3-5 năm để thấy xu hướng. "
            "\n"
            "CHỈ TÍCH LŨY tiêu chuẩn: "
            "- Khả năng thanh toán: > 1 = an toàn, < 1 = rủi ro ngắn hạn. "
            "- Đòn bẩy tài chính: Nợ/VCSH thấp = an toàn, cao = rủi ro; khả năng trả lãi cao = dễ trả nợ. "
            "- Hiệu quả hoạt động: vòng quay cao = khai thác tốt; số ngày tồn kho/phải thu thấp = tốt. "
            "- Khả năng sinh lời: ROE > 15% = tốt, ROE < 8% = yếu. "
            "- Định giá ngành tài chính (CHỈ dùng P/B): TUYỆT ĐỐI không nhắc P/E hay EV/EBITDA. "
            "\n"
            "Chỉ khi has_fundamental_data = false mới ghi: 'Không có dữ liệu phân tích cơ bản.'"
        )
    )
    news: str = Field(
        description=(
            "Phân tích tin tức bằng tiếng Việt theo PROMPT PTCB, gồm 3 phần riêng biệt:\n"
            "\n"
            "1. **Tác động về mô đến Ngành**:\n"
            "   Phân tích cách các thay đổi về thuế TNCN, quản lý tài sản, chính sách mới "
            "(hoặc dự thảo khả thi năm 2026) tác động TÍCH CỰC hay TIÊU CỰC tới tổng cầu, "
            "hành vi tiêu dùng/đầu tư, và hoạt động của toàn ngành. "
            "Ví dụ: thuế TNCN giảm → thu nhập khả dụng tăng → sức mua chung tăng (tích cực cho bán lẻ, tiêu dùng); "
            "siết quản lý tài sản riêng → hạn chế đầu tư (tiêu cực cho bất động sản, chứng khoán). "
            "   VÍ DỤ GỢI Ý theo ngành: "
            "   - Bất động sản/Chứng khoán: quản lý tài sản → dòng tiền nhà đầu tư; xác thực BĐS → chi phí tuân thủ. "
            "   - Bán lẻ/Tiêu dùng/TMĐT: thuế TNCN → sức mua; siết thuế TMĐT → lợi nhuận. "
            "   - Ngân hàng/Bảo hiểm: quản lý tài sản → huy động vốn; tiền gửi chính chủ → kênh bancassurance. "
            "\n"
            "2. **Tác động vi mô đến Mã cổ phiếu [NHẬ p TÊN MÃ CỤ THỂ]**:\n"
            "   Đi sâu vào nội tại cụ thể: chính sách nào ĐÁ NH TRỰC TIẾP vào cấu phần nào của hoạt động công ty "
            "(doanh thu → suy giảm?; chi phí tuân thủ → tăng?; tốc độ tăng trưởng CAGR → kìm hãm hay kích thích?). "
            "   Đánh giá xem công ty có lợi thế cạnh tranh nào để 'phòng thủ' hoặc 'tận dụng' chính sách mới so với đối thủ cùng ngành. "
            "\n"
            "3. **Kết luận triển vọng và định giá lại**:\n"
            "   Với mỗi tin tức/chính sách, BẮT BUỘC GIẢI THÍCH rõ ràng tác động của nó là TÍCH CỰC (tăng triển vọng kinh doanh, cổ phiếu tăng giá) "
            "   hay TIÊU CỰC (giảm triển vọng, cổ phiếu có rủi ro giảm giá). "
            "   KHÔNG được để mơ hồ hoặc không kết luận. "
            "\n"
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
            "Đánh giá sức khỏe tài chính theo PROMPT PTCB, dựa trên DuPont & chiến lược tài chính:\n"
            "  strong  = ROE > 15% với chiến lược lành mạnh theo DuPont:\n"
            "            (a) Vốn chủ yếu + biên LN cao (margin-driven), HOẶC\n"
            "            (b) Nợ vừa phải (Đòn bẩy TC ~ 1.5-2.5) + hiệu quả khai thác tốt (vòng quay cao),\n"
            "            (c) Nợ thấp (Đòn bẩy TC < 1.5) + lợi nhuận cao.\n"
            "            Thêm: CAGR ROE dương, P/E hợp lý, thanh khoản ≥ 1.\n"
            "  neutral = ROE 8-15% hoặc có yếu tố rủi ro vừa phải (nợ cao nhưng ROE/lợi nhuận chưa xấu).\n"
            "            CAGR ROE gần 0 (dao động) hoặc chưa rõ xu hướng dài hạn.\n"
            "            Không có dấu hiệu cực đoan; thanh khoản vừa phải (0.8-1.2).\n"
            "  weak    = ROE < 8% HOẶC chiến lược cao rủi ro (Đòn bẩy TC > 3.0 + ROE thấp + CAGR ROE âm).\n"
            "            Tăng trưởng âm (CAGR ROE < 0 kéo dài), P/E quá cao so với tăng trưởng.\n"
            "            Thanh khoản < 1 (rủi ro ngắn hạn), hoặc nợ tăng mà lợi nhuận suy giảm.\n"
            "  N/A     = không có dữ liệu fundamental đủ để đánh giá (thiếu ROE hoặc DuPont components).\n"
            "\n"
            "  ⚠️ CẢNH BÁO RỦI RO DUPONT: Nếu mã có Đòn bẩy TC > 3.0 + CAGR ROE < 0 (suy giảm),\n"
            "  coi như WEAK dù ROE hiện tại chưa xấu — công ty đang trong quá trình thoái, nợ cao + lợi nhuận yếu."
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
     Nếu có dữ liệu: đánh giá sức khỏe tài chính theo PROMPT PTCB (xem Phần III):
         strong  = ROE > 15% + chiến lược DuPont lành mạnh + CAGR ROE dương + P/E hợp lý + thanh khoản ≥ 1.
                   Chiến lược lành mạnh: (a) margin-driven (vốn chủ yếu), HOẶC
                                        (b) efficiency-driven (nợ 1.5-2.5x, vòng quay cao), HOẶC
                                        (c) nợ thấp (<1.5x) + margin cao.
         neutral = ROE 8-15% hoặc rủi ro vừa phải (nợ cao nhưng ROE chưa xấu);
                   CAGR ROE gần 0 (dao động); không dấu hiệu cực đoan; thanh khoản 0.8-1.2.
         weak    = ROE < 8% HOẶC chiến lược cao rủi ro (nợ > 3.0x + ROE thấp + CAGR ROE < 0);
                   tăng trưởng âm; P/E quá cao; thanh khoản < 1 hoặc nợ tăng + lợi nhuận suy giảm.
     Nếu thiếu dữ liệu: trả về "N/A".

3. Article (tùy chọn) — Theo PROMPT PTCB:
     Nếu có dữ liệu: đánh giá sentiment tổng hợp từ 3 phần:
         1. Tác động về mô đến Ngành (chính sách/tin tức tác động TÍCH CỰC / TIÊU CỰC tới ngành).
         2. Tác động vi mô đến Mã cổ phiếu (tác động trực tiếp, lợi thế cạnh tranh).
         3. Kết luận triển vọng (giải thích rõ TÍCH CỰC / TIÊU CỰC).
         positive = tin tức/chính sách tác động tích cực, hỗ trợ xu hướng tăng, không có rủi ro lớn.
         neutral  = tin tức lẫn lộn (có cả tích cực, tiêu cực), hoặc tác động trung tính.
         negative = tin tức/chính sách tác động tiêu cực, rủi ro giảm giá, không có hỗ trợ tích cực.
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
Viết bằng tiếng Việt, chi tiết và khách quan, tuân thủ nghiêm ngặt theo PROMPT PTCB:

    ĐỘ CHI TIẾT (BẮT BUỘC):
    - Phân tích PHẢI cụ thể, giải thích rõ VÌ SAO mạnh / VÌ SAO yếu — KHÔNG nói chung chung.
    - Mỗi chỉ số kỹ thuật: 2–4 câu. Mỗi nhóm chỉ số cơ bản: 2–3 câu.
    - Với mỗi mục, luôn kèm 4 ý: (1) số liệu cụ thể (giá trị hiện tại và kỳ trước nếu có);
      (2) so sánh với ngưỡng / đường tham chiếu / giá trị kỳ trước; (3) CƠ CHẾ vì sao điều đó
      tích cực hay tiêu cực; (4) hàm ý cho xu hướng giá hoặc định giá.
    - TUYỆT ĐỐI không lặp lại câu/ý đã viết, không viết sáo rỗng, không lan man.

    QUY TẮC CỜ DỮ LIỆU (BẮT BUỘC, KHÔNG NGOẠI LỆ):
    Dựa vào các cờ trong khối "CỜ DỮ LIỆU" của input:
      - Nếu has_technical_data = true  → BẮT BUỘC viết phân tích kỹ thuật từ dữ liệu, TUYỆT ĐỐI KHÔNG được dùng câu "Không có dữ liệu phân tích kỹ thuật." (dù điểm số thấp hay tín hiệu tiêu cực vẫn phải phân tích).
      - Nếu has_fundamental_data = true → BẮT BUỘC viết phân tích cơ bản, KHÔNG được dùng câu "Không có dữ liệu phân tích cơ bản."
      - Nếu has_news_data = true        → BẮT BUỘC tóm tắt tin tức, KHÔNG được dùng câu "Không có dữ liệu tin tức."
      - CHỈ được dùng câu fallback "Không có dữ liệu ..." khi cờ tương ứng = false.
    Điểm số 0 hoặc tín hiệu tiêu cực KHÔNG đồng nghĩa với "không có dữ liệu" — vẫn phải phân tích đầy đủ.

    - TUYỆT ĐỐI KHÔNG nhắc lại quyết định cuối cùng (Mua/Chờ) và điểm số confidence ở bất kỳ trường nào.

    - analysis.technical: Đi qua TỪNG chỉ số CÓ trong dữ liệu (RSI, MA, Bollinger Bands, MACD, KDJ).
      Với mỗi chỉ số: nêu giá trị hiện tại (và kỳ trước nếu có), trạng thái Tích cực/Tiêu cực, VÌ SAO
      (dựa trên ngưỡng và cơ chế của chỉ số đó), và hàm ý. Định hướng cách lý giải:
        • RSI: <30 quá bán, 30–50 yếu/đang hồi phục, 50–70 tăng động lực, >70 quá mua; đang tăng hay giảm so với kỳ trước.
        • MA: vị trí giá so với SMA20/SMA50; SMA20>SMA50 = xu hướng tăng, SMA20<SMA50 = xu hướng giảm ("death cross"); độ dốc của đường MA.
        • Bollinger: giá nằm ở dải trên/giữa/dưới; dải mở rộng (biến động/đà mạnh) hay co hẹp (tích lũy, sắp bứt phá).
        • MACD: MACD so với Signal (vừa cắt lên = tín hiệu mua, cắt xuống = bán); histogram tăng (đà mạnh dần) hay giảm (đà yếu dần).
        • KDJ: K so với D (cắt lên/xuống), J tăng tốc hay suy yếu, vùng quá mua (>80) / quá bán (<20).
      Cuối phần, nêu RÕ chỉ số nào đang ỦNG HỘ và chỉ số nào đang CẢN TRỞ, và vì sao tổng điểm kỹ thuật ra như vậy.

    - analysis.fundamental: BẮT BUỘC viết theo CẤU TRÚC NHIỀU ĐOẠN theo PROMPT PTCB (từng nhóm/cấu phần = 1 đoạn riêng in đậm), KHÔNG GỘP.

      DOANH NGHIỆP PHI TÀI CHÍNH — 5 nhóm, BẮT BUỘC theo thứ tự:
      1. **Khả năng thanh toán**: Giá trị năm gần nhất (và năm đầu kỳ), so ngưỡng > 1 = an toàn, < 1 = rủi ro.
         BẮTBUỘC trích dẫn CAGR của ít nhất 1 chỉ số chính (thanh toán hiện hành / nhanh / tiền mặt).
         Đối chiếu trung vị ngành (CAGR ngành). Giải thích xu hướng cải thiện / suy giảm.
      2. **Đòn bẩy tài chính**: Nợ/VCSH, khả năng trả lãi, giá trị năm gần nhất + năm đầu.
         BẮTBUỘC trích dẫn CAGR Nợ/VCSH (tăng/giảm nợ?). Đối chiếu trung vị ngành.
         🔍 PHÂN TÍCH DUPONT (bắt buộc nếu có đủ dữ liệu ROE, biên LN, vòng quay TS, đòn bẩy TC):
            - Giải thích ROE = Biên LN ròng (%) × Vòng quay TS × Đòn bẩy TC.
            - NÊU RÕ 3 điểm: (1) Thành phần nào đỡ ROE (margin, efficiency, leverage)?
                           (2) Chiến lược nào: (a) vốn cao + margin cao, (b) nợ + efficiency tốt, (c) nợ bù margin/efficiency thấp?
                           (3) CAGR 3 thành phần 3-5 năm → xu hướng.
      3. **Hiệu quả hoạt động**: Vòng quay TS/TSCĐ, số ngày tồn kho, số ngày phải thu.
         BẮTBUỘC trích dẫn CAGR của ≥1 chỉ số. Lưu ý: CAGR âm của số ngày = cải thiện, không phải suy giảm.
         Đối chiếu trung vị ngành. Khai thác tốt hay đáng lo?
      4. **Khả năng sinh lời**: ROE, ROA, biên lợi nhuận gộp/ròng. Giá trị năm gần nhất + năm đầu.
         BẮTBUỘC trích dẫn CAGR (ROE > 15% = tốt, < 8% = yếu). Đối chiếu trung vị ngành.
         Sinh lời cải thiện / suy giảm?
      5. **Định giá**: P/E, P/B, EV/EBITDA (nếu có). So với ngành & lịch sử.
         KHÔNG cần CAGR cho mục này. Cổ phiếu đắt / rẻ tương đối?

      NGÀNH TÀI CHÍNH (ngân hàng, bảo hiểm, DVTC — theo khung CAMELS) — 7 mục, BẮT BUỘC theo thứ tự:
      1. **C — An toàn vốn**: CAR (nếu có), giá trị năm gần nhất + năm đầu. BẮTBUỘC CAGR.
         Đối chiếu trung vị ngành. Vốn dày / mỏng?
      2. **A — Chất lượng tài sản**: NPL, LLR (nếu có). BẮTBUỘC CAGR.
         Đối chiếu trung vị ngành. Tài sản xấu?
      3. **M — Năng lực quản trị**: CIR (nếu có), kiểm soát chi phí. BẮTBUỘC CAGR.
         Đối chiếu trung vị ngành.
      4. **E — Khả năng sinh lời**: NIM, ROE, ROA (nếu có). BẮTBUỘC CAGR.
         Đối chiếu trung vị ngành. Sinh lời tốt?
      5. **L — Thanh khoản**: LDR hoặc chỉ số thanh khoản tương ứng (nếu có). BẮTBUỘC CAGR + xu hướng.
         Đối chiếu trung vị ngành.
      6. **S — Độ nhạy rủi ro thị trường**: Rủi ro ngoại tệ, lãi suất (nếu có). Đối chiếu ngành.
      7. **Định giá**: CHỈ dùng P/B (TUYỆT ĐỐI không nhắc P/E / EV/EBITDA cho ngành tài chính).
         So với ngành. Đắt / rẻ?

      ⚠️ CẢNH BÁO: Tôn trọng ghi chú "chưa có CAR/NPL/NIM/LDR/CIR" — KHÔNG bịa, NÊU RÕ hạn chế.
      ✅ BẮT BUỘC SO SÁNH TRUNG VỊ NGÀNH (nếu input có "So sánh với ngành"):
         - Mỗi đoạn phải nêu: "Chỉ số X: Y so với trung vị ngành Z → cao hơn / thấp hơn / tương đương".
         - So CAGR mã vs CAGR ngành (mã tăng nhanh / chậm hơn?).
         - Đây là căn cứ chính kết luận cổ phiếu tốt/xấu, đắt/rẻ TƯƠNG ĐỐI — không bỏ qua.
      ✅ ĐỌC ĐÚNG chiều CAGR: CAGR dương = tăng, CAGR âm = giảm (không mô tả ngược).
      ✅ Lưu ý CAGR "—" = không tính được → nói "không tính được CAGR", không suy diễn.
      ✅ CHỈ nhắc chỉ số CÓ trong dữ liệu; KHÔNG nhắc tổng tài sản, doanh thu, dòng tiền nếu không có.

    - analysis.news: Theo PROMPT PTCB, PHẢI gồm 3 phần riêng biệt (dấu ## hoặc **):
      1. **Tác động về mô đến Ngành**: Cách chính sách/tin tức tác động TÍCH CỰC / TIÊU CỰC tới tổng cầu, hành vi tiêu dùng/đầu tư, hoạt động ngành.
      2. **Tác động vi mô đến Mã [TÊN MÃ]**: Chính sách nào tác động trực tiếp tới yếu tố nào của công ty? Công ty có lợi thế cạnh tranh gì để phòng thủ/tận dụng?
      3. **Kết luận triển vọng và định giá lại**: BẮT BUỘC GIẢI THÍCH rõ tác động là TÍCH CỰC (tăng triển vọng, giá tăng) hay TIÊU CỰC (giảm triển vọng, giá có rủi ro).
      KHÔNG được để mơ hồ hoặc không kết luận.

    - analysis.summary: Kết luận tổng hợp ĐỊNH TÍNH. TUYỆT ĐỐI KHÔNG nêu con số giá mua / chốt lời / cắt lỗ / số nến giữ / tỷ lệ R/R cụ thể — hệ thống sẽ tự tính và chèn vào cuối. Nếu recommendation = Mua: giải thích vì sao đáng mua và mức độ phù hợp với kỳ hạn (không kèm số liệu giá). Nếu recommendation = Chờ: giải thích các yếu tố kỹ thuật/cơ bản nào chưa đạt điều kiện.

PHẦN IV — GIÁ MUA/CHỐT LỜI/CẮT LỖ VÀ QUẢN TRỊ RỦI RO (HARD BOUNDARIES)

Hệ thống chỉ sử dụng khung nến ngày (`interval` = "1d"). Dựa vào kỳ hạn đầu tư (`investment_horizon` từ risk_appetite),
áp dụng các giới hạn cứng (HARD BOUNDARIES) sau đây để xác định mức chốt lời (TP), cắt lỗ (SL) và số nến giữ tối đa (max_hold_candles):

- Kỳ hạn NGẮN HẠN (1d candle): TP [8%, 15%] từ giá mua; SL [4%, 7%]; max_hold_candles [5, 15].
- Kỳ hạn TRUNG HẠN (1d candle): TP [15%, 30%] từ giá mua; SL [7%, 12%]; max_hold_candles [15, 60].
- Kỳ hạn DÀI HẠN (1d candle): TP [40%, 80%] từ giá mua; SL [15%, 20%]; max_hold_candles [120, 260].

QUY TẮC TINH CHỈNH (CÓ GIỚI HẠN):
1. Các khoảng TP, SL, max_hold_candles nêu trên là HARD BOUNDARIES — tuyệt đối bắt buộc.
   Bạn CHỈ được phép tinh chỉnh MỨC GIÁ TRONG PHẠM VI các giới hạn đó, dựa vào:
   - ATR (2×ATR) làm SL tham chiếu.
   - Vùng kháng cự gần nhất → TP tham chiếu.
   - Vùng hỗ trợ gần nhất → SL tham chiếu.
   - Bollinger Bands: SL >= lower band.
   TUYỆT ĐỐI KHÔNG vượt ra ngoài hard boundaries (vd Trung hạn: SL phải [7%, 12%], không được < 7% hoặc > 12%).

2. Tỷ lệ Risk/Reward (TP/SL, tính bằng %) tối thiểu >= 1.5.
   Nếu sau khi tinh chỉnh mà R/R < 1.5, PHẢI chuyển recommendation thành "Chờ" (dù technical_score >= ngưỡng).
   Ưu tiên quy tắc này để tránh lệnh mua có rủi ro cao không xứng đáng.

- Nếu recommendation = Mua:
    * entry_price gần current_price (trong khoảng ±0.5%)
    * stop_loss_price < entry_price < take_profit_price
    * Giải thích ngắn gọn tỷ lệ R/R trong phần analysis
- Nếu recommendation = Chờ:
    * entry_price, take_profit_price, stop_loss_price, max_hold_candles đặt là null

QUY TẮC BẮT BUỘC (PROMPT PTCB):
    ✓ Không bịa số liệu — chỉ nhắc chỉ số THỰC SỰ có trong dữ liệu.
    ✓ Không override logic tổng hợp ở Phần II (hard rules: technical ≥ ngưỡng, fundamental ≠ weak, article ≠ negative).
    ✓ Nếu nguồn thiếu dữ liệu, ghi rõ "Không có dữ liệu [nguồn]" — CHỈ dùng fallback này khi cờ = false.
    ✓ KHÔNG tự sinh confidence — hệ thống sẽ tính từ technical_score, fundamental_health, article_sentiment.
    ✓ Fundamental: viết NHIỀU ĐOẠN riêng biệt (mỗi nhóm/cấu phần = 1 đoạn in đậm), KHÔNG GỘP.
    ✓ Fundamental: BẮT BUỘC trích dẫn CAGR (ít nhất 1 chỉ số/nhóm, dạng "X%/năm") + đối chiếu trung vị ngành.
    ✓ Fundamental: CAGR "—" = không tính được → nói "không tính được CAGR", không suy diễn.
    ✓ Fundamental: DUPONT ANALYSIS bắt buộc nếu có ROE + biên LN + vòng quay + đòn bẩy → giải thích 3 điểm chiến lược.
    ✓ Fundamental (ngành tài chính): dùng P/B để định giá, TUYỆT ĐỐI KHÔNG nhắc P/E hay EV/EBITDA.
    ✓ News: viết 3 phần (tác động về mô → vi mô → kết luận), BẮT BUỘC giải thích TÍCH CỰC / TIÊU CỰC rõ ràng.
    ✓ Đọc ĐÚNG chiều CAGR: CAGR dương = tăng, CAGR âm = giảm (KHÔNG mô tả ngược).
    ✓ Hard Boundaries: TP/SL/hold PHẢI nằm trong khoảng theo kỳ hạn, R/R >= 1.5 (nếu không → "Chờ").
    ✓ KHÔNG nhắc lại quyết định Mua/Chờ hay confidence score ở bất kỳ trường nào trong analysis.
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
    horizon = normalize_horizon(investment_horizon)

    # Trọng số thủ công người dùng nhập qua data_selection.weight (news/technical/
    # fundamental, đã validate tổng = 1.0). Map "news" → khóa nội bộ "article".
    # None nếu người dùng không truyền → dùng mặc định theo kỳ hạn.
    user_weight = get_selection(state).get("weight")
    base_weights = (
        {
            "technical":   user_weight.get("technical", 0.0),
            "fundamental": user_weight.get("fundamental", 0.0),
            "article":     user_weight.get("news", 0.0),
        }
        if user_weight else None
    )

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
        # Nguồn KHÔNG có dữ liệu (bị người dùng tắt hoặc DB không có) → 0 điểm,
        # không để mức trung lập 0.5 gây hiểu lầm là nguồn đó vẫn đóng góp. Quyết
        # định mua/bán không bị ảnh hưởng: confidence vẫn loại các nguồn này ra
        # (xem _effective_weights), nên 0 ở đây chỉ mang tính hiển thị.
        score = {
            "news":        round(news_component, 4) if has_news        else 0.0,
            "technical":   round(tech_component, 4) if has_technical   else 0.0,
            "fundamental": round(fund_component, 4) if has_fundamental else 0.0,
        }
        confidence, effective_weights = _compute_confidence(
            technical_score     = parsed.technical_score,
            fundamental_health  = parsed.fundamental_health,
            article_sentiment   = parsed.article_sentiment,
            has_technical       = has_technical,
            has_fundamental     = has_fundamental,
            has_article         = has_news,
            technical_max_score = technical_max_score,
            horizon             = horizon,
            base_weights        = base_weights,
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