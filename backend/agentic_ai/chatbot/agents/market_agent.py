"""
agentic_ai/chatbot/agents/market_agent.py — Market Query Agent (text-to-SQL)

Xử lý intent MARKET_QUERY: câu hỏi cần dữ liệu thị trường thực tế.

Luồng:
  1. generate_sql  — LLM sinh một câu SELECT dựa trên schema thật (introspect động).
  2. run_select    — chạy qua sql_runner (read-only, allowlist bảng, timeout). Lỗi → retry 1 lần.
  3. (tùy chọn) tính chỉ báo kỹ thuật từ OHLC bằng TechnicalIndicatorsService —
                 vì RSI/MACD/KDJ KHÔNG lưu trong DB.
  4. synthesize    — LLM lần 2 viết câu trả lời tiếng Việt dựa trên dữ liệu lấy được.

Mọi SQL đều đi qua sql_runner.sanitize_sql() — LLM không bao giờ chạm DB trực tiếp.
"""

import json
import unicodedata
from datetime import datetime, timezone, timedelta

import pandas as pd
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel

from agentic_ai.chatbot.state import ChatbotState
from agentic_ai.chatbot.sql_runner import get_schema_ddl, run_select, UnsafeSQLError
from agentic_ai.service.openai_service import _get_openai_client
from app.services.technical_indicators_service import TechnicalIndicatorsService

# Giờ Việt Nam (UTC+7) — dùng để cho LLM biết "hôm nay" là ngày nào.
_VN_TZ = timezone(timedelta(hours=7))


def _today_str() -> str:
    """Ngày hôm nay theo giờ Việt Nam, dạng YYYY-MM-DD."""
    return datetime.now(_VN_TZ).strftime("%Y-%m-%d")


def _normalize_text(text: str) -> str:
    """Chuẩn hóa Unicode về dạng NFC để câu hỏi có dấu/không dấu được tokenize ổn định.

    Tiếng Việt có thể được gõ ở nhiều dạng tổ hợp dấu khác nhau (NFC vs NFD);
    chuẩn hóa giúp LLM nhận cùng một chuỗi token cho cùng một câu, giảm việc
    cùng câu hỏi mà ra kết quả khác nhau.
    """
    if not text:
        return text
    return unicodedata.normalize("NFC", text).strip()


def _fallback_sql_for_symbol(symbol: str) -> str:
    """Câu SQL mặc định khi đã xác định được mã CK nhưng LLM không sinh SQL.

    Lấy bảng tổng quan cơ bản FA_Summary của mã đó — luôn có dữ liệu để đánh giá,
    không phụ thuộc vào quyết định bỏ cuộc thiếu ổn định của LLM.
    """
    sym = symbol.strip().upper().replace("'", "")
    return (
        'SELECT * FROM "FA_Summary" '
        'WHERE stock_id = (SELECT id FROM "Stock" '
        f"WHERE stock_symbol = '{sym}') LIMIT 1"
    )


# ─── Prompts ───────────────────────────────────────────────────────────────────

