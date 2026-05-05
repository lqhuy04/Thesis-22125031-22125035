"""
app/services/agentic_service.py
"""

from agentic_ai.chatbot.graph import build_chatbot_graph
from agentic_ai.analyze.graph import build_graph
from typing import Any

# Graph được khởi tạo một lần duy nhất khi server start
# tránh tạo lại sqlite connection mỗi request
# _chatbot_graph = build_chatbot_graph()

_graph = build_graph()
_chatbot_graph = build_chatbot_graph()


# ─── API mode ────────────────────────────────────────────────────────────────

def run_stock_analysis(
    symbol: str,
    risk_appetite: dict,
    mode: str,
    plan: Any | None
) -> dict:
    initial_state = {
        "mode": mode,
        
        "user_input": (
            f"Tóm tắt tình hình và gợi ý thời điểm đầu tư của mã cổ phiếu {symbol} "
            f"dựa vào khẩu vị rủi ro của nhà đầu tư."
        ),
        "risk_appetite": risk_appetite,

        "symbol": symbol,

        "plan": plan or {},
        "agent_results": {},

        "final_output": "",
        "error": None,
    }

    result = _graph.invoke(initial_state)

    if result.get("error"):
        raise RuntimeError(result["error"])

    return result["final_output"]


# ─── Chatbot mode ─────────────────────────────────────────────────────────────

# Cache risk_appetite theo session_id
# Để client chỉ cần gửi risk_appetite ở turn đầu, các turn sau bỏ qua

def run_chat(
    session_id: str,
    message: str,
    risk_appetite: dict,
) -> dict:
    initial_state = {
        "user_input": message,
        "risk_appetite": risk_appetite,
        
        "sub_results": [],
        
        "intents": [],
        "messages": [],

        "final_output": "",
        "error": None,
    }

    # thread_id = session_id → LangGraph tự load/save history qua SqliteSaver
    result = _chatbot_graph.invoke(initial_state, config={"configurable": {"thread_id": session_id}})

    if result.get("error"):
        raise RuntimeError(result["error"])

    return result["final_output"]