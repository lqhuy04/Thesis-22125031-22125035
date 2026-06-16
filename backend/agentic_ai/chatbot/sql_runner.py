"""
agentic_ai/chatbot/sql_runner.py — Lớp thực thi SQL read-only an toàn cho chatbot.

market_agent để LLM sinh câu SELECT, nhưng SQL đó KHÔNG bao giờ được chạy thẳng.
Mọi câu lệnh phải đi qua `run_select()`, nơi:
  1. sanitize_sql()  — chỉ cho phép một câu SELECT/WITH, cấm DML/DDL, cấm multi-statement,
                       cấm comment, và mọi bảng trong FROM/JOIN phải nằm trong ALLOWED_TABLES.
  2. execute        — chạy trong transaction READ ONLY + statement_timeout ngắn,
                       trả tối đa MAX_ROWS dòng.

Dùng chung pool với PostgresSaver (xem db.py). Schema được introspect động từ
information_schema để prompt của LLM luôn khớp tên cột thật (tránh hallucination).
"""

import re

from psycopg.rows import dict_row

from agentic_ai.chatbot.db import get_pool

# ─── Cấu hình guardrail ───────────────────────────────────────────────────────

# Các bảng dữ liệu thị trường được phép truy vấn. Cố tình LOẠI các bảng nhạy cảm:
# User, RiskAppetite, Portfolio, Favorite, chat_sessions, và các bảng checkpoint
# của LangGraph.
ALLOWED_TABLES: set[str] = {
    "Stock",
    "Current_Stock_Price",
    "Current_Market_Index",
    "Stock_Price_1m",
    "Stock_Price_15m",
    "Stock_Price_1h",
    "Stock_Price_1d",
    "FA_Summary",
    "FA_Indicator",
    "FA_BalanceSheet",
    "FA_CashFlow",
    "FA_IncomeStatement",
    "Article",
    "Article_Stock",
    "Category_Stock",
    "BI_Profile",
    "BI_Leader",
    "BI_Subsidiary",
}

MAX_ROWS = 100            # Số dòng tối đa trả về (chống ngốn token + lạm dụng)
STATEMENT_TIMEOUT_MS = 4000  # Hủy query chạy quá lâu

# Từ khóa bị cấm tuyệt đối (ghi/thay đổi dữ liệu hoặc lệnh nguy hiểm).
_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|"
    r"comment|copy|merge|call|do|vacuum|analyze|reindex|set|reset|"
    r"into|returning)\b",
    re.IGNORECASE,
)

# Tìm bảng đứng sau FROM / JOIN. Bắt cả dạng có/không dấu nháy kép.
_TABLE_REF = re.compile(
    r'\b(?:from|join)\s+"?([A-Za-z_][A-Za-z0-9_]*)"?',
    re.IGNORECASE,
)


class UnsafeSQLError(ValueError):
    """Raise khi câu SQL không vượt qua được kiểm tra an toàn."""


def sanitize_sql(sql: str) -> str:
    """Kiểm tra & chuẩn hóa câu SQL. Trả về SQL sạch hoặc raise UnsafeSQLError."""
    if not sql or not sql.strip():
        raise UnsafeSQLError("Câu SQL rỗng.")

    cleaned = sql.strip().rstrip(";").strip()

    # 1. Cấm comment (né bypass kiểu `-- ` hoặc `/* */`)
    if "--" in cleaned or "/*" in cleaned or "*/" in cleaned:
        raise UnsafeSQLError("SQL chứa comment — không cho phép.")

    # 2. Cấm multi-statement (sau khi đã bỏ dấu ; ở cuối mà vẫn còn ;)
    if ";" in cleaned:
        raise UnsafeSQLError("Chỉ cho phép một câu lệnh duy nhất.")

    # 3. Phải là câu đọc: bắt đầu bằng SELECT hoặc WITH (CTE)
    lowered = cleaned.lower()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise UnsafeSQLError("Chỉ cho phép câu SELECT (hoặc WITH ... SELECT).")

    # 4. Cấm từ khóa ghi/DDL/lệnh nguy hiểm
    forbidden = _FORBIDDEN_KEYWORDS.search(cleaned)
    if forbidden:
        raise UnsafeSQLError(f"SQL chứa từ khóa bị cấm: '{forbidden.group(1)}'.")

    # 5. Mọi bảng trong FROM/JOIN phải nằm trong allowlist
    refs = _TABLE_REF.findall(cleaned)
    if not refs:
        raise UnsafeSQLError("Không xác định được bảng nguồn trong câu SQL.")
    for table in refs:
        if table not in ALLOWED_TABLES:
            raise UnsafeSQLError(
                f"Bảng '{table}' không được phép truy vấn."
            )

    return cleaned


def run_select(sql: str) -> list[dict]:
    """Sanitize rồi chạy câu SELECT trong transaction read-only. Trả list[dict].

    Raise UnsafeSQLError nếu SQL không an toàn; raise các lỗi psycopg nếu SQL sai
    cú pháp/sai cột (market_agent bắt để retry).
    """
    safe_sql = sanitize_sql(sql)

    pool = get_pool()
    with pool.connection() as conn:
        # Mở transaction tường minh (pool đang autocommit) để SET LOCAL có hiệu lực.
        with conn.transaction():
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SET TRANSACTION READ ONLY")
                cur.execute(f"SET LOCAL statement_timeout = {STATEMENT_TIMEOUT_MS}")
                cur.execute(safe_sql)
                rows = cur.fetchmany(MAX_ROWS)
    return rows


# ─── Introspect schema cho prompt ──────────────────────────────────────────────

_schema_cache: str | None = None


def get_schema_ddl() -> str:
    """Trả về mô tả schema (dạng DDL rút gọn) của các bảng trong ALLOWED_TABLES.

    Introspect từ information_schema một lần rồi cache, để prompt của LLM luôn khớp
    tên cột thật trong DB.
    """
    global _schema_cache
    if _schema_cache is not None:
        return _schema_cache

    table_list = sorted(ALLOWED_TABLES)
    pool = get_pool()
    cols_by_table: dict[str, list[str]] = {t: [] for t in table_list}

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = ANY(%s)
                ORDER BY table_name, ordinal_position
                """,
                (table_list,),
            )
            for row in cur.fetchall():
                t = row["table_name"]
                cols_by_table.setdefault(t, []).append(
                    f"{row['column_name']} {row['data_type']}"
                )

    lines: list[str] = []
    for table in table_list:
        cols = cols_by_table.get(table) or []
        if not cols:
            continue  # Bảng chưa tồn tại trong DB — bỏ qua khỏi prompt
        cols_str = ",\n  ".join(cols)
        lines.append(f'TABLE "{table}" (\n  {cols_str}\n);')

    _schema_cache = "\n\n".join(lines)
    return _schema_cache
