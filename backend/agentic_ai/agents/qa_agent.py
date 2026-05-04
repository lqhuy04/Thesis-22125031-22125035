"""
qa_agent.py — QA Agent

Xử lý các intent không cần pipeline DB:
    - general_question: trả lời kiến thức chứng khoán
    - clarification:    hỏi lại user
    - out_of_scope:     báo ngoài phạm vi
"""

from agentic_ai.service.openai_service import _get_openai_client
from agentic_ai.state import AgentState


QA_SYSTEM_PROMPT = """
Bạn là trợ lý phân tích chứng khoán Việt Nam, đang trò chuyện trực tiếp với nhà đầu tư.

Nhiệm vụ: Trả lời câu hỏi được giao dựa theo loại intent.

Quy tắc:
- general_question: trả lời kiến thức chứng khoán / tài chính ngắn gọn, dễ hiểu
- clarification: hỏi lại user để làm rõ, thân thiện, không hỏi nhiều hơn 1 câu
- out_of_scope: giải thích nhẹ nhàng rằng câu hỏi ngoài phạm vi hệ thống

Trả lời bằng tiếng Việt. Không bịa số liệu.
"""


def qa_agent(job: AgentState) -> dict:
    """
    Nhận một AgentState, gọi LLM trả lời thẳng không qua DB.
    Trả về dict có order và reply để Reply Merger gộp.
    """
    intent_type = job["intent"]
    user_input = job["user_input"]
    order = job["order"]

    print(f"[QA Agent] Xử lý intent [{order}] {intent_type}: {user_input}")

    client = _get_openai_client()

    user_message = (
        f"Loại câu hỏi: {intent_type}\n"
        f"Câu hỏi: {user_input}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": QA_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    reply = response.choices[0].message.content
    print(f"[QA Agent] Reply [{order}]: {reply[:80]}...")

    return {
        "sub_results": [{
            "order": order,
            "intent": intent_type,
            "user_input": user_input,
            "reply": reply,
        }]
    }