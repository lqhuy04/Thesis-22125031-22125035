"""
app/services/agentic_service.py
"""

from typing import Any

from langchain_core.messages import AIMessage

from agentic_ai.chatbot.graph import build_chatbot_graph
from agentic_ai.analyze.graph import build_graph
from app.services.chat_session_service import ChatSessionService

# Graph được khởi tạo một lần duy nhất khi server start
# tránh tạo lại connection mỗi request
_graph = build_graph()
_chatbot_graph = build_chatbot_graph()

# Đảm bảo bảng chat_sessions tồn tại (idempotent)
ChatSessionService.ensure_table()


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

def run_chat(session_id: str, message: str, user_id: str) -> str:
    """Đối đáp thông thường: gửi message vào graph 1 agent, nhận lại reply.

    Lịch sử hội thoại được giữ qua PostgresSaver theo thread_id = session_id.
    Map session ↔ user được lưu ở bảng chat_sessions để liệt kê/đọc lại sau này.
    """
    # Kiểm tra quyền sở hữu session
    owner = ChatSessionService.get_owner(session_id)
    if owner is None:
        # Tin nhắn đầu tiên của session → tạo bản ghi, lấy tiêu đề từ message
        ChatSessionService.register_session(session_id, user_id, message)
    elif owner != user_id:
        raise PermissionError("Session không thuộc về người dùng này.")

    initial_state = {
        "user_input": message,
        "final_output": "",
        "error": None,
    }

    # thread_id = session_id → LangGraph tự load/save history qua PostgresSaver
    result = _chatbot_graph.invoke(
        initial_state, config={"configurable": {"thread_id": session_id}}
    )

    if result.get("error"):
        raise RuntimeError(result["error"])

    ChatSessionService.touch(session_id)
    return result["final_output"]


def list_chat_sessions(user_id: str) -> list[dict]:
    """Danh sách các cuộc trò chuyện của user (mới nhất trước)."""
    return ChatSessionService.list_by_user(user_id)


def get_chat_history(session_id: str, user_id: str) -> list[dict]:
    """Đọc lại toàn bộ tin nhắn của một session (kiểm tra quyền sở hữu)."""
    owner = ChatSessionService.get_owner(session_id)
    if owner is None:
        raise ValueError("Không tìm thấy cuộc trò chuyện.")
    if owner != user_id:
        raise PermissionError("Session không thuộc về người dùng này.")

    snapshot = _chatbot_graph.get_state(
        config={"configurable": {"thread_id": session_id}}
    )
    messages = (snapshot.values or {}).get("messages", []) if snapshot else []

    return [
        {
            "role": "assistant" if isinstance(msg, AIMessage) else "user",
            "content": msg.content,
        }
        for msg in messages
    ]


def delete_chat_session(session_id: str, user_id: str) -> None:
    """Xóa một cuộc trò chuyện và toàn bộ lịch sử của nó (kiểm tra quyền sở hữu)."""
    owner = ChatSessionService.get_owner(session_id)
    if owner is None:
        raise ValueError("Không tìm thấy cuộc trò chuyện.")
    if owner != user_id:
        raise PermissionError("Session không thuộc về người dùng này.")

    ChatSessionService.delete(session_id)