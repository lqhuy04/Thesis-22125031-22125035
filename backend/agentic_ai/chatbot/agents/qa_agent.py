"""
agentic_ai/chatbot/agents/qa_agent.py — QA Agent

Xử lý hai loại intent:
  - KNOWLEDGE_QA  : Giải thích khái niệm chứng khoán/tài chính, không cần DB.
  - MARKET_QUERY  : Tạm thời xử lý ở đây (Phase 2 sẽ chuyển sang market_agent
                    có tool calls thực sự). Hiện tại thông báo rõ là chưa có
                    dữ liệu real-time và đưa ra phân tích định tính.
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
- Trả lời bằng tiếng Việt, rõ ràng, có cấu trúc nếu nội dung phức tạp.
- Dùng ví dụ thực tế khi giải thích khái niệm để dễ hiểu hơn.
- Không bịa đặt số liệu hoặc thông tin về cổ phiếu cụ thể.
- Nếu câu hỏi yêu cầu dữ liệu thực tế (giá cổ phiếu, chỉ số hôm nay...) mà bạn không có,
  hãy thành thật nói rõ và gợi ý cách tra cứu hoặc phân tích định tính.
""".strip()

MARKET_QUERY_NOTE = """

Lưu ý thêm: Người dùng đang hỏi về dữ liệu thị trường cụ thể.
Chức năng truy vấn dữ liệu thời gian thực đang được phát triển.
Hãy:
1. Thừa nhận rõ ràng rằng bạn chưa có dữ liệu real-time cho câu hỏi này.
2. Cung cấp phân tích định tính, kiến thức tổng quát liên quan nếu có thể.
3. Gợi ý người dùng tra cứu dữ liệu thực tế trên các nguồn uy tín (VPS, SSI, Fireant...).
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
    intent = state.get("intent", "KNOWLEDGE_QA")
    history: list[BaseMessage] = state.get("messages", [])

    print(f"[QA Agent] >>> Intent : {intent}")
    print(f"[QA Agent] >>> Input  : {user_input!r}")
    print(f"[QA Agent] >>> History: {len(history)} messages")

    system_prompt = QA_SYSTEM_PROMPT
    if intent == "MARKET_QUERY":
        system_prompt = QA_SYSTEM_PROMPT + "\n\n" + MARKET_QUERY_NOTE
        print(f"[QA Agent] >>> Mode   : MARKET_QUERY (no real-time data, qualitative only)")
    else:
        print(f"[QA Agent] >>> Mode   : KNOWLEDGE_QA")

    try:
        client = _get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            messages=_build_openai_messages(system_prompt, history, user_input),
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
