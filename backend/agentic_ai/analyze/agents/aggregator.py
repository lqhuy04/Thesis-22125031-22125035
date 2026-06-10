"""
aggregator.py — Aggregator Agent (simplified)

Đọc output từ technical_analysis_agent, tổng hợp và đưa ra quyết định Mua/Chờ.
Rule: total_score >= 3/5 → Mua, ngược lại → Chờ.

Confidence được tính deterministic trong Python (không để LLM tự sinh),
dựa trên 3 nguồn với trọng số bằng nhau:

  confidence = (1/3) * technical_component     # technical_score / 5
             + (1/3) * fundamental_component   # strong=1.0 / neutral=0.5 / weak=0.0 / N/A=0.5
             + (1/3) * article_component       # positive=1.0 / neutral=0.5 / negative=0.0 / N/A=0.5

  Ngưỡng chấp nhận lệnh Mua: confidence >= CONFIDENCE_THRESHOLD (0.55)
"""

import json
from typing import Literal
from pydantic import BaseModel, Field

from agentic_ai.service.openai_service import _get_openai_client
from agentic_ai.analyze.state import AgentState


# ─────────────────────────────────────────────────────────────
# ⚙️ Confidence Config
# ─────────────────────────────────────────────────────────────

# Ngưỡng tối thiểu để chấp nhận lệnh Mua
CONFIDENCE_THRESHOLD = 0.55

# Trọng số từng nguồn (bằng nhau, tổng = 1.0)
CONFIDENCE_WEIGHTS = {
    "technical":   1 / 3,
    "fundamental": 1 / 3,
    "article":     1 / 3,
}

# Điểm trung lập khi nguồn thiếu dữ liệu (N/A)
_NA_SCORE = 0.5

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


def _compute_confidence(
    technical_score: int,
    fundamental_health: str,
    article_sentiment: str,
) -> float:
    """
    Tính confidence score [0.0, 1.0] hoàn toàn bằng rule cứng.

    3 nguồn, trọng số đều nhau (1/3 mỗi nguồn):
      technical_component   = technical_score / 5
      fundamental_component = _FUNDAMENTAL_SCORE_MAP[fundamental_health]
      article_component     = _ARTICLE_SCORE_MAP[article_sentiment]

    Khi nguồn thiếu dữ liệu (N/A) → dùng _NA_SCORE = 0.5 (trung lập),
    không redistribute trọng số sang nguồn khác.
    """
    technical_component   = max(0.0, min(technical_score, 5)) / 5.0
    fundamental_component = _FUNDAMENTAL_SCORE_MAP.get(fundamental_health, _NA_SCORE)
    article_component     = _ARTICLE_SCORE_MAP.get(article_sentiment, _NA_SCORE)

    w = CONFIDENCE_WEIGHTS
    score = (
        w["technical"]   * technical_component
        + w["fundamental"] * fundamental_component
        + w["article"]     * article_component
    )

    return round(score, 4)


# ─────────────────────────────────────────────────────────────
# 📦 Structured Output Schema
# ─────────────────────────────────────────────────────────────

