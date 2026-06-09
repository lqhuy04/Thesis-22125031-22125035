"""
aggregator.py — Aggregator Agent (simplified)

Đọc output từ technical_analysis_agent, tổng hợp và đưa ra quyết định Mua/Chờ.
Rule: total_score >= 3/5 → Mua, ngược lại → Chờ.
"""

import json
from typing import Literal
from pydantic import BaseModel, Field

from agentic_ai.service.openai_service import _get_openai_client
from agentic_ai.analyze.state import AgentState


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
        description=(
            "Giá chốt lời đề xuất. Nếu recommendation = Chờ thì để null."
        ),
    )

    stop_loss_price: float | None = Field(
        default=None,
        description=(
            "Giá cắt lỗ đề xuất. Nếu recommendation = Chờ thì để null."
        ),
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
            "Phân tích tổng hợp gồm 4 phần:\n"
            "  1. Quyết định: Mua/Chờ và lý do tổng hợp\n"
            "  2. Kỹ thuật: total_score x/5, điểm từng indicator\n"
            "  3. Cơ bản: sức khỏe tài chính, các chỉ số nổi bật\n"
            "  4. Giá mua/TP/SL và thời gian giữ: nêu rõ mức giá và số nến tối đa"
        )
    )

    confidence: Literal["high", "medium", "low"] = Field(
        description=(
            "Mức độ tin cậy của quyết định:\n"
            "  high   = technical & fundamental đồng thuận\n"
            "  medium = chỉ 1 nguồn mạnh, hoặc 1 nguồn thiếu dữ liệu\n"
            "  low    = tín hiệu yếu hoặc mâu thuẫn"
        )
    )

    data_sources_used: list[Literal["technical", "fundamental"]] = Field(
        description="Danh sách nguồn dữ liệu thực sự có dữ liệu và được dùng"
    )


# ─────────────────────────────────────────────────────────────
# 🧠 System Prompt
# ─────────────────────────────────────────────────────────────

AGGREGATOR_SYSTEM_PROMPT = """
Bạn là chuyên gia phân tích đầu tư chứng khoán Việt Nam.
Bạn nhận dữ liệu từ 2 nguồn và tổng hợp thành quyết định Mua/Chờ.
Nguồn tin tức (article) hiện đang tạm ngưng — bỏ qua hoàn toàn.

PHẦN I — ĐÁNH GIÁ TỪNG NGUỒN

1. Technical (bắt buộc):
     Đọc total_score từ technical_analysis_agent.
     Không tự tính lại.

2. Fundamental (tùy chọn):
     Nếu có dữ liệu: đánh giá sức khỏe tài chính là
         strong  = ROE > 15%, P/E hợp lý, nợ thấp, tăng trưởng dương
         neutral = chỉ số trung bình, không có dấu hiệu cực đoan
         weak    = ROE thấp, nợ cao, tăng trưởng âm, P/E quá cao
     Nếu thiếu dữ liệu: bỏ qua điều kiện này.

PHẦN II — LOGIC TỔNG HỢP (CỨNG, KHÔNG OVERRIDE)

Mua = technical_score >= 3
            VÀ fundamental_health != weak     (nếu có dữ liệu)

Chờ = mọi trường hợp còn lại

Ví dụ:
    score=4, fundamental=strong  → Mua, confidence=high
    score=4, fundamental=weak    → Chờ, confidence=medium
    score=4, fundamental=N/A     → Mua, confidence=medium
    score=2, fundamental=strong  → Chờ, confidence=high

PHẦN III — VIẾT analysis

Viết theo thứ tự:
    1. Quyết định Mua/Chờ, confidence, lý do tổng hợp 1–2 câu
    2. Kỹ thuật: total_score x/5, từng indicator (RSI→MA→BOLL→MACD→KDJ)
    3. Cơ bản: health đánh giá được, dẫn 2–3 chỉ số nổi bật
    4. Giá mua/TP/SL: nêu rõ mức giá đề xuất

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
    * Tất cả = null

QUY TẮC BẮT BUỘC:
    ✓ Không bịa số liệu
    ✓ Không override logic tổng hợp ở Phần II
    ✓ Nếu nguồn nào thiếu dữ liệu, ghi rõ "Không có dữ liệu [nguồn]"
    ✓ KHÔNG dùng article (đang tạm ngưng)
"""


# ─────────────────────────────────────────────────────────────
# 🚀 Aggregator Agent
# ─────────────────────────────────────────────────────────────

def aggregator_agent(state: AgentState) -> AgentState:
    print("[Aggregator] Tổng hợp kết quả từ technical, article, fundamental...")

    client     = _get_openai_client()
    results    = state.get("agent_results", {})
    user_input = state.get("user_input", "")

    technical = results.get("technical_analysis_agent", {})
    fundamental = results.get("fundamental_analysis_agent", "")

    fundamental_text = fundamental if fundamental else "Không có dữ liệu"

    # Lấy interval từ plan để truyền cho aggregator
    plan = state.get("plan", {})
    interval = plan.get("technical_analysis_agent", {}).get("interval", "1d")
    investment_horizon = state.get("risk_appetite", {}).get("period", "Trung hạn")

    analysis_message = f"""
DỮ LIỆU PHÂN TÍCH:

=== TECHNICAL ANALYSIS ===
{json.dumps(technical, ensure_ascii=False, indent=2)}

=== FUNDAMENTAL ANALYSIS ===
=== CONTEXT ===
interval: {interval}
investment_horizon: {investment_horizon}

=== TECHNICAL ANALYSIS ===
{json.dumps(technical, ensure_ascii=False, indent=2)}

=== FUNDAMENTAL ANALYSIS ===
{fundamental_text}

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

        output = {
            "recommendation":    parsed.recommendation,
            "entry_price":       parsed.entry_price,
            "take_profit_price": parsed.take_profit_price,
            "stop_loss_price":   parsed.stop_loss_price,
            "max_hold_candles":  parsed.max_hold_candles,
            "confidence":        parsed.confidence,
            "data_sources_used": parsed.data_sources_used,
            "analysis":          parsed.analysis,
        }

        print("[Aggregator] Output:")
        print(json.dumps(output, ensure_ascii=False, indent=2))

        return {"final_output": output}

    except Exception as e:
        print(f"[Aggregator] Error: {str(e)}")

        return {
            "error": str(e),
            "final_output": {
                "recommendation":    "Chờ",
                "entry_price":       None,
                "take_profit_price": None,
                "stop_loss_price":   None,
                "max_hold_candles":  None,
                "confidence":        "low",
                "data_sources_used": [],
                "analysis":          "Lỗi hệ thống — vui lòng thử lại sau.",
            },
        }