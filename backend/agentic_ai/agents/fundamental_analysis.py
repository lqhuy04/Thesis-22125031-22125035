from agentic_ai.state import AgentState
from agentic_ai.service import database_service
 
 
def fundamental_analysis_agent(state: AgentState) -> AgentState:
    """
    Fundamental Analysis Agent — xử lý task_b.
    TODO: Thêm logic / tool / LLM call vào đây.
    """
    myTask = state.get("plan", {}).get("fundamental_analysis_agent", {})
    print("[Fundamental Analysis Agent] Đang xử lý task:", myTask)
 
    result = database_service.get_fundamental_analysis(
        symbol=myTask.get("symbol", ""),
        indicators=myTask.get("indicators", []),
    )
 
    return {
        "agent_results": {
            "fundamental_analysis_agent": result,
        },
    }