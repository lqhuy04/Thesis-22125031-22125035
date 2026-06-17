"""
agentic_ai/chatbot/agents/qa_agent.py — QA Agent

Xử lý intent KNOWLEDGE_QA: giải thích khái niệm chứng khoán/tài chính, không cần DB.
(MARKET_QUERY đã được tách sang market_agent — text-to-SQL trên Supabase Postgres.)
"""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from agentic_ai.chatbot.state import ChatbotState
from agentic_ai.service.openai_service import _get_openai_client

# ─── System prompts ──────────────────────────────────────────────────────────

QA_SYSTEM_PROMPT = """
Bạn là chuyên gia phân tích chứng khoán Việt Nam với kiến thức sâu rộng về:
- Phân tích kỹ thuật: RSI, MACD, Bollinger Bands, EMA/SMA, các mẫu nến Nhật, hỗ trợ/kháng cự, xu hướng.
- Phân tích cơ bản: P/E, P/B, ROE, EPS, tỷ lệ nợ, dòng tiền, báo cáo tài chính.
- Thị trường chứng khoán Việt Nam: HOSE, HNX, UPCOM, VN-Index, HNX-Index, quy tắc giao dịch T+2.
- Chiến lược đầu tư: value investing, growth investing, momentum, quản lý danh mục, quản lý rủi ro.
- Tâm lý học đầu tư: FOMO, sai lệch nhận thức, kỷ luật giao dịch.

Quy tắc:
- NGÔN NGỮ: Trả lời bằng ĐÚNG ngôn ngữ người dùng dùng trong câu hỏi
  (hỏi tiếng Anh → trả lời tiếng Anh; hỏi tiếng Việt → trả lời tiếng Việt).
- Rõ ràng, có cấu trúc nếu nội dung phức tạp.
- Dùng ví dụ thực tế khi giải thích khái niệm để dễ hiểu hơn.
- Không bịa đặt số liệu hoặc thông tin về cổ phiếu cụ thể.
- Nếu câu hỏi yêu cầu dữ liệu thực tế (giá cổ phiếu, chỉ số hôm nay...) mà bạn không có,
  hãy thành thật nói rõ và gợi ý cách tra cứu hoặc phân tích định tính.
""".strip()


# ─── Helper ──────────────────────────────────────────────────────────────────

def _build_openai_messages(system_prompt: str, history: list[BaseMessage], user_input: str) -> list[dict]:
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        role = "assistant" if isinstance(msg, AIMessage) else "user"
        messages.append({"role": role, "content": msg.content})
    messages.append({"role": "user", "content": user_input})
    return messages


# ─── Agent function ──────────────────────────────────────────────────────────

def qa_agent(state: ChatbotState) -> dict:
    user_input = state["user_input"]
    history: list[BaseMessage] = state.get("messages", [])

    print(f"[QA Agent] >>> Intent : KNOWLEDGE_QA")
    print(f"[QA Agent] >>> Input  : {user_input!r}")
    print(f"[QA Agent] >>> History: {len(history)} messages")

    try:
        client = _get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            messages=_build_openai_messages(QA_SYSTEM_PROMPT, history, user_input),
        )
        reply = response.choices[0].message.content

        print(f"[QA Agent] >>> Reply  : {reply[:120]}{'...' if len(reply) > 120 else ''}")

        return {
            "messages": [HumanMessage(content=user_input), AIMessage(content=reply)],
            "final_output": reply,
            "error": None,
        }

    except Exception as e:
        print(f"[QA Agent] >>> ERROR  : {e}")
        return {
            "final_output": "Xin lỗi, có lỗi xảy ra khi xử lý câu hỏi của bạn. Vui lòng thử lại.",
            "error": f"Lỗi QA Agent: {e}",
        }
