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
        "session_id": "",   # api mode không dùng memory
        "intent": {},
        "plan": {},
        "agent_results": {},
        "messages": [],
        "final_output": "",
        "error": None,
    }

    result = _graph.invoke(initial_state, config={"configurable": {"thread_id": f"api_{symbol}"}})

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
        "intent": {},
        "plan": {},
        "agent_results": {},
        "messages": [],
        "final_output": "",
        "error": None,
    }

    # thread_id = session_id → LangGraph tự load/save history qua SqliteSaver
    config = {"configurable": {"thread_id": session_id}}
    result = _graph.invoke(initial_state, config=config)

    intent = result.get("intent", {})
    intent_type = intent.get("intent_type", "out_of_scope")

    # Xác định reply và nguồn gốc
    if intent_type != "stock_analysis":
        # Kết thúc sớm tại intent_classifier
        reply = intent.get("instant_reply", "Xin lỗi, mình không hiểu yêu cầu này.")
        is_instant = True
    else:
        reply = result.get("final_output", "")
        is_instant = False

    return {
        "reply": reply,
        "intent_type": intent_type,
        "instant_reply": is_instant,
    }