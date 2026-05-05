from agentic_ai.service import database_service
from agentic_ai.chatbot.state import IntentJob
 
 
def article_agent(state: IntentJob) -> dict:
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