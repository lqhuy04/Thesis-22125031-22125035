from state import AgentState
 
 
def article_agent(state: AgentState) -> AgentState:
    """
    Article Agent — xử lý task_a.
    TODO: Thêm logic / tool / LLM call vào đây.
    """
    print("[Article Agent] Đang xử lý...")
 
    # TODO: Thêm logic thực sự, ví dụ:
    # result = some_tool.run(state["user_input"])
 
    result = "Kết quả giả từ Article Agent"
 
    return {
        "agent_results": {
            "article_agent": "Kết quả giả từ Article Agent",
        },
    }