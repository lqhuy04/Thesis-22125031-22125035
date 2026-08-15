"""
agentic_ai/chatbot/sql_runner.py — Lớp thực thi SQL read-only an toàn cho chatbot.

market_agent để LLM sinh câu SELECT, nhưng SQL đó KHÔNG bao giờ được chạy thẳng.
Mọi câu lệnh phải đi qua `run_select()`, nơi:
  1. sanitize_sql()  — chỉ cho phép một câu SELECT/WITH, cấm DML/DDL, cấm multi-statement,
                       cấm comment, và mọi bảng trong FROM/JOIN phải nằm trong ALLOWED_TABLES.
  2. execute        — chạy trong transaction READ ONLY + statement_timeout ngắn,
                       trả tối đa 100 dòng thông thường hoặc 200 nến khi tính chỉ báo kỹ thuật.

Dùng chung pool với PostgresSaver (xem db.py). Schema được introspect động từ
information_schema để prompt của LLM luôn khớp tên cột thật (tránh hallucination).
"""

import re

from psycopg.rows import dict_row
from sqlglot import exp, parse_one
from sqlglot.errors import ParseError

from agentic_ai.chatbot.db import get_query_pool

# ─── Cấu hình guardrail ───────────────────────────────────────────────────────

# Các bảng dữ liệu thị trường được phép truy vấn. Cố tình LOẠI các bảng nhạy cảm/
# nội bộ: User, RiskAppetite, Portfolio, Favorite, Search_History, chat_sessions,
# và các bảng checkpoint của LangGraph (checkpoints, checkpoint_blobs,
# checkpoint_writes, checkpoint_migrations).
ALLOWED_TABLES: set[str] = {
    "Stock",
    "Current_Stock_Price",
    "Current_Market_Index",
    "Stock_Price_1m",
    "Stock_Price_1d",
    "FA_Summary",
    "FA_Indicator",
    "FA_BalanceSheet",
    "FA_CashFlow",
    "FA_IncomeStatement",
    "FA_Industry_Aggregate",
    "Article",
    "Article_Stock",
    "Article_Category",
    "Category",
    "Category_Stock",
    "BI_Profile",
    "BI_Leader",
    "BI_Subsidiary",
    "MarketIndex",
    "Stock_MarketIndex",
}

MAX_ROWS = 100            # Giới hạn mặc định cho câu hỏi dữ liệu thông thường.
TECHNICAL_MAX_ROWS = 200  # Chỉ dùng khi market_agent cần đủ nến tính chỉ báo.
STATEMENT_TIMEOUT_MS = 4000  # Hủy query chạy quá lâu
MAX_SQL_LENGTH = 12_000

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
_CTE_NAME = re.compile(
    r'(?:\bwith|,)\s+"?([A-Za-z_][A-Za-z0-9_]*)"?\s+as\s*\(',
    re.IGNORECASE,
)

_LIMIT = re.compile(r"\blimit\s+(\d+)\b", re.IGNORECASE)
_DISALLOWED_CONTEXT = re.compile(
    r"\b(current_user|session_user|current_role|current_catalog|current_schema)\b",
    re.IGNORECASE,
)
_ROW_LOCK = re.compile(
    r"\bfor\s+(update|no\s+key\s+update|share|key\s+share)\b", re.IGNORECASE
)
_ALLOWED_FUNCTIONS = {
    "abs", "avg", "cast", "coalesce", "count", "date", "date_trunc",
    "extract", "greatest", "least", "lower", "max", "min", "nullif",
    "round", "sum", "to_char", "upper",
}
def _mask_string_literals(sql: str) -> str:
    """Mask quoted values so their contents are not parsed as SQL structure."""
    return re.sub(r"'(?:''|[^'])*'", "''", sql)


def _validate_function_calls(sql: str) -> None:
    """Allow only approved SQL functions, identified from a PostgreSQL AST.

    A regex cannot distinguish real calls from valid syntax such as
    ``SELECT (current_price)`` or ``FROM (SELECT ...)``. Parsing the SQL first
    preserves the strict function allowlist while avoiding those false positives.
    """
    try:
        statement = parse_one(sql, dialect="postgres")
    except ParseError as exc:
        raise UnsafeSQLError("SQL không hợp lệ.") from exc

    for function in statement.find_all(exp.Func):
        name = function.sql_name().lower()
        if name not in _ALLOWED_FUNCTIONS:
            raise UnsafeSQLError(f"Hàm SQL '{name}' không được phép.")


class UnsafeSQLError(ValueError):
    """Raise khi câu SQL không vượt qua được kiểm tra an toàn."""


