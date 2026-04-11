"""
aggregator.py — Aggregator Agent
Nhận input từ người dùng, phân tích, lên kế hoạch và quyết định
sub-agent nào sẽ được gọi.
"""

from state import AgentState


def aggregator_agent(state: AgentState) -> AgentState:
    """
    Node tổng hợp: gom kết quả từ các sub-agent và tạo output cuối.
    """
    print("[Aggregator] Tổng hợp kết quả...")

    results = state.get("agent_results", {})

    # TODO: Gọi LLM để tổng hợp các kết quả thành câu trả lời mạch lạc
    # Ví dụ:
    # summary = llm.invoke(f"Tổng hợp các kết quả sau: {results}")

    # Placeholder
    summary_parts = [f"- {name}: {result}" for name, result in results.items()]
    final_output = "Kết quả tổng hợp:\n" + "\n".join(summary_parts)

    print(f"[Aggregator] Output: {final_output}")
    return {"final_output": final_output}