GEN_SQL_SYSTEM_PROMPT = """
Bạn là chuyên gia chuyển câu hỏi (tiếng Việt hoặc tiếng Anh) về chứng khoán thành MỘT câu
truy vấn PostgreSQL (SELECT) trên cơ sở dữ liệu thị trường chứng khoán Việt Nam.

Hôm nay là ngày {today} (giờ Việt Nam). Khi user nói "hôm nay", "today", "hiện tại", "now"...
hãy hiểu theo ngày này (vd lọc trading_time theo ngày này).

QUY TẮC SINH SQL (bắt buộc tuân thủ):
- Chỉ sinh MỘT câu SELECT (hoặc WITH ... SELECT). TUYỆT ĐỐI không INSERT/UPDATE/DELETE/DDL.
- Chỉ dùng các bảng và CỘT có trong schema dưới đây. Không bịa tên cột.
- Tên bảng phân biệt hoa/thường → luôn bọc trong dấu nháy kép, ví dụ: "Current_Stock_Price".
- Mã cổ phiếu viết HOA (VNM, HPG, FPT...).
- Luôn thêm LIMIT hợp lý (<= 100). Với dữ liệu lịch sử/giá theo thời gian, ORDER BY thời gian DESC.
- Các bảng FA_* (cơ bản) liên kết với "Stock" qua FA_*.stock_id = "Stock".id.
- Tin tức: "Article" liên kết "Stock" qua bảng nối "Article_Stock" (article_id, stock_id).

⚠️ ĐƠN VỊ GIÁ/KHỐI LƯỢNG (BẮT BUỘC):
- Trong HAI bảng "Stock_Price_1d" và "Stock_Price_1m", các cột open, high, low, close, volume
  được lưu ở dạng ĐÃ CHIA 1000 (giá trị thật = giá trị lưu × 1000).
- Khi SELECT bất kỳ cột nào trong open/high/low/close/volume từ hai bảng này, BẮT BUỘC nhân
  với 1000 NGAY TRONG SQL và GIỮ NGUYÊN tên cột (alias) để kết quả trả về là giá trị thật:
    SELECT (close * 1000) AS close, (volume * 1000) AS volume FROM "Stock_Price_1d" ...
  Với hàm tổng hợp cũng phải nhân 1000:
    SELECT (MAX(high) * 1000) AS max_high FROM "Stock_Price_1d" ...
- Các bảng KHÁC (vd "Current_Stock_Price") KHÔNG áp dụng quy tắc này — giữ nguyên giá trị.

PHÂN TÍCH KỸ THUẬT (RSI, MACD, KDJ, Bollinger, SMA):
- Các chỉ báo này KHÔNG lưu trong DB, phải tính từ dữ liệu nến.
- Khi user hỏi chỉ báo kỹ thuật: đặt needs_technical_calc = true, và sinh SQL lấy
  (open * 1000) AS open, (high * 1000) AS high, (low * 1000) AS low,
  (close * 1000) AS close, (volume * 1000) AS volume, trading_time
  từ bảng "Stock_Price_1d" của mã đó, ORDER BY trading_time DESC LIMIT 200
  (cần >= 50 nến để tính được; nhớ quy tắc ×1000 ở trên).

⭐ KHI ĐÃ XÁC ĐỊNH ĐƯỢC MÃ CỔ PHIẾU (BẮT BUỘC):
- Nếu xác định được một mã CK (ghi vào trường symbol) và câu hỏi mang tính ĐÁNH GIÁ
  định tính (vd "có tiềm năng không", "có nên mua không", "đánh giá", "sức khỏe tài chính",
  "định giá", "cổ phiếu này thế nào")... thì TUYỆT ĐỐI KHÔNG để sql rỗng.
  PHẢI sinh truy vấn lấy dữ liệu cơ bản tổng quan:
    SELECT * FROM "FA_Summary"
    WHERE stock_id = (SELECT id FROM "Stock" WHERE stock_symbol = 'MÃ') LIMIT 1
  (có thể bổ sung JOIN/UNION với "FA_Indicator" nếu cần thêm chỉ số định giá).
- Chỉ đặt sql = "" khi câu hỏi THỰC SỰ nằm ngoài phạm vi dữ liệu (không có mã CK nào,
  hoặc hỏi thứ không thể suy ra từ schema). Đừng bỏ cuộc chỉ vì câu hỏi mang tính định tính.

NẾU KHÔNG THỂ TRẢ LỜI BẰNG DỮ LIỆU SẴN CÓ:
- Đặt sql = "" và ghi no_query_reason giải thích ngắn gọn. (Lưu ý: nếu đã có symbol, hãy
  ưu tiên sinh SQL FA_Summary như quy tắc ⭐ ở trên thay vì để rỗng.)

NGÔN NGỮ:
- Phát hiện ngôn ngữ của câu hỏi MỚI NHẤT và ghi vào trường language
  (vd "Vietnamese", "English"). Dùng để trả lời đúng ngôn ngữ người dùng.

Chỉ trả về đúng cấu trúc được yêu cầu.

=== SCHEMA ===
{schema}
""".strip()

