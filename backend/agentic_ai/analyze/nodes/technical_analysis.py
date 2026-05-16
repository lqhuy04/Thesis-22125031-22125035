from agentic_ai.analyze.state import AgentState
from agentic_ai.service import database_service
 
ALL_TECHNICAL_INDICATORS = [
    "sma_20", "sma_50", "rsi_14", "macd", "macd_signal",
    "macd_histogram", "bb_upper", "bb_middle", "bb_lower",
    "kdj_k", "kdj_d", "kdj_j"
]

def technical_analysis_agent(state: AgentState) -> AgentState:
    myTask = state.get("plan", {}).get("technical_analysis_agent", {})
    symbol = state.get("symbol", "")
    interval = myTask.get("interval", "1d")
    from_date = myTask.get("from_date", "")
    to_date = myTask.get("to_date", "")

    print("""[Technical Analysis Agent] Đang xử lý mã: {symbol} với interval {interval} từ ngày {from_date} đến ngày {to_date}""" )

    result = database_service.get_technical_analysis(
        symbol=symbol,
        interval=interval,
        from_date=from_date,
        to_date=to_date,
        indicators=ALL_TECHNICAL_INDICATORS,  # Lấy hết
    )

    print("[Technical Analysis Agent] Kết quả:", result)

    return {
        "agent_results": {
            "technical_analysis_agent": result,
        },
    }