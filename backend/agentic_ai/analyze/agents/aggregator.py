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
            "Quyết định cuối dựa trên tổng hợp 3 nguồn:\n"
            "  - technical_score: 0–5\n"
            "  - article_sentiment: positive | neutral | negative\n"
            "  - fundamental_health: strong | neutral | weak\n"
            "\n"
            "  Logic tổng hợp:\n"
            "  Mua  = technical_score >= 3\n"
            "         VÀ article_sentiment != negative\n"
            "         VÀ fundamental_health != weak\n"
            "  Chờ  = mọi trường hợp còn lại\n"
            "\n"
            "  Nếu article hoặc fundamental không có dữ liệu\n"
            "  → bỏ qua điều kiện đó, chỉ dùng điều kiện còn lại"
        )
    )

    analysis: str = Field(
        description=(
            "Phân tích tổng hợp gồm 4 phần:\n"
            "  1. Quyết định: Mua/Chờ và lý do tổng hợp\n"
            "  2. Kỹ thuật: total_score x/5, điểm từng indicator\n"
            "  3. Tin tức: sentiment và các điểm chính\n"
            "  4. Cơ bản: sức khỏe tài chính, các chỉ số nổi bật"
        )
    )

    confidence: Literal["high", "medium", "low"] = Field(
        description=(
            "Mức độ tin cậy của quyết định:\n"
            "  high   = cả 3 nguồn đồng thuận\n"
            "  medium = 2/3 nguồn đồng thuận, hoặc 1 nguồn thiếu dữ liệu\n"
            "  low    = các nguồn mâu thuẫn nhau, hoặc 2 nguồn thiếu dữ liệu"
        )
    )

    data_sources_used: list[Literal["technical", "article", "fundamental"]] = Field(
        description="Danh sách nguồn dữ liệu thực sự có dữ liệu và được dùng"
    )


# ─────────────────────────────────────────────────────────────
# 🧠 System Prompt
# ─────────────────────────────────────────────────────────────

AGGREGATOR_SYSTEM_PROMPT = """
Bạn là chuyên gia phân tích đầu tư chứng khoán Việt Nam.
Bạn nhận dữ liệu từ 3 nguồn và tổng hợp thành quyết định Mua/Chờ.

PHẦN I — ĐÁNH GIÁ TỪNG NGUỒN

1. Technical (bắt buộc):
     Đọc total_score từ technical_analysis_agent.
     Không tự tính lại.

2. Article (tùy chọn):
     Nếu có dữ liệu: đánh giá sentiment tổng thể là
         positive  = tin tức tích cực rõ ràng
         neutral   = không rõ chiều hoặc lẫn lộn
         negative  = tin tức tiêu cực rõ ràng
     Nếu "Không có tin tức hữu ích" hoặc thiếu dữ liệu:
         đánh dấu là không có dữ liệu, bỏ qua điều kiện này.

3. Fundamental (tùy chọn):
     Nếu có dữ liệu: đánh giá sức khỏe tài chính là
         strong  = ROE > 15%, P/E hợp lý, nợ thấp, tăng trưởng dương
         neutral = chỉ số trung bình, không có dấu hiệu cực đoan
         weak    = ROE thấp, nợ cao, tăng trưởng âm, P/E quá cao
     Nếu thiếu dữ liệu: bỏ qua điều kiện này.

PHẦN II — LOGIC TỔNG HỢP (CỨNG, KHÔNG OVERRIDE)

Mua = technical_score >= 3
            VÀ article_sentiment != negative  (nếu có dữ liệu)
            VÀ fundamental_health != weak     (nếu có dữ liệu)

Chờ = mọi trường hợp còn lại

Ví dụ:
    score=4, article=positive, fundamental=strong  → Mua, confidence=high
    score=4, article=negative, fundamental=strong  → Chờ, confidence=medium
    score=4, article=N/A,      fundamental=strong  → Mua, confidence=medium
    score=2, article=positive, fundamental=strong  → Chờ, confidence=high
    score=4, article=N/A,      fundamental=N/A     → Mua, confidence=low

PHẦN III — VIẾT analysis

Viết theo thứ tự:
    1. Quyết định Mua/Chờ, confidence, lý do tổng hợp 1–2 câu
    2. Kỹ thuật: total_score x/5, từng indicator (RSI→MA→BOLL→MACD→KDJ)
    3. Tin tức: sentiment đánh giá được, dẫn 1–2 điểm chính
    4. Cơ bản: health đánh giá được, dẫn 2–3 chỉ số nổi bật

QUY TẮC BẮT BUỘC:
    ✓ Không bịa số liệu
    ✓ Không override logic tổng hợp ở Phần II
    ✓ Nếu nguồn nào thiếu dữ liệu, ghi rõ "Không có dữ liệu [nguồn]"
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
    article = results.get("article_agent", "")
    fundamental = results.get("fundamental_analysis_agent", "")

    article_text = article if article else "Không có dữ liệu"
    fundamental_text = fundamental if fundamental else "Không có dữ liệu"

    analysis_message = f"""
DỮ LIỆU PHÂN TÍCH:

=== TECHNICAL ANALYSIS ===
{json.dumps(technical, ensure_ascii=False, indent=2)}

=== ARTICLE SENTIMENT ===
{article_text}

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
                "confidence":        "low",
                "data_sources_used": [],
                "analysis":          "Lỗi hệ thống — vui lòng thử lại sau.",
            },
        }