"""
app/services/agentic_service.py
"""

import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_core.messages import AIMessage, HumanMessage

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
    data_selection: dict | None = None,
) -> dict:
    # Chỉ chế độ manual mới tôn trọng lựa chọn dữ liệu của người dùng.
    # Chế độ auto luôn dùng toàn bộ dữ liệu ({} → get_selection mặc định bật tất cả).
    effective_selection = data_selection if mode == "manual" else {}

    initial_state = {
        "mode": mode,

        "user_input": (
            f"Tóm tắt tình hình và gợi ý thời điểm đầu tư của mã cổ phiếu {symbol} "
            f"dựa vào khẩu vị rủi ro của nhà đầu tư."
        ),
        "risk_appetite": risk_appetite,

        "symbol": symbol,

        "data_selection": effective_selection or {},

        "plan": {},
        "agent_results": {},

        "final_output": "",
        "error": None,
    }

    result = _graph.invoke(initial_state)

    if result.get("error"):
        raise RuntimeError(result["error"])

    return result["final_output"]


# ─── Admin API mode (single symbol or full index basket) ──────────────────────

SUPPORTED_UNIVERSES = ("VN30", "VN100")

# Bounded concurrency: each symbol runs a full LLM pipeline. Too many parallel
# runs would hammer the LLM provider; a small pool keeps batch runs reasonable.
_ADMIN_BATCH_WORKERS = 4


def run_admin_analysis(
    mode: str,
    risk_appetite: dict,
    data_selection: dict | None = None,
    symbol: str | None = None,
    universe: str | None = None,
) -> dict:
    """
    Admin variant of run_stock_analysis. When `universe` is VN30/VN100 the index
    members are resolved from Supabase and analyzed with bounded concurrency.
    Otherwise a single `symbol` is analyzed.

    Returns a uniform shape:
        {"universe": str, "count": int, "results": [{"symbol", "status", ...}]}
    """
    uni = (universe or "").strip().upper()

    if uni in SUPPORTED_UNIVERSES:
        from app.utils.market_index import get_index_symbols

        symbols = get_index_symbols(uni)
        if not symbols:
            raise ValueError(f"Không tìm thấy mã cổ phiếu nào cho rổ {uni}.")

        results: list[dict] = []

        def _one(sym: str) -> dict:
            try:
                rec = run_stock_analysis(
                    symbol=sym,
                    risk_appetite=risk_appetite,
                    mode=mode,
                    data_selection=data_selection,
                )
                return {"symbol": sym, "status": "ok", "recommendation": rec}
            except Exception as e:  # noqa: BLE001 — báo lỗi từng mã, không làm hỏng cả rổ
                return {"symbol": sym, "status": "error", "error": str(e)}

        with ThreadPoolExecutor(max_workers=_ADMIN_BATCH_WORKERS) as pool:
            futures = {pool.submit(_one, s): s for s in symbols}
            for fut in as_completed(futures):
                results.append(fut.result())

        results.sort(key=lambda r: r["symbol"])
        return {"universe": uni, "count": len(results), "results": results}

    # Single-symbol path (behaves like /analyze)
    if not symbol or not symbol.strip():
        raise ValueError("Cần cung cấp 'symbol' khi không chọn rổ VN30/VN100.")

    rec = run_stock_analysis(
        symbol=symbol.strip().upper(),
        risk_appetite=risk_appetite,
        mode=mode,
        data_selection=data_selection,
    )
    return {
        "universe": "single",
        "count": 1,
        "results": [{"symbol": symbol.strip().upper(), "status": "ok", "recommendation": rec}],
    }


# ─── Chatbot mode ─────────────────────────────────────────────────────────────

def run_chat(session_id: str, message: str, user_id: str) -> str:
    """Đối đáp thông thường: gửi message vào graph 1 agent, nhận lại reply.

    Lịch sử hội thoại được giữ qua PostgresSaver theo thread_id = session_id.
    Map session ↔ user được lưu ở bảng chat_sessions để liệt kê/đọc lại sau này.
    """
    # Chuẩn hóa Unicode (NFC) NGAY tại cửa ngõ: tiếng Việt có thể được gõ ở nhiều
    # dạng tổ hợp dấu (NFC/NFD) khiến LLM tokenize khác nhau → cùng câu hỏi ra kết
    # quả khác nhau. Chuẩn hóa một lần ở đây để MỌI agent (intent_classifier, qa,
    # chat, market) đều nhận chuỗi nhất quán.
    message = unicodedata.normalize("NFC", message).strip() if message else message

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


def seed_chat_session(
    session_id: str,
    user_message: str,
    assistant_message: str,
    user_id: str,
) -> None:
    """Nạp sẵn 1 lượt Q&A vào một session chat mới (từ màn phân tích AI).

    Ghi thẳng cặp (HumanMessage, AIMessage) vào checkpoint của thread qua
    `update_state` — không chạy graph, không gọi LLM. Nhờ đó session có memory
    thật ngay từ đầu để các câu hỏi tiếp theo giữ đúng ngữ cảnh phân tích.
    """
    user_message = (
        unicodedata.normalize("NFC", user_message).strip() if user_message else user_message
    )
    assistant_message = (
        unicodedata.normalize("NFC", assistant_message).strip()
        if assistant_message
        else assistant_message
    )

    owner = ChatSessionService.get_owner(session_id)
    if owner is None:
        ChatSessionService.register_session(session_id, user_id, user_message)
    elif owner != user_id:
        raise PermissionError("Session không thuộc về người dùng này.")

    # Ghi cặp message vào lịch sử (add_messages reducer sẽ nối vào state)
    _chatbot_graph.update_state(
        config={"configurable": {"thread_id": session_id}},
        values={
            "messages": [
                HumanMessage(content=user_message),
                AIMessage(content=assistant_message),
            ]
        },
    )

    ChatSessionService.touch(session_id)


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