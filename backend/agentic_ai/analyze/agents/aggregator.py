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
            "Hành động đề xuất dựa trên total_score:\n"
            "  'Mua'  = total_score >= 3\n"
            "  'Chờ' = total_score < 3"
        )
    )

    analysis: str = Field(
        description=(
            "Phân tích tổng thể. Bao gồm:\n"
            "  1. Tổng score (total_score/5) và kết luận Mua/Chờ\n"
            "  2. Từng indicator theo thứ tự RSI → MA → BOLL → MACD → KDJ: "
            "score và reason, dẫn số liệu cụ thể\n"
            "  3. Nhận xét ngắn về xu hướng kỹ thuật tổng thể"
        )
    )


# ─────────────────────────────────────────────────────────────
# 🧠 System Prompt
# ─────────────────────────────────────────────────────────────

AGGREGATOR_SYSTEM_PROMPT = """
Bạn là chuyên gia phân tích kỹ thuật chứng khoán Việt Nam.

Bạn nhận dữ liệu từ technical_analysis_agent. Điểm số đã được tính sẵn —
nhiệm vụ của bạn chỉ là đọc, tóm tắt và đưa ra quyết định.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHẦN I — CẤU TRÚC DỮ LIỆU
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  technical_analysis_agent:
    total_score: int          ← tổng điểm 0–5, đã tính sẵn
    indicators:
      rsi:  { value: {...}, score: 0|1, reason: string }
      ma:   { value: {...}, score: 0|1, reason: string }
      boll: { value: {...}, score: 0|1, reason: string }
      macd: { value: {...}, score: 0|1, reason: string }
      kdj:  { value: {...}, score: 0|1, reason: string }

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHẦN II — QUYẾT ĐỊNH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Đọc total_score trực tiếp — KHÔNG tự tính lại:

  total_score >= 3  →  "Mua"
  total_score < 3   →  "Chờ"

Đây là rule cứng — KHÔNG override dù bạn thấy các yếu tố khác.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHẦN III — VIẾT analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Viết analysis theo thứ tự:
  1. Mở đầu: total_score x/5 → Mua hoặc Chờ
  2. Từng indicator (RSI → MA → BOLL → MACD → KDJ):
     dùng lại reason từ dữ liệu, kèm số liệu cụ thể từ value
  3. Kết: nhận xét ngắn về xu hướng kỹ thuật tổng thể

QUY TẮC BẮT BUỘC:
  ✓ Không bịa số liệu ngoài dữ liệu được cung cấp
  ✓ Đọc total_score trực tiếp, không tự cộng lại
  ✓ Không override rule total_score >= 3 → Mua
  ✓ Dùng lại reason từ dữ liệu, không diễn giải lại theo ý mình
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


# ─────────────────────────────────────────────────────────────
# 🚀 Aggregator Agent
# ─────────────────────────────────────────────────────────────

def aggregator_agent(state: AgentState) -> AgentState:
    print("[Aggregator] Tổng hợp kết quả từ technical_analysis_agent...")

    client     = _get_openai_client()
    results    = state.get("agent_results", {})
    user_input = state.get("user_input", "")

    analysis_message = f"""
DỮ LIỆU PHÂN TÍCH:

{json.dumps(results, ensure_ascii=False, indent=2)}

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
            "recommendation": parsed.recommendation,
            "analysis":       parsed.analysis,
        }

        print("[Aggregator] Output:")
        print(json.dumps(output, ensure_ascii=False, indent=2))

        return {"final_output": output}

    except Exception as e:
        print(f"[Aggregator] Error: {str(e)}")

        return {
            "error": str(e),
            "final_output": {
                "recommendation": "Chờ",
                "analysis":       "Lỗi hệ thống — vui lòng thử lại sau.",
            },
        }