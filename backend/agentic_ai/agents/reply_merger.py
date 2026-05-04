"""
reply_merger.py — Reply Merger Agent

Gộp tất cả kết quả từ các job song song thành một reply duy nhất.
Sắp xếp theo order để giữ đúng thứ tự user hỏi.
"""

import json
from langchain_core.messages import AIMessage

from agentic_ai.service.openai_service import _get_openai_client
from agentic_ai.chatbot.state import AgentState


MERGER_SYSTEM_PROMPT = """
Bạn là trợ lý phân tích chứng khoán Việt Nam.

Nhiệm vụ: Nhận danh sách các câu trả lời riêng lẻ cho từng ý trong câu hỏi của user,
gộp lại thành một phản hồi duy nhất mạch lạc, tự nhiên.

Quy tắc:
- Giữ đúng nội dung từng câu trả lời, không bỏ sót ý nào
- Kết nối các phần mượt mà, không liệt kê cứng nhắc
- Nếu chỉ có 1 câu trả lời → trả nguyên, không thêm gì
- Trả lời bằng tiếng Việt, thân thiện
- Không thêm lời chào hay kết thúc sáo rỗng
"""


def reply_merger_agent(state: AgentState) -> dict:
    print("[Reply Merger] Gộp kết quả...")

    sub_results = state.get("sub_results", [])
    mode = state.get("mode", "api")

    # Sắp xếp theo order để đúng thứ tự user hỏi
    sub_results_sorted = sorted(sub_results, key=lambda x: x.get("order", 0))

    print(f"[Reply Merger] Gộp {len(sub_results_sorted)} kết quả")

    # Nếu chỉ có 1 kết quả → trả thẳng, không cần gọi LLM merge
    if len(sub_results_sorted) == 1:
        single = sub_results_sorted[0]
        reply = single.get("reply") or json.dumps(
            single.get("final_output", {}), ensure_ascii=False
        )

        return {
            "final_output": reply if mode == "chatbot" else single.get("final_output", reply),
            "messages": [AIMessage(content=reply if isinstance(reply, str) else str(reply))],
        }

    # Nhiều kết quả → gọi LLM gộp lại (chỉ áp dụng chatbot mode)
    # API mode: trả list structured output
    if mode == "api":
        return {
            "final_output": sub_results_sorted,
        }

    # Chatbot mode: gộp thành plain text mượt mà
    client = _get_openai_client()

    parts_text = "\n\n".join([
        f"[Câu hỏi {i+1}]: {r['sub_query']}\n[Trả lời {i+1}]: {r.get('reply', '')}"
        for i, r in enumerate(sub_results_sorted)
    ])

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": MERGER_SYSTEM_PROMPT},
            {"role": "user", "content": parts_text},
        ],
    )

    merged_reply = response.choices[0].message.content
    print(f"[Reply Merger] Merged reply: {merged_reply[:100]}...")

    return {
        "final_output": merged_reply,
        "messages": [AIMessage(content=merged_reply)],
    }