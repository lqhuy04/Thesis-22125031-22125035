from agentic_ai.analyze.state import AgentState
from agentic_ai.service import database_service
 
ALL_FUNDAMENTAL_INDICATORS = [
    "pe_ratio", "pb_ratio", "ps_ratio",
    "roe", "roa", "net_margin", "gross_margin", "ebit_margin",
    "revenue_yoy", "profit_yoy",
    "debt_to_equity", "current_ratio", "quick_ratio", "interest_coverage",
    "asset_turnover", "days_inventory", "days_receivable", "days_payable",
    "eps", "p_cash_flow",
    "market_cap"
]

def fundamental_analysis_agent(state: AgentState) -> AgentState:
    symbol = state.get("symbol", "")
    print("[Fundamental Analysis Agent] Đang xử lý mã:", symbol)

    result = database_service.get_fundamental_analysis(
        symbol=symbol,
        indicators=ALL_FUNDAMENTAL_INDICATORS,  # Lấy hết
    )

    print("[Fundamental Analysis Agent] Kết quả:", result)

    return {
        "agent_results": {
            "fundamental_analysis_agent": result,
        },
    }