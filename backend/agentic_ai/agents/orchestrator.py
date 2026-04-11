"""
orchestrator.py — Orchestrator Agent
Nhận input từ người dùng, phân tích, lên kế hoạch và quyết định
sub-agent nào sẽ được gọi.
"""

from state import AgentState


def orchestrator_agent(state: AgentState) -> AgentState:
    """
    Node chính: phân tích yêu cầu và tạo plan.
    Hiện tại chỉ là skeleton — thêm logic LLM vào đây sau.
    """
    print(f"[Orchestrator] Nhận input: {state['user_input']}")

    # TODO: Gọi LLM để phân tích input và quyết định sub-task
    # Ví dụ:
    # response = llm.invoke(f"Phân tích yêu cầu sau và liệt kê các bước: {state['user_input']}")
    # plan = parse_plan(response)

    # Placeholder plan
    plan = ["task_a", "task_b", "task_c"]  # Giả sử Orchestrator quyết định cần 3 task này

    print(f"[Orchestrator] Kế hoạch: {plan}")
    return {"plan": plan}