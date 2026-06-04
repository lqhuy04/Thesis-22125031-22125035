"""
agentic_ai/chatbot/db.py — Connection pool Postgres dùng chung cho chatbot.

Dùng bởi:
  - PostgresSaver (lịch sử hội thoại) trong graph.py
  - ChatSessionService (bảng chat_sessions: map user ↔ session)

Cả hai cùng nằm trong DB Supabase, quản lý chung một pool cho gọn.
"""

import atexit

from psycopg_pool import ConnectionPool

from app.config import settings

# open=False: chưa kết nối lúc import, chỉ mở khi get_pool() được gọi lần đầu.
# autocommit + prepare_threshold=0 để tương thích Supabase pooler (pgbouncer).
_pool = ConnectionPool(
    conninfo=settings.SUPABASE_DB_URL,
    min_size=1,
    max_size=10,
    num_workers=1,
    open=False,
    kwargs={
        "autocommit": True,
        "prepare_threshold": 0,
        "connect_timeout": 10,
    },
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
    """Đóng pool khi app tắt (gọi ở shutdown handler).

    timeout=15: nới rộng thời gian chờ worker dừng (mặc định 5s) để tránh cảnh báo
    "couldn't stop thread ... within 5.0 seconds" khi connection Supabase đóng chậm.
    """
    global _opened
    if _opened:
        _pool.close(timeout=15.0)
        _opened = False


# Đóng pool tường minh lúc interpreter thoát. Cần thiết vì khi bấm Ctrl+C trên
# Windows (uvicorn reload), ASGI lifespan shutdown thường không chạy → nếu không
# có atexit, pool bị finalizer dọn với timeout 5s và in cảnh báo
# "couldn't stop thread ... within 5.0 seconds". atexit chạy khi interpreter còn
# khỏe nên close() dừng được worker/scheduler. Idempotent với close_pool ở lifespan.
atexit.register(close_pool)