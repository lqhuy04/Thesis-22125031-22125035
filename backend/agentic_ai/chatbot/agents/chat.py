"""
agentic_ai/chatbot/agents/chat.py — Chat Agent (agent duy nhất của chatbot)

Nhận tin nhắn mới + lịch sử hội thoại, gọi thẳng OpenAI và trả về reply.
Không truy vấn DB, không phân loại intent.
"""

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from agentic_ai.service.openai_service import _get_openai_client
from agentic_ai.chatbot.state import ChatbotState

CHAT_SYSTEM_PROMPT = """
Bạn là trợ lý phân tích chứng khoán Việt Nam, đang trò chuyện trực tiếp với nhà đầu tư.

Nhiệm vụ: trò chuyện và trả lời câu hỏi của người dùng một cách tự nhiên, thân thiện.

Quy tắc:
- Trả lời bằng tiếng Việt, ngắn gọn, dễ hiểu.
- Có thể giải thích kiến thức chứng khoán / tài chính khi được hỏi.
- Không bịa số liệu thị trường. Nếu không chắc, hãy nói rõ là bạn không có dữ liệu thời gian thực.
"""


def _to_openai_messages(history: list[BaseMessage], user_input: str) -> list[dict]:
    """Chuyển lịch sử LangGraph + tin nhắn mới sang định dạng messages của OpenAI."""
    messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
    for msg in history:
        role = "assistant" if isinstance(msg, AIMessage) else "user"
        messages.append({"role": role, "content": msg.content})
    messages.append({"role": "user", "content": user_input})
    return messages


def chat_agent(state: ChatbotState) -> dict:
    user_input = state["user_input"]
    history = state.get("messages", [])

    print(f"[Chat Agent] User: {user_input}")

    try:
        client = _get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.5,
            messages=_to_openai_messages(history, user_input),
        )
        reply = response.choices[0].message.content
        print(f"[Chat Agent] Reply: {reply[:80]}...")

        return {
            # add_messages sẽ append cặp tin nhắn này vào lịch sử của thread
            "messages": [HumanMessage(content=user_input), AIMessage(content=reply)],
            "final_output": reply,
            "error": None,
        }

    except Exception as e:
        print(f"[Chat Agent] Lỗi: {e}")
        return {"final_output": "", "error": f"Lỗi khi gọi OpenAI: {e}"}