SYNTHESIZE_SYSTEM_PROMPT = """
Bạn là chuyên gia phân tích chứng khoán Việt Nam. Hãy trả lời câu hỏi của người dùng
DỰA HOÀN TOÀN trên dữ liệu được cung cấp bên dưới (lấy từ cơ sở dữ liệu).

Hôm nay là ngày {today} (giờ Việt Nam).

⚠️ NGÔN NGỮ (QUAN TRỌNG NHẤT): BẮT BUỘC viết TOÀN BỘ câu trả lời bằng {language}.
Không dùng ngôn ngữ khác, bất kể prompt này viết bằng tiếng Việt.

Quy tắc:
- KHÔNG bịa thêm số liệu ngoài dữ liệu được cung cấp.
- Nếu kết quả CÓ cột thời gian (vd trading_time, trading_date) và mốc đó KHÔNG phải hôm nay
  ({today}), nói rõ "dữ liệu ngày ..." — KHÔNG ngầm hiểu là dữ liệu của hôm nay.
- Nếu kết quả KHÔNG có cột thời gian nào, đừng bịa/đoán ngày — chỉ trình bày số liệu.
- Nếu dữ liệu rỗng, nói thẳng là không tìm thấy dữ liệu cho mã/câu hỏi đó.
- Với chỉ báo kỹ thuật, diễn giải ý nghĩa (vd RSI > 70 là quá mua) dựa trên giá trị mới nhất.
""".strip()


# ─── Schema cho structured output ──────────────────────────────────────────────

class GeneratedSQL(BaseModel):
    sql: str                          # Câu SELECT, hoặc "" nếu không thể truy vấn
    needs_technical_calc: bool        # True nếu cần tính chỉ báo kỹ thuật từ OHLC
    symbol: str | None                # Mã cổ phiếu chính (nếu xác định được)
    no_query_reason: str | None       # Lý do nếu sql rỗng
    language: str                     # Ngôn ngữ câu hỏi (vd "Vietnamese", "English") để trả lời đúng ngôn ngữ


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _history_to_messages(history: list[BaseMessage], limit: int = 6) -> list[dict]:
    msgs = []
    for msg in history[-limit:]:
        role = "assistant" if isinstance(msg, AIMessage) else "user"
        msgs.append({"role": role, "content": msg.content})
    return msgs


def _generate_sql(client, history: list[BaseMessage], user_input: str,
                  prev_error: str | None = None) -> GeneratedSQL:
    """Gọi LLM sinh SQL. prev_error != None → vòng retry, đính kèm lỗi để LLM sửa."""
    system = GEN_SQL_SYSTEM_PROMPT.format(schema=get_schema_ddl(), today=_today_str())
    messages = [{"role": "system", "content": system}]
    messages += _history_to_messages(history)
    user_content = user_input
    if prev_error:
        user_content = (
            f"{user_input}\n\n[Câu SQL trước bị lỗi: {prev_error}\n"
            f"Hãy sửa lại, chỉ dùng cột có trong schema.]"
        )
    messages.append({"role": "user", "content": user_content})

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        temperature=0,
        messages=messages,
        response_format=GeneratedSQL,
    )
    return completion.choices[0].message.parsed


def _compute_technical(rows: list[dict]) -> dict | None:
    """Tính chỉ báo kỹ thuật từ rows OHLC. Trả về giá trị MỚI NHẤT của từng chỉ báo."""
    if not rows:
        return None
    df = pd.DataFrame(rows)
    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(df.columns):
        return None

    # SQL trả DESC (mới nhất trước) → đảo lại tăng dần để tính chỉ báo cho đúng.
    if "trading_time" in df.columns:
        df = df.sort_values("trading_time").reset_index(drop=True)
    else:
        df = df.iloc[::-1].reset_index(drop=True)

    try:
        indicators = TechnicalIndicatorsService.calculate_all_indicators(df)
    except ValueError as e:
        return {"error": str(e)}

    # Mỗi chỉ báo là một mảng theo thời gian → chỉ lấy giá trị cuối (mới nhất).
    latest: dict = {}
    for key, series in indicators.items():
        if isinstance(series, list) and series:
            latest[key] = series[-1]
        else:
            latest[key] = series
    return latest


def _synthesize(client, history: list[BaseMessage], user_input: str,
                rows: list[dict], technical: dict | None,
                language: str = "Vietnamese") -> str:
    """LLM lần 2: viết câu trả lời dựa trên dữ liệu lấy được."""
    data_payload = {"rows": rows[:50]}
    if technical is not None:
        data_payload["technical_indicators_latest"] = technical

    system = SYNTHESIZE_SYSTEM_PROMPT.format(today=_today_str(), language=language or "Vietnamese")
    messages = [{"role": "system", "content": system}]
    messages += _history_to_messages(history, limit=4)
    messages.append({
        "role": "user",
        "content": (
            f"Câu hỏi: {user_input}\n\n"
            f"Dữ liệu từ DB (JSON):\n"
            f"{json.dumps(data_payload, ensure_ascii=False, default=str)}"
        ),
    })

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=messages,
    )
    return response.choices[0].message.content