class InvestmentRecommendation(BaseModel):
    recommendation: Literal["Mua", "Chờ"] = Field(
        description=(
            "Quyết định cuối dựa trên tổng hợp 2 nguồn:\n"
            "  - technical_score: 0–5\n"
            "  - fundamental_health: strong | neutral | weak\n"
            "\n"
            "  Logic tổng hợp:\n"
            "  Mua  = technical_score >= 3\n"
            "         VÀ fundamental_health != weak (nếu có dữ liệu)\n"
            "  Chờ  = mọi trường hợp còn lại\n"
            "\n"
            "  Nếu fundamental không có dữ liệu\n"
            "  → bỏ qua điều kiện đó, chỉ dùng technical"
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

    analysis: str = Field(
        description=(
            "Phân tích tổng hợp bằng tiếng Việt, gồm các phần:\n"
            "  1. Kỹ thuật: Đi qua từng chỉ số (RSI, MA, Bollinger Bands, MACD, KDJ), chỉ ra tích cực/tiêu cực, tại sao, dẫn chứng số liệu.\n"
            "  2. Cơ bản: Tóm tắt phân tích cơ bản đầy đủ (định giá, sinh lời, tăng trưởng, sức khỏe tài chính, dòng tiền).\n"
            "  3. Tin tức: Tóm tắt dữ liệu tin tức và nhắc tới những thông tin nổi bật (nếu có).\n"
            "  4. Giá mua/TP/SL và thời gian giữ: mức giá đề xuất và giải thích R/R (nếu Mua). Không được nhắc lại recommendation và confidence."
        )
    )

    # ── Raw signals để Python tính confidence ──────────────────
    technical_score: int = Field(
        description=(
            "Điểm kỹ thuật tổng hợp đọc trực tiếp từ technical_analysis_agent. "
            "Giá trị nguyên 0–5. KHÔNG tự tính lại."
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

PHẦN I — ĐÁNH GIÁ TỪNG NGUỒN

1. Technical (bắt buộc):
     Đọc total_score từ technical_analysis_agent. KHÔNG tự tính lại.

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

Mua = technical_score >= 3
            VÀ fundamental_health != weak     (nếu có dữ liệu)

Chờ = mọi trường hợp còn lại

Ví dụ:
    score=4, fundamental=strong   → Mua
    score=4, fundamental=weak     → Chờ
    score=4, fundamental=N/A      → Mua
    score=2, fundamental=strong   → Chờ

PHẦN III — VIẾT analysis

Viết văn bản phân tích tổng hợp (bằng tiếng Việt) chi tiết và khách quan, tuân thủ nghiêm ngặt các quy tắc cấu trúc sau:
    - TUYỆT ĐỐI KHÔNG nhắc lại quyết định cuối cùng (Mua/Chờ) và điểm số confidence ở bất kỳ đâu trong phần analysis này.
    - Cấu trúc bài phân tích gồm các phần sau:
        1. Phân tích kỹ thuật: Đi qua từng chỉ số kỹ thuật cụ thể (RSI, MA, Bollinger Bands, MACD, KDJ). Với từng chỉ số, hãy chỉ rõ trạng thái là Tích cực hay Tiêu cực, lý giải tại sao và dẫn chứng số liệu/giá trị cụ thể.
        2. Phân tích cơ bản: Tóm tắt phân tích cơ bản một cách đầy đủ và toàn diện dựa trên dữ liệu (gồm định giá, sức khỏe tài chính, khả năng sinh lời, tăng trưởng, dòng tiền).
        3. Tin tức: Tóm tắt dữ liệu tin tức, nhắc tới những thông tin/sự kiện nổi bật nhất (nếu có).
        4. Mức giá & Quản trị rủi ro (nếu recommendation = Mua): Nêu rõ mức giá đề xuất, số nến giữ tối đa và tỷ lệ Risk/Reward. Nếu recommendation = Chờ, giải thích các yếu tố kỹ thuật hoặc cơ bản nào chưa đạt điều kiện mà không đề xuất giá.

PHẦN IV — GIÁ MUA/CHỐT LỜI/CẮT LỖ

Đọc `interval` từ technical analysis để xác định kỳ hạn, rồi áp dụng bảng sau:

┌──────────────┬──────────────┬──────────────────┬──────────────────┬──────────────────────┐
│ Kỳ hạn       │ interval     │ TP (% từ entry)  │ SL (% từ entry)  │ max_hold_candles     │
├──────────────┼──────────────┼──────────────────┼──────────────────┼──────────────────────┤
│ Ngắn hạn     │ 1h           │ 4% - 8%          │ 2% - 4%          │ 24 - 72 nến (1-3 ngày)│
│ Ngắn hạn     │ 1d           │ 8% - 15%         │ 4% - 7%          │ 5 - 15 nến           │
│ Trung hạn    │ 1d           │ 15% - 30%        │ 7% - 12%         │ 15 - 60 nến          │
│ Trung hạn    │ 1w           │ 20% - 40%        │ 10% - 15%        │ 8 - 24 nến           │
│ Dài hạn      │ 1w           │ 40% - 80%        │ 15% - 20%        │ 24 - 52 nến          │
│ Dài hạn      │ 1M           │ 50% - 100%       │ 15% - 25%        │ 6 - 18 nến           │
└──────────────┴──────────────┴──────────────────┴──────────────────┴──────────────────────┘

Trong phạm vi trên, tinh chỉnh thêm dựa vào:
- Biên độ ATR gần nhất (nếu có trong technical): dùng 2*ATR làm SL tham chiếu
- Vùng kháng cự gần nhất làm TP tham chiếu
- Vùng hỗ trợ gần nhất làm SL tham chiếu
- Nếu technical có bollinger band: SL không nên thấp hơn lower band

Tỷ lệ Risk/Reward tối thiểu: TP/SL >= 1.5
Nếu không đạt tỷ lệ này → recommendation = Chờ dù score >= 3.

- Nếu recommendation = Mua:
    * entry_price gần current_price (±0.5%)
    * stop_loss_price < entry_price < take_profit_price
    * Giải thích ngắn tỷ lệ R/R trong analysis
- Nếu recommendation = Chờ:
    * entry_price, take_profit_price, stop_loss_price, max_hold_candles = null

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

    # Lấy interval từ plan để truyền cho aggregator
    plan = state.get("plan", {})
    interval = plan.get("technical_analysis_agent", {}).get("interval", "1d")
    investment_horizon = state.get("risk_appetite", {}).get("period", "Trung hạn")

    analysis_message = f"""
DỮ LIỆU PHÂN TÍCH:

=== CONTEXT ===
interval: {interval}
investment_horizon: {investment_horizon}

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

    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": AGGREGATOR_SYSTEM_PROMPT},
                {"role": "user",   "content": analysis_message},
            ],
            response_format=InvestmentRecommendation,
        )

        parsed: InvestmentRecommendation = response.choices[0].message.parsed

        # ── Tính confidence deterministic từ 3 raw signals ────────────────────
        confidence = _compute_confidence(
            technical_score    = parsed.technical_score,
            fundamental_health = parsed.fundamental_health,
            article_sentiment  = parsed.article_sentiment,
        )

        # ── Override recommendation nếu confidence dưới ngưỡng ────────────────
        recommendation = parsed.recommendation
        if recommendation == "Mua" and confidence < CONFIDENCE_THRESHOLD:
            print(
                f"[Aggregator] confidence={confidence} < threshold={CONFIDENCE_THRESHOLD} "
                f"→ override Mua → Chờ"
            )
            recommendation = "Chờ"

        if recommendation == "Chờ":
            entry_price       = None
            take_profit_price = None
            stop_loss_price   = None
            max_hold_candles  = None
        else:
            entry_price       = parsed.entry_price
            take_profit_price = parsed.take_profit_price
            stop_loss_price   = parsed.stop_loss_price
            max_hold_candles  = parsed.max_hold_candles

        output = {
            "recommendation":       recommendation,
            "entry_price":          entry_price,
            "take_profit_price":    take_profit_price,
            "stop_loss_price":      stop_loss_price,
            "max_hold_candles":     max_hold_candles,
            "confidence":           confidence,
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "confidence_breakdown": {
                "technical_score":    parsed.technical_score,
                "fundamental_health": parsed.fundamental_health,
                "article_sentiment":  parsed.article_sentiment,
                "weights":            {k: round(v, 4) for k, v in CONFIDENCE_WEIGHTS.items()},
            },
            "analysis":             parsed.analysis,
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
                "confidence":           0.0,
                "confidence_threshold": CONFIDENCE_THRESHOLD,
                "confidence_breakdown": {},
                "analysis":             "Lỗi hệ thống — vui lòng thử lại sau.",
            },
        }