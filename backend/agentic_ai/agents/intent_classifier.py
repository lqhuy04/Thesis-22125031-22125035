"""
intent_classifier.py — Intent Classifier Agent

Phân loại ý định của user trước khi vào pipeline chính.

intent_type:
    - stock_analysis   → cần DB + full pipeline
    - general_question → hỏi kiến thức, trả lời thẳng
    - clarification    → thiếu thông tin, hỏi lại user
    - out_of_scope     → ngoài phạm vi hệ thống
"""

from typing import Literal
from pydantic import BaseModel, Field

from agentic_ai.service.openai_service import _get_openai_client
from agentic_ai.state import AgentState


# ─────────────────────────────────────────────────────────────
# 📦 Structured Output Schema
# ─────────────────────────────────────────────────────────────

class IntentClassification(BaseModel):
    intent_type: Literal[
        "stock_analysis",
        "general_question",
        "clarification",
        "out_of_scope"
    ] = Field(
        description=(
            "Phân loại ý định của user:\n"
            "- stock_analysis: yêu cầu phân tích / gợi ý đầu tư một mã cổ phiếu cụ thể\n"
            "- general_question: câu hỏi kiến thức chứng khoán chung (không cần dữ liệu DB)\n"
            "- clarification: yêu cầu chưa đủ thông tin để xử lý (thiếu mã CP, quá mơ hồ)\n"
            "- out_of_scope: hoàn toàn ngoài phạm vi hệ thống phân tích chứng khoán"
        )
    )

    symbol: str | None = Field(
        default=None,
        description=(
            "Mã cổ phiếu được đề cập (VD: VNM, FPT, VIC). "
            "Chỉ điền khi intent_type = 'stock_analysis'. "
            "Viết HOA, không kèm sàn giao dịch."
        )
    )

    instant_reply: str | None = Field(
        default=None,
        description=(
            "Câu trả lời / câu hỏi lại trả thẳng cho user. "
            "Bắt buộc điền khi intent_type != 'stock_analysis'. "
            "Trả lời bằng tiếng Việt, thân thiện, ngắn gọn."
        )
    )


# ─────────────────────────────────────────────────────────────
# 🧠 Prompt
# ─────────────────────────────────────────────────────────────

INTENT_CLASSIFIER_SYSTEM_PROMPT = """
Bạn là bộ phân loại ý định (intent classifier) cho chatbot phân tích chứng khoán Việt Nam.

Nhiệm vụ: Đọc input của user và phân loại vào đúng intent_type.

────────────────────────
PHÂN LOẠI:

1. stock_analysis
   - User hỏi về một mã cổ phiếu cụ thể
   - Ví dụ: "VNM có nên mua không?", "Phân tích FPT giúp tôi", "HPG đang như thế nào?"
   - Bắt buộc: extract symbol vào trường symbol

2. general_question
   - Câu hỏi kiến thức chứng khoán, tài chính, không cần dữ liệu thực
   - Ví dụ: "RSI là gì?", "Cách đọc MACD?", "P/E ratio dùng để làm gì?"
   - Trả lời thẳng vào instant_reply

3. clarification
   - Yêu cầu phân tích nhưng thiếu thông tin hoặc quá mơ hồ
   - Ví dụ: "Phân tích cổ phiếu ngân hàng", "Mua gì bây giờ?"
   - Hỏi lại cụ thể vào instant_reply (ví dụ: "Bạn muốn phân tích mã cụ thể nào?")

4. out_of_scope
   - Hoàn toàn không liên quan đến chứng khoán / tài chính
   - Ví dụ: "Hôm nay thời tiết thế nào?", "Viết thơ cho tôi"
   - Giải thích nhẹ nhàng vào instant_reply

────────────────────────
QUY TẮC:
- symbol luôn là None nếu intent_type != "stock_analysis"
- instant_reply luôn là None nếu intent_type = "stock_analysis"
- instant_reply bắt buộc có giá trị nếu intent_type != "stock_analysis"
- Trả lời bằng tiếng Việt
"""


# ─────────────────────────────────────────────────────────────
# 🚀 Intent Classifier Agent
# ─────────────────────────────────────────────────────────────

def intent_classifier_agent(state: AgentState) -> dict:
    print("[Intent Classifier] Phân loại input...")

    client = _get_openai_client()
    user_input = state.get("user_input", "")

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": INTENT_CLASSIFIER_SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
        response_format=IntentClassification,
    )

    result: IntentClassification = response.choices[0].message.parsed

    print(f"[Intent Classifier] intent_type = {result.intent_type}")
    if result.symbol:
        print(f"[Intent Classifier] symbol = {result.symbol}")
    if result.instant_reply:
        print(f"[Intent Classifier] instant_reply = {result.instant_reply}")

    return {
        "intent": result.model_dump(),
        # Nếu classifier extract được symbol thì ghi vào state luôn
        # để Orchestrator không phải tự đoán
        "symbol": result.symbol or state.get("symbol", ""),
    }