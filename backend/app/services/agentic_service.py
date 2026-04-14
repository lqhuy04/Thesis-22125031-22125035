"""
services/agentic_service.py
Cầu nối duy nhất giữa FastAPI và agentic_ai.
"""

from agentic_ai.graph import build_graph
from app.models.agentic_schemas import InvestmentRecommendation

_graph = build_graph()


def run_stock_analysis(symbol: str, risk_appetite: dict) -> InvestmentRecommendation:
    """
    Chạy multi-agent pipeline, trả về InvestmentRecommendation (Pydantic object).
    """
    initial_state = {
        "user_input": (
            f"Tóm tắt tình hình và gợi ý thời điểm đầu tư của mã cổ phiếu {symbol} "
            f"dựa vào khẩu vị rủi ro của nhà đầu tư."
        ),
        "risk_appetite": risk_appetite,
        "symbol": symbol,
        "plan": {},
        "agent_results": {},
        "final_output": "",
        "error": None,
    }

    result = _graph.invoke(initial_state)

    if result.get("error"):
        raise RuntimeError(result["error"])

    # final_output là InvestmentRecommendation object từ aggregator
    return result["final_output"]