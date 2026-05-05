from agentic_ai.service import database_service
from agentic_ai.chatbot.state import IntentJob
 
 
def fundamental_analysis_agent(state: IntentJob) -> dict:
    myTask = state.get("plan", {}).get("fundamental_analysis_agent", {})
    symbol = state.get("symbol", "")
    print("[Fundamental Analysis Agent] Đang xử lý task:", myTask)
 
    result = database_service.get_fundamental_analysis(
        symbol=symbol,
        indicators=myTask.get("indicators", []),
    )
 
    return {
        "agent_results": {
            "fundamental_analysis_agent": result,
        },
    }