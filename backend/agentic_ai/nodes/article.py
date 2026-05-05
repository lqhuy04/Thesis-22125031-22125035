from agentic_ai.state import AgentState
from agentic_ai.service import database_service
 
 
def article_agent(state: AgentState) -> AgentState:
    """
    Article Agent — xử lý task_a.
    TODO: Thêm logic / tool / LLM call vào đây.
    """
    
    myTask = state.get("plan", {}).get("article_agent", {})

    symbol = state.get("symbol", "")
    market_index = state.get("market_index","")
    category = state.get("category","")

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