"""
app/services/chat_session_service.py

Quản lý map user ↔ session chat (bảng chat_sessions).
Lịch sử nội dung do LangGraph PostgresSaver lo (bảng checkpoints*);
bảng này chỉ lưu: session thuộc về ai, tiêu đề, thời gian.

Dùng chung connection pool psycopg với checkpointer (agentic_ai/chatbot/db.py).
"""

from typing import Any

from agentic_ai.chatbot.db import get_pool

TABLE_NAME = "chat_sessions"
TITLE_MAX_LEN = 60


def _make_title(message: str) -> str:
    """Sinh tiêu đề từ tin nhắn đầu tiên: cắt gọn ~60 ký tự."""
    text = (message or "").strip().replace("\n", " ")
    if len(text) > TITLE_MAX_LEN:
        return text[:TITLE_MAX_LEN].rstrip() + "…"
    return text or "Cuộc trò chuyện mới"


class ChatSessionService:

    @staticmethod
    def ensure_table() -> None:
        """Tạo bảng chat_sessions nếu chưa có (idempotent, gọi lúc khởi động)."""
        pool = get_pool()
        with pool.connection() as conn:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    session_id  TEXT PRIMARY KEY,
                    user_id     TEXT NOT NULL,
                    title       TEXT NOT NULL DEFAULT '',
                    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_user "
                f"ON {TABLE_NAME} (user_id, updated_at DESC);"
            )

    @staticmethod
    def get_owner(session_id: str) -> str | None:
        """Trả về user_id sở hữu session, hoặc None nếu session chưa tồn tại."""
        pool = get_pool()
        with pool.connection() as conn:
            row = conn.execute(
                f"SELECT user_id FROM {TABLE_NAME} WHERE session_id = %s",
                (session_id,),
            ).fetchone()
        return row[0] if row else None

    @staticmethod
    def register_session(session_id: str, user_id: str, message: str) -> None:
        """Tạo bản ghi session mới (gọi ở tin nhắn đầu của một session)."""
        pool = get_pool()
        with pool.connection() as conn:
            conn.execute(
                f"INSERT INTO {TABLE_NAME} (session_id, user_id, title) "
                f"VALUES (%s, %s, %s) ON CONFLICT (session_id) DO NOTHING",
                (session_id, user_id, _make_title(message)),
            )

    @staticmethod
    def touch(session_id: str) -> None:
        """Cập nhật updated_at sau mỗi turn để sắp xếp danh sách theo gần nhất."""
        pool = get_pool()
        with pool.connection() as conn:
            conn.execute(
                f"UPDATE {TABLE_NAME} SET updated_at = now() WHERE session_id = %s",
                (session_id,),
            )

    @staticmethod
    def list_by_user(user_id: str) -> list[dict[str, Any]]:
        """Danh sách session của user, mới nhất trước."""
        pool = get_pool()
        with pool.connection() as conn:
            rows = conn.execute(
                f"SELECT session_id, title, updated_at FROM {TABLE_NAME} "
                f"WHERE user_id = %s ORDER BY updated_at DESC",
                (user_id,),
            ).fetchall()
        return [
            {
                "session_id": r[0],
                "title": r[1],
                "updated_at": r[2].isoformat() if r[2] else None,
            }
            for r in rows
        ]

    @staticmethod
    def delete(session_id: str) -> None:
        """Xóa session + toàn bộ checkpoint (lịch sử) của thread tương ứng."""
        pool = get_pool()
        with pool.connection() as conn:
            # Xóa lịch sử hội thoại trong các bảng checkpoint của LangGraph
            for tbl in ("checkpoint_writes", "checkpoint_blobs", "checkpoints"):
                conn.execute(f"DELETE FROM {tbl} WHERE thread_id = %s", (session_id,))
            conn.execute(f"DELETE FROM {TABLE_NAME} WHERE session_id = %s", (session_id,))
