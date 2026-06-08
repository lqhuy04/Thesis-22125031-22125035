"""
agentic_ai/chatbot/agents/intent_classifier.py — Intent Classifier Agent

Phân loại tin nhắn của người dùng vào một trong 4 nhóm:
  - OUT_OF_SCOPE  : Ngoài phạm vi chứng khoán/tài chính → từ chối, set final_output luôn
  - GREETING      : Chào hỏi, smalltalk → route sang chat_agent
  - KNOWLEDGE_QA  : Câu hỏi kiến thức chứng khoán (không cần DB) → route sang qa_agent
  - MARKET_QUERY  : Cần dữ liệu thực tế / phân tích mã cụ thể → route sang qa_agent (tạm thời, Phase 2 sẽ có market_agent)

Xem xét cả lịch sử hội thoại (6 tin gần nhất) để phân loại chính xác hơn.
"""

from typing import Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel

from agentic_ai.chatbot.state import ChatbotState
from agentic_ai.service.openai_service import _get_openai_client

# ─── Constants ──────────────────────────────────────────────────────────────

OUT_OF_SCOPE_REPLY = (
    "Xin lỗi, tôi chỉ hỗ trợ các câu hỏi liên quan đến chứng khoán và tài chính. "
    "Bạn có câu hỏi nào về thị trường, phân tích kỹ thuật, hay đầu tư không?"
)

INTENT_SYSTEM_PROMPT = """
Bạn là bộ phân loại ý định (intent classifier) cho chatbot phân tích chứng khoán Việt Nam.

Phân loại tin nhắn MỚI NHẤT của người dùng vào MỘT trong các nhóm sau:

1. OUT_OF_SCOPE
   Câu hỏi hoàn toàn không liên quan đến chứng khoán, tài chính, đầu tư, kinh tế.
   Ví dụ: "Nấu phở như thế nào?", "Thời tiết Hà Nội", "Python là gì?", "Đặt vé máy bay"

2. GREETING
   Chào hỏi, smalltalk, hỏi về bản thân chatbot, cảm ơn, tạm biệt.
   Ví dụ: "Xin chào", "Bạn là ai?", "Bạn có thể làm gì?", "Cảm ơn", "Tạm biệt"

3. KNOWLEDGE_QA
   Câu hỏi về khái niệm/kiến thức chứng khoán, tài chính — KHÔNG cần dữ liệu thực tế.
   Ví dụ: "RSI là gì?", "MACD hoạt động như thế nào?", "P/E ratio bao nhiêu là tốt?",
           "Phân tích kỹ thuật là gì?", "Chỉ số VN-Index đo lường cái gì?"

4. MARKET_QUERY
   Câu hỏi cần dữ liệu thị trường thực tế hoặc phân tích một mã cổ phiếu cụ thể.
   Ví dụ: "Giá VNM hôm nay bao nhiêu?", "Phân tích kỹ thuật HPG", "Nên mua hay bán VIC?",
           "VN-Index đang ở mức nào?", "Top cổ phiếu tăng mạnh hôm nay"

Lưu ý quan trọng:
- Xem xét LỊCH SỬ HỘI THOẠI để hiểu ngữ cảnh. Ví dụ: "Phân tích thêm đi" sau khi bàn về VNM → MARKET_QUERY.
- Câu hỏi khái niệm tổng quát → KNOWLEDGE_QA, kể cả khi có tên mã cổ phiếu làm ví dụ.
- Câu hỏi về dữ liệu cụ thể, khuyến nghị mua/bán → MARKET_QUERY.
""".strip()


# ─── Pydantic schema cho structured output ──────────────────────────────────

class IntentResult(BaseModel):
    intent: Literal["OUT_OF_SCOPE", "GREETING", "KNOWLEDGE_QA", "MARKET_QUERY"]
    reason: str  # Dùng để debug, không hiển thị cho user


# ─── Agent function ──────────────────────────────────────────────────────────

def intent_classifier_agent(state: ChatbotState) -> dict:
    user_input = state["user_input"]
    history: list[BaseMessage] = state.get("messages", [])

    print(f"\n{'='*60}")
    print(f"[Intent Classifier] >>> Input: {user_input!r}")
    print(f"[Intent Classifier] >>> History length: {len(history)} messages")

    try:
        client = _get_openai_client()

        # Đưa vào 6 tin nhắn gần nhất để classifier có ngữ cảnh
        context_messages = [{"role": "system", "content": INTENT_SYSTEM_PROMPT}]
        for msg in history[-6:]:
            role = "assistant" if isinstance(msg, AIMessage) else "user"
            context_messages.append({"role": role, "content": msg.content})
        context_messages.append({"role": "user", "content": user_input})

        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            temperature=0,  # Deterministic — classifier không cần sáng tạo
            messages=context_messages,
            response_format=IntentResult,
        )

        result: IntentResult = completion.choices[0].message.parsed
        print(f"[Intent Classifier] >>> Intent  : {result.intent}")
        print(f"[Intent Classifier] >>> Reason  : {result.reason}")

        if result.intent == "OUT_OF_SCOPE":
            print(f"[Intent Classifier] >>> Action  : BLOCK — set refusal reply, route to END")
            print(f"{'='*60}\n")
            return {
                "intent": "OUT_OF_SCOPE",
                # Lưu cặp tin nhắn vào history để user thấy trong conversation
                "messages": [
                    HumanMessage(content=user_input),
                    AIMessage(content=OUT_OF_SCOPE_REPLY),
                ],
                "final_output": OUT_OF_SCOPE_REPLY,
                "error": None,
            }

        print(f"[Intent Classifier] >>> Action  : PASS — route to '{result.intent.lower()}' agent")
        print(f"{'='*60}\n")
        return {
            "intent": result.intent,
            "final_output": None,
            "error": None,
        }

    except Exception as e:
        print(f"[Intent Classifier] >>> ERROR: {e}")
        print(f"[Intent Classifier] >>> Fallback to KNOWLEDGE_QA")
        print(f"{'='*60}\n")
        # Fallback an toàn: để qa_agent xử lý
        return {
            "intent": "KNOWLEDGE_QA",
            "error": f"Lỗi classifier: {e}",
        }
