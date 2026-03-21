import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI
from supabase import Client, create_client


load_dotenv()


def _get_supabase_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment.")
    return create_client(supabase_url, supabase_key)


def _get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY in environment.")
    return OpenAI(api_key=api_key)


def _fetch_table(
    supabase: Client,
    table_name: str,
    symbol: str,
    year: Optional[int],
    limit: int,
) -> List[Dict[str, Any]]:
    query = supabase.table(table_name).select("*").eq("symbol", symbol.upper())
    if year is not None:
        query = query.eq("year", year)
    query = query.order("year", desc=True).limit(limit)
    result = query.execute()
    return result.data if result.data else []


def _upsert_summary(supabase: Client, symbol: str, summary: str) -> None:
    supabase.table("fundamental_analysis_summary")\
        .upsert(
            {
                "symbol": symbol.upper(),
                "summary": summary,
            },
            on_conflict="symbol",
        )\
        .execute()


def get_saved_summary(symbol: str) -> Optional[str]:
    supabase = _get_supabase_client()
    result = (
        supabase.table("fundamental_analysis_summary")
        .select("summary")
        .eq("symbol", symbol.upper())
        .limit(1)
        .execute()
    )
    if not result.data:
        return None
    return result.data[0].get("summary")


def fetch_fundamental_tables(symbol: str, year: Optional[int] = None, limit: int = 5) -> Dict[str, List[Dict[str, Any]]]:
    supabase = _get_supabase_client()
    return {
        "balance_sheets": _fetch_table(supabase, "financial_balance_sheets", symbol, year, limit),
        "income_statements": _fetch_table(supabase, "financial_income_statements", symbol, year, limit),
        "cash_flows": _fetch_table(supabase, "financial_cash_flows", symbol, year, limit),
        "financial_indicators": _fetch_table(supabase, "financial_indicators", symbol, year, limit),
    }


def summarize_fundamental(symbol: str, company_name: Optional[str] = None, year: Optional[int] = None, limit: int = 5) -> Dict[str, Any]:
    supabase = _get_supabase_client()
    data = {
        "balance_sheets": _fetch_table(supabase, "financial_balance_sheets", symbol, year, limit),
        "income_statements": _fetch_table(supabase, "financial_income_statements", symbol, year, limit),
        "cash_flows": _fetch_table(supabase, "financial_cash_flows", symbol, year, limit),
        "financial_indicators": _fetch_table(supabase, "financial_indicators", symbol, year, limit),
    }

    if not any(data.values()):
        raise ValueError(f"No financial data found for symbol: {symbol}")

    target_name = company_name or symbol.upper()
    prompt = f"""
Tôi sẽ cung cấp cho bạn 4 bảng dữ liệu phân tích cơ bản của {target_name}: Bảng cân đối kế toán, Bảng kết quả kinh doanh, Bảng lưu chuyển tiền tệ và Các chỉ số tài chính.

Hãy đóng vai một chuyên gia phân tích tài chính cao cấp, thực hiện tóm tắt những thông tin cốt lõi theo các mục sau:

- Sức khỏe tài chính tổng quát
- Hiệu quả hoạt động
- Đánh giá chỉ số
- Điểm nhấn và Rủi ro

Yêu cầu: Trình bày ngắn gọn, súc tích, mỗi ý tóm tắt trong một đoạn 3 - 5 câu.

Dữ liệu đầu vào (JSON):
- Bảng cân đối kế toán: {data['balance_sheets']}
- Bảng kết quả kinh doanh: {data['income_statements']}
- Bảng lưu chuyển tiền tệ: {data['cash_flows']}
- Các chỉ số tài chính: {data['financial_indicators']}
""".strip()

    client = _get_openai_client()
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": "Bạn là chuyên gia phân tích tài chính cấp cao, viết rõ ràng, súc tích, trung lập và bám sát dữ liệu.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    analysis = completion.choices[0].message.content or ""
    cleaned_analysis = analysis.strip()

    _upsert_summary(supabase=supabase, symbol=symbol, summary=cleaned_analysis)

    years = sorted(
        {
            row.get("year")
            for rows in data.values()
            for row in rows
            if isinstance(row, dict) and row.get("year") is not None
        },
        reverse=True,
    )

    return {
        "symbol": symbol.upper(),
        "company_name": target_name,
        "analysis": cleaned_analysis,
        "source_years": years,
        "raw_data": data,
    }