# ─── Agent function ────────────────────────────────────────────────────────────

def market_agent(state: ChatbotState) -> dict:
    # Cách 3: chuẩn hóa Unicode (NFC) để câu hỏi có dấu/không dấu ổn định khi tokenize.
    user_input = _normalize_text(state["user_input"])
    history: list[BaseMessage] = state.get("messages", [])

    print(f"[Market Agent] >>> Input  : {user_input!r}")
    print(f"[Market Agent] >>> History: {len(history)} messages")

    try:
        client = _get_openai_client()

        # 1) Sinh SQL
        gen = _generate_sql(client, history, user_input)
        print(f"[Market Agent] >>> SQL    : {gen.sql!r}")
        print(f"[Market Agent] >>> TechCalc: {gen.needs_technical_calc} | Symbol: {gen.symbol}")

        # Cách 1: LLM bỏ cuộc (sql rỗng) nhưng VẪN xác định được mã CK →
        # tự build query FA_Summary mặc định thay vì từ chối. Quyết định "đã có mã
        # thì luôn truy vấn được" phải deterministic, không lệ thuộc ý LLM.
        if not gen.sql.strip() and gen.symbol and gen.symbol.strip():
            gen.sql = _fallback_sql_for_symbol(gen.symbol)
            print(f"[Market Agent] >>> Fallback SQL (symbol={gen.symbol}): {gen.sql!r}")

        # Thật sự không thể tạo truy vấn (không có cả mã CK) → trả lời lịch sự, không bịa
        if not gen.sql.strip():
            reason = gen.no_query_reason or "Câu hỏi cần dữ liệu chưa có trong hệ thống."
            print(f"[Market Agent] >>> NoQuery: {reason}")
            reply = (
                "Xin lỗi, hiện tôi chưa thể truy vấn dữ liệu cho câu hỏi này. "
                f"{reason}"
            )
            return {
                "messages": [HumanMessage(content=user_input), AIMessage(content=reply)],
                "generated_sql": None,
                "final_output": reply,
                "error": None,
            }

        # 2) Chạy SQL (retry 1 lần nếu lỗi cú pháp/cột)
        try:
            rows = run_select(gen.sql)
        except UnsafeSQLError as e:
            # SQL không an toàn — không retry, từ chối luôn
            print(f"[Market Agent] >>> UNSAFE SQL: {e}")
            reply = "Xin lỗi, tôi không thể thực hiện truy vấn này vì lý do an toàn dữ liệu."
            return {
                "messages": [HumanMessage(content=user_input), AIMessage(content=reply)],
                "generated_sql": gen.sql,
                "final_output": reply,
                "error": f"UnsafeSQL: {e}",
            }
        except Exception as e:
            print(f"[Market Agent] >>> SQL error, retrying once: {e}")
            gen = _generate_sql(client, history, user_input, prev_error=str(e))
            print(f"[Market Agent] >>> SQL(retry): {gen.sql!r}")
            rows = run_select(gen.sql)

        print(f"[Market Agent] >>> Rows   : {len(rows)}")

        # 3) Chỉ báo kỹ thuật (nếu cần)
        technical = None
        if gen.needs_technical_calc:
            technical = _compute_technical(rows)
            print(f"[Market Agent] >>> Technical: {technical is not None}")

        # 4) Tổng hợp câu trả lời (đúng ngôn ngữ user đã hỏi)
        reply = _synthesize(client, history, user_input, rows, technical, gen.language)
        print(f"[Market Agent] >>> Reply  : {reply[:120]}{'...' if len(reply) > 120 else ''}")

        return {
            "messages": [HumanMessage(content=user_input), AIMessage(content=reply)],
            "generated_sql": gen.sql,
            "query_result": rows[:50],
            "final_output": reply,
            "error": None,
        }

    except Exception as e:
        print(f"[Market Agent] >>> ERROR  : {e}")
        return {
            "final_output": "Xin lỗi, có lỗi xảy ra khi truy vấn dữ liệu thị trường. Vui lòng thử lại.",
            "error": f"Lỗi Market Agent: {e}",
        }
