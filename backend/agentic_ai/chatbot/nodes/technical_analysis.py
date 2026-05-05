from agentic_ai.service import database_service
from agentic_ai.chatbot.state import IntentJob
 
def technical_analysis_agent(state: IntentJob) -> dict:
    myTask = state.get("plan", {}).get("technical_analysis_agent", {})
    symbol = state.get("symbol", "")
    print("[Technical Analysis Agent] Đang xử lý task:", myTask)
 
    result = database_service.get_technical_analysis(
        symbol=symbol,
        interval=myTask.get("interval", ""),
        from_date=myTask.get("from_date", ""),  
        to_date=myTask.get("to_date", ""),
        indicators=myTask.get("indicators", []),
    ) 
    
    return {
        "agent_results": {
            "technical_analysis_agent": result,
        },
    }