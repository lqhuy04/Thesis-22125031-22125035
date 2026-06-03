"""
agentic_ai/chatbot/db.py — Connection pool Postgres dùng chung cho chatbot.

Dùng bởi:
  - PostgresSaver (lịch sử hội thoại) trong graph.py
  - ChatSessionService (bảng chat_sessions: map user ↔ session)

Cả hai cùng nằm trong DB Supabase, quản lý chung một pool cho gọn.
"""

from psycopg_pool import ConnectionPool

from app.config import settings

# open=False: chưa kết nối lúc import, chỉ mở khi get_pool() được gọi lần đầu.
# autocommit + prepare_threshold=0 để tương thích Supabase pooler (pgbouncer).
_pool = ConnectionPool(
    conninfo=settings.SUPABASE_DB_URL,
    max_size=10,
    open=False,
    kwargs={"autocommit": True, "prepare_threshold": 0},
)
_opened = False


def get_pool() -> ConnectionPool:
    """Trả về pool đã mở (mở lần đầu, idempotent)."""
    global _opened
    if not _opened:
        _pool.open()
        _opened = True
    return _pool


def close_pool() -> None:
    """Đóng pool khi app tắt (gọi ở shutdown handler)."""
    global _opened
    if _opened:
        _pool.close()
        _opened = False