def sanitize_sql(sql: str, max_rows: int = MAX_ROWS) -> str:
    """Kiểm tra & chuẩn hóa câu SQL. Trả về SQL sạch hoặc raise UnsafeSQLError."""
    if max_rows not in {MAX_ROWS, TECHNICAL_MAX_ROWS}:
        raise ValueError("max_rows phải là giới hạn truy vấn đã được phê duyệt.")
    if not sql or not sql.strip():
        raise UnsafeSQLError("Câu SQL rỗng.")

    cleaned = sql.strip().rstrip(";").strip()
    if len(cleaned) > MAX_SQL_LENGTH:
        raise UnsafeSQLError("SQL vượt quá độ dài cho phép.")
    structural_sql = _mask_string_literals(cleaned)

    # 1. Cấm comment (né bypass kiểu `-- ` hoặc `/* */`)
    if "--" in structural_sql or "/*" in structural_sql or "*/" in structural_sql:
        raise UnsafeSQLError("SQL chứa comment — không cho phép.")

    # 2. Cấm multi-statement (sau khi đã bỏ dấu ; ở cuối mà vẫn còn ;)
    if ";" in structural_sql:
        raise UnsafeSQLError("Chỉ cho phép một câu lệnh duy nhất.")

    # 3. Phải là câu đọc: bắt đầu bằng SELECT hoặc WITH (CTE)
    lowered = cleaned.lower()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise UnsafeSQLError("Chỉ cho phép câu SELECT (hoặc WITH ... SELECT).")

    # 4. Cấm từ khóa ghi/DDL/lệnh nguy hiểm
    forbidden = _FORBIDDEN_KEYWORDS.search(structural_sql)
    if forbidden:
        raise UnsafeSQLError(f"SQL chứa từ khóa bị cấm: '{forbidden.group(1)}'.")

    # 5. Mọi bảng trong FROM/JOIN phải nằm trong allowlist
    if _DISALLOWED_CONTEXT.search(structural_sql) or _ROW_LOCK.search(structural_sql):
        raise UnsafeSQLError("SQL chứa biểu thức truy cập ngữ cảnh hệ thống.")

    _validate_function_calls(cleaned)

    refs = _TABLE_REF.findall(structural_sql)
    cte_names = {name.lower() for name in _CTE_NAME.findall(structural_sql)}
    if not refs:
        raise UnsafeSQLError("Không xác định được bảng nguồn trong câu SQL.")
    for table in refs:
        if table not in ALLOWED_TABLES and table.lower() not in cte_names:
            raise UnsafeSQLError(
                f"Bảng '{table}' không được phép truy vấn."
            )

    limits = [int(value) for value in _LIMIT.findall(structural_sql)]
    if any(value > max_rows for value in limits):
        raise UnsafeSQLError(f"LIMIT không được vượt quá {max_rows}.")
    if not limits:
        cleaned = f"SELECT * FROM ({cleaned}) AS guarded_query LIMIT {max_rows}"

    return cleaned


def run_select(sql: str, max_rows: int = MAX_ROWS) -> list[dict]:
    """Sanitize rồi chạy câu SELECT trong transaction read-only. Trả list[dict].

    Raise UnsafeSQLError nếu SQL không an toàn; raise các lỗi psycopg nếu SQL sai
    cú pháp/sai cột (market_agent bắt để retry).
    """
    safe_sql = sanitize_sql(sql, max_rows=max_rows)

    pool = get_query_pool()
    with pool.connection() as conn:
        # Mở transaction tường minh (pool đang autocommit) để SET LOCAL có hiệu lực.
        with conn.transaction():
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SET TRANSACTION READ ONLY")
                cur.execute(f"SET LOCAL statement_timeout = {STATEMENT_TIMEOUT_MS}")
                cur.execute("SET LOCAL search_path = pg_catalog, public")
                cur.execute(safe_sql)
                rows = cur.fetchmany(max_rows)
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
    pool = get_query_pool()
    cols_by_table: dict[str, list[str]] = {t: [] for t in table_list}
    table_comment: dict[str, str] = {}

    # Lấy kèm comment (mô tả nghiệp vụ) đã set bằng COMMENT ON — xem schema_comments.sql.
    # information_schema không có sẵn comment nên phải join pg_catalog:
    #   obj_description(oid)        → comment của bảng
    #   col_description(oid, colno) → comment của cột (theo ordinal_position)
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    c.table_name,
                    c.column_name,
                    c.data_type,
                    col_description(pc.oid, c.ordinal_position) AS column_comment,
                    obj_description(pc.oid) AS table_comment
                FROM information_schema.columns c
                JOIN pg_class pc
                    ON pc.relname = c.table_name
                JOIN pg_namespace pn
                    ON pn.oid = pc.relnamespace
                   AND pn.nspname = c.table_schema
                WHERE c.table_schema = 'public'
                  AND c.table_name = ANY(%s)
                ORDER BY c.table_name, c.ordinal_position
                """,
                (table_list,),
            )
            for row in cur.fetchall():
                t = row["table_name"]
                if row["table_comment"] and t not in table_comment:
                    table_comment[t] = row["table_comment"]
                col_def = f"{row['column_name']} {row['data_type']}"
                if row["column_comment"]:
                    col_def += f"  -- {row['column_comment']}"
                cols_by_table.setdefault(t, []).append(col_def)

    lines: list[str] = []
    for table in table_list:
        cols = cols_by_table.get(table) or []
        if not cols:
            continue  # Bảng chưa tồn tại trong DB — bỏ qua khỏi prompt
        cols_str = ",\n  ".join(cols)
        header = f'TABLE "{table}"'
        if table in table_comment:
            header += f"  -- {table_comment[table]}"
        lines.append(f"{header} (\n  {cols_str}\n);")

    _schema_cache = "\n\n".join(lines)
    return _schema_cache
