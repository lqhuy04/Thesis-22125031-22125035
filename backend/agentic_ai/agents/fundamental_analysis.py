from state import AgentState
 
 
def fundamental_analysis_agent(state: AgentState) -> AgentState:
    """
    Fundamental Analysis Agent — xử lý task_b.
    TODO: Thêm logic / tool / LLM call vào đây.
    """
    print("[Fundamental Analysis Agent] Đang xử lý...")
 
    # TODO: Thêm logic thực sự, ví dụ:
    # result = some_tool.run(state["user_input"])
 
    result = "Kết quả giả từ Fundamental Analysis Agent"
 
    return {
        "agent_results": {
            "fundamental_analysis_agent": "Kết quả giả từ Fundamental Analysis Agent",
        },
    }