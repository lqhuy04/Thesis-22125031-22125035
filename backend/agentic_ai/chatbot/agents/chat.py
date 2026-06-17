"""
agentic_ai/chatbot/agents/chat.py — Chat Agent (xử lý GREETING)

Xử lý chào hỏi, smalltalk, câu hỏi về bản thân chatbot.
Intent GREETING được phân loại bởi intent_classifier_agent.
"""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from agentic_ai.chatbot.state import ChatbotState
from agentic_ai.service.openai_service import _get_openai_client

CHAT_SYSTEM_PROMPT = """
Bạn là trợ lý phân tích chứng khoán Việt Nam, đang trò chuyện trực tiếp với nhà đầu tư.

Nhiệm vụ: chào hỏi và trò chuyện thân thiện với người dùng.

Quy tắc:
- NGÔN NGỮ: Trả lời bằng ĐÚNG ngôn ngữ người dùng dùng trong câu hỏi
  (hỏi tiếng Anh → trả lời tiếng Anh; hỏi tiếng Việt → trả lời tiếng Việt).
- Tự nhiên, ngắn gọn.
- Khi được hỏi về khả năng, hãy giới thiệu: bạn có thể giải thích khái niệm chứng khoán,
  phân tích kỹ thuật/cơ bản, và (sắp có) truy vấn dữ liệu thị trường thực tế.
- Không cần phân tích chứng khoán trong lượt này — chỉ chào hỏi và gợi mở.
""".strip()


def _to_openai_messages(history: list[BaseMessage], user_input: str) -> list[dict]:
    messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
    for msg in history[-4:]:  # Chỉ cần vài tin gần nhất cho greeting
        role = "assistant" if isinstance(msg, AIMessage) else "user"
        messages.append({"role": role, "content": msg.content})
    messages.append({"role": "user", "content": user_input})
    return messages


def chat_agent(state: ChatbotState) -> dict:
    user_input = state["user_input"]
    history: list[BaseMessage] = state.get("messages", [])

    print(f"[Chat Agent] >>> Intent : GREETING")
    print(f"[Chat Agent] >>> Input  : {user_input!r}")

    try:
        client = _get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.6,
            messages=_to_openai_messages(history, user_input),
        )
        reply = response.choices[0].message.content

        print(f"[Chat Agent] >>> Reply  : {reply[:120]}{'...' if len(reply) > 120 else ''}")

        return {
            "messages": [HumanMessage(content=user_input), AIMessage(content=reply)],
            "final_output": reply,
            "error": None,
        }

    except Exception as e:
        print(f"[Chat Agent] >>> ERROR  : {e}")
        return {
            "final_output": "Xin chào! Tôi là trợ lý phân tích chứng khoán. Bạn cần hỗ trợ gì?",
            "error": f"Lỗi Chat Agent: {e}",
        }
