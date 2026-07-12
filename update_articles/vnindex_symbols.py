"""
vnindex_symbols.py
Helper dùng chung: lấy danh sách các mã cổ phiếu thuộc rổ VNINDEX từ Supabase.

Quan hệ bảng:
    MarketIndex(id, name)               name = 'VNINDEX'
    Stock_MarketIndex(id, stock_id, market_index_id)
    Stock(id, stock_symbol)
    BI_Profile(symbol, company_name)    tên công ty theo mã

Cách lấy: MarketIndex(name='VNINDEX').id
          → Stock_MarketIndex.market_index_id
          → Stock.id → Stock.stock_symbol
          → BI_Profile.symbol → BI_Profile.company_name
"""

import logging

logger = logging.getLogger(__name__)

VNINDEX_INDEX_NAME = "VNINDEX"

# Stock.id là uuid (~36 ký tự). Gọi .in_("id", stock_ids) với danh sách quá dài
# (VNINDEX có thể ~400 mã) có thể khiến query string vượt giới hạn độ dài URL
# (HTTP 414) hoặc bị proxy cắt bớt âm thầm. Chia nhỏ theo từng lô để tránh rủi ro này.
CHUNK_SIZE = 100


def _chunked(seq: list, size: int):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def get_vnindex_symbols(supabase) -> set[str]:
    """Trả về set các mã cổ phiếu (uppercase) thuộc VNINDEX. Lỗi → set rỗng."""
    try:
        idx_resp = (
            supabase.table("MarketIndex")
            .select("id")
            .eq("name", VNINDEX_INDEX_NAME)
            .limit(1)
            .execute()
        )
        idx_rows = getattr(idx_resp, "data", None) or []
        if not idx_rows:
            logger.error(f"MarketIndex '{VNINDEX_INDEX_NAME}' not found")
            return set()
        market_index_id = idx_rows[0]["id"]

        link_resp = (
            supabase.table("Stock_MarketIndex")
            .select("stock_id")
            .eq("market_index_id", market_index_id)
            .execute()
        )
        link_rows = getattr(link_resp, "data", None) or []
        stock_ids = [row["stock_id"] for row in link_rows if row.get("stock_id") is not None]
        if not stock_ids:
            logger.warning(f"No stocks linked to MarketIndex '{VNINDEX_INDEX_NAME}'")
            return set()

        symbols: set[str] = set()
        for chunk in _chunked(stock_ids, CHUNK_SIZE):
            try:
                stock_resp = (
                    supabase.table("Stock")
                    .select("stock_symbol")
                    .in_("id", chunk)
                    .execute()
                )
                stock_rows = getattr(stock_resp, "data", None) or []
                symbols.update(
                    str(row.get("stock_symbol") or "").strip().upper()
                    for row in stock_rows
                    if str(row.get("stock_symbol") or "").strip()
                )
            except Exception as e:
                logger.error(f"Failed to fetch stock_symbol chunk ({len(chunk)} ids): {e}")

        logger.info(f"Loaded {len(symbols)} VNINDEX symbols from DB")
        return symbols
    except Exception as e:
        logger.error(f"Failed to fetch VNINDEX symbols from DB: {e}")
        return set()


def get_vnindex_company_names(supabase) -> dict[str, str]:
    """
    Trả về dict {symbol: company_name} cho các mã VNINDEX.

    Lấy mã VNINDEX (get_vnindex_symbols) rồi join sang BI_Profile để lấy company_name.
    Mã không có company_name trong BI_Profile sẽ fallback về chính symbol.
    Lỗi → dict rỗng.
    """
    try:
        symbols = get_vnindex_symbols(supabase)
        if not symbols:
            return {}

        # Mặc định fallback company_name = symbol
        result_map = {symbol: symbol for symbol in symbols}

        for chunk in _chunked(list(symbols), CHUNK_SIZE):
            try:
                profile_resp = (
                    supabase.table("BI_Profile")
                    .select("symbol, company_name")
                    .in_("symbol", chunk)
                    .execute()
                )
                profile_rows = getattr(profile_resp, "data", None) or []
                for row in profile_rows:
                    symbol = str(row.get("symbol") or "").strip().upper()
                    company_name = str(row.get("company_name") or "").strip()
                    if symbol in result_map and company_name:
                        result_map[symbol] = company_name
            except Exception as e:
                logger.error(f"Failed to fetch company_name chunk ({len(chunk)} symbols): {e}")

        matched = sum(1 for s, n in result_map.items() if n != s)
        logger.info(f"Loaded company names for {matched}/{len(result_map)} VNINDEX symbols")
        return result_map
    except Exception as e:
        logger.error(f"Failed to fetch VNINDEX company names from DB: {e}")
        return {}
