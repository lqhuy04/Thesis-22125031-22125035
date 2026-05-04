"""
app/services/agentic_service.py
"""

from agentic_ai.graph import build_graph

# Graph được khởi tạo một lần duy nhất khi server start
# tránh tạo lại sqlite connection mỗi request
_graph = build_graph()


# ─── API mode ────────────────────────────────────────────────────────────────

def run_stock_analysis(
    symbol: str,
    risk_appetite: dict,
    user_input: str | None = None,
) -> dict:
    initial_state = {
        "user_input": user_input or (
            f"Tóm tắt tình hình và gợi ý thời điểm đầu tư của mã cổ phiếu {symbol} "
            f"dựa vào khẩu vị rủi ro của nhà đầu tư."
        ),
        "risk_appetite": risk_appetite,
        "symbol": symbol,
        "mode": "api",
        "session_id": "",
        "intents": [],
        "plan": {},
        "agent_results": {},
        "sub_results": [],
        "messages": [],
        "final_output": "",
        "error": None,
    }

    result = _graph.invoke(initial_state, config={"configurable": {"thread_id": "api_static"}})

    if result.get("error"):
        raise RuntimeError(result["error"])

    return result["final_output"]


# ─── Chatbot mode ─────────────────────────────────────────────────────────────

# Cache risk_appetite theo session_id
# Để client chỉ cần gửi risk_appetite ở turn đầu, các turn sau bỏ qua
_session_risk_appetite: dict[str, dict] = {}

DEFAULT_RISK_APPETITE = {
    "capital_ratio": "Không xác định",
    "comfort_zone": "Không xác định",
    "expectation": "Không xác định",
    "experience": "Không xác định",
    "period": "Không xác định",
}


def run_chat(
    session_id: str,
    message: str,
    risk_appetite: dict | None = None,
) -> dict:
    # Lưu risk_appetite nếu turn đầu có gửi, các turn sau dùng lại từ cache
    if risk_appetite:
        _session_risk_appetite[session_id] = risk_appetite

    resolved_risk_appetite = _session_risk_appetite.get(session_id, DEFAULT_RISK_APPETITE)

    initial_state = {
        "user_input": message,
        "risk_appetite": resolved_risk_appetite,
        "symbol": "",
        "mode": "chatbot",
        "session_id": session_id,
        "intents": [],
        "plan": {},
        "agent_results": {},
        "sub_results": [],
        "messages": [],
        "final_output": "",
        "error": None,
    }

    # thread_id = session_id → LangGraph tự load/save history qua SqliteSaver
    result = _graph.invoke(initial_state, config={"configurable": {"thread_id": session_id}})
    
    print(result)

    if result.get("error"):
        raise RuntimeError(result["error"])

    return result["final_output"]