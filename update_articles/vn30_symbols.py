"""
vn30_symbols.py
Helper dùng chung: lấy danh sách 30 mã cổ phiếu thuộc rổ VN30 từ Supabase.

Quan hệ bảng:
    MarketIndex(id, name)               name = 'VN30'
    Stock_MarketIndex(id, stock_id, market_index_id)
    Stock(id, stock_symbol)
    BI_Profile(symbol, company_name)    tên công ty theo mã

Cách lấy: MarketIndex(name='VN30').id
          → Stock_MarketIndex.market_index_id
          → Stock.id → Stock.stock_symbol
          → BI_Profile.symbol → BI_Profile.company_name
"""

import logging

logger = logging.getLogger(__name__)

VN30_INDEX_NAME = "VN30"


def get_vn30_symbols(supabase) -> set[str]:
    """Trả về set các mã cổ phiếu (uppercase) thuộc VN30. Lỗi → set rỗng."""
    try:
        idx_resp = (
            supabase.table("MarketIndex")
            .select("id")
            .eq("name", VN30_INDEX_NAME)
            .limit(1)
            .execute()
        )
        idx_rows = getattr(idx_resp, "data", None) or []
        if not idx_rows:
            logger.error(f"MarketIndex '{VN30_INDEX_NAME}' not found")
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
            logger.warning(f"No stocks linked to MarketIndex '{VN30_INDEX_NAME}'")
            return set()

        stock_resp = (
            supabase.table("Stock")
            .select("stock_symbol")
            .in_("id", stock_ids)
            .execute()
        )
        stock_rows = getattr(stock_resp, "data", None) or []
        symbols = {
            str(row.get("stock_symbol") or "").strip().upper()
            for row in stock_rows
            if str(row.get("stock_symbol") or "").strip()
        }
        logger.info(f"Loaded {len(symbols)} VN30 symbols from DB")
        return symbols
    except Exception as e:
        logger.error(f"Failed to fetch VN30 symbols from DB: {e}")
        return set()


def get_vn30_company_names(supabase) -> dict[str, str]:
    """
    Trả về dict {symbol: company_name} cho các mã VN30.

    Lấy mã VN30 (get_vn30_symbols) rồi join sang BI_Profile để lấy company_name.
    Mã không có company_name trong BI_Profile sẽ fallback về chính symbol.
    Lỗi → dict rỗng.
    """
    try:
        symbols = get_vn30_symbols(supabase)
        if not symbols:
            return {}

        # Mặc định fallback company_name = symbol
        result_map = {symbol: symbol for symbol in symbols}

        profile_resp = (
            supabase.table("BI_Profile")
            .select("symbol, company_name")
            .in_("symbol", list(symbols))
            .execute()
        )
        profile_rows = getattr(profile_resp, "data", None) or []
        for row in profile_rows:
            symbol = str(row.get("symbol") or "").strip().upper()
            company_name = str(row.get("company_name") or "").strip()
            if symbol in result_map and company_name:
                result_map[symbol] = company_name

        matched = sum(1 for s, n in result_map.items() if n != s)
        logger.info(f"Loaded company names for {matched}/{len(result_map)} VN30 symbols")
        return result_map
    except Exception as e:
        logger.error(f"Failed to fetch VN30 company names from DB: {e}")
        return {}
