from agentic_ai.analyze.state import AgentState
from agentic_ai.service import database_service
 
 
def article_agent(state: AgentState) -> AgentState:
    myTask = state.get("plan", {}).get("article_agent", {})
    symbol = state.get("symbol", "")

    print("[Article Agent] Đang xử lý task:", myTask)
 
    result = database_service.get_articles(
        symbol=symbol,
        from_date=myTask.get("from_date", ""),
        to_date=myTask.get("to_date", ""),
    )
 
    return {
        "agent_results": {
            "article_agent": result,
        },
    }