"""
app/services/agentic_service.py
"""

from agentic_ai.chatbot.chatbot_graph import build_chatbot_graph
from agentic_ai.analyze.analyze_graph import build_analyze_graph

# Graph được khởi tạo một lần duy nhất khi server start
# tránh tạo lại sqlite connection mỗi request
_chatbot_graph = build_chatbot_graph()

_analyze_graph = build_analyze_graph()


# ─── API mode ────────────────────────────────────────────────────────────────

def run_stock_analysis(
    symbol: str,
    risk_appetite: dict,
    user_input: str | None = None,
) -> dict:
    initial_state = {
        "mode": "auto",

        "user_input": user_input or (
            f"Tóm tắt tình hình và gợi ý thời điểm đầu tư của mã cổ phiếu {symbol} "
            f"dựa vào khẩu vị rủi ro của nhà đầu tư."
        ),
        "risk_appetite": risk_appetite,

        "symbol": symbol,
        "market_index": None,
        "category": None,

        "plan": {},
        "agent_results": {},

        "final_output": "",
        "error": None,
    }

    result = _analyze_graph.invoke(initial_state)

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
        "mode": "chat",
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
    result = _chatbot_graph.invoke(initial_state, config={"configurable": {"thread_id": session_id}})

    if result.get("error"):
        raise RuntimeError(result["error"])

    return result["final_output"]


def delete_session(session_id: str) -> None:
    """Xóa toàn bộ checkpoint của một session khỏi DB."""
    conn = _chatbot_graph.checkpointer.conn
    conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (session_id,))
    conn.execute("DELETE FROM checkpoint_blobs WHERE thread_id = ?", (session_id,))
    conn.execute("DELETE FROM checkpoint_writes WHERE thread_id = ?", (session_id,))
    conn.commit()

    # Xóa cache risk_appetite nếu có
    _session_risk_appetite.pop(session_id, None)

    print(f"[Session] Đã xóa session: {session_id}")