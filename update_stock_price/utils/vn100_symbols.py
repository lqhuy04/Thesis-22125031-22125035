"""
vn100_symbols.py
Helper dùng chung: lấy danh sách 100 mã cổ phiếu thuộc rổ VN100 từ Supabase.

Quan hệ bảng:
    MarketIndex(id, name)               name = 'VN100'
    Stock_MarketIndex(id, stock_id, market_index_id)
    Stock(id, stock_symbol)

Cách lấy: MarketIndex(name='VN100').id
          → Stock_MarketIndex.market_index_id
          → Stock.id → Stock.stock_symbol
"""

import logging

logger = logging.getLogger(__name__)

VN100_INDEX_NAME = "VN100"

# Stock.id là uuid (~36 ký tự). Gọi .in_("id", stock_ids) với danh sách quá dài
# có thể khiến query string vượt giới hạn độ dài URL (HTTP 414) hoặc bị proxy
# cắt bớt âm thầm. Chia nhỏ theo từng lô để tránh rủi ro này.
CHUNK_SIZE = 100


def _chunked(seq: list, size: int):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def get_stock_ids(supabase, symbols) -> dict[str, str]:
    """Resolve arbitrary stock symbols to Stock.id values."""
    normalized_symbols = sorted({
        str(symbol).strip().upper()
        for symbol in symbols
        if str(symbol).strip()
    })
    stocks: dict[str, str] = {}

    for chunk in _chunked(normalized_symbols, CHUNK_SIZE):
        response = (
            supabase.table("Stock")
            .select("id,stock_symbol")
            .in_("stock_symbol", chunk)
            .execute()
        )
        rows = getattr(response, "data", None) or []
        for row in rows:
            symbol = str(row.get("stock_symbol") or "").strip().upper()
            stock_id = row.get("id")
            if not symbol or stock_id is None:
                continue
            normalized_id = str(stock_id)
            previous_id = stocks.get(symbol)
            if previous_id is not None and previous_id != normalized_id:
                raise ValueError(
                    f"Duplicate Stock.stock_symbol '{symbol}' has multiple ids"
                )
            stocks[symbol] = normalized_id

    return stocks


def get_vn100_stock_ids(supabase) -> dict[str, str]:
    """Return an uppercase stock_symbol -> Stock.id mapping for VN100 stocks."""
    try:
        idx_resp = (
            supabase.table("MarketIndex")
            .select("id")
            .eq("name", VN100_INDEX_NAME)
            .limit(1)
            .execute()
        )
        idx_rows = getattr(idx_resp, "data", None) or []
        if not idx_rows:
            logger.error(f"MarketIndex '{VN100_INDEX_NAME}' not found")
            return {}
        market_index_id = idx_rows[0]["id"]

        link_resp = (
            supabase.table("Stock_MarketIndex")
            .select("stock_id")
            .eq("market_index_id", market_index_id)
            .execute()
        )
        link_rows = getattr(link_resp, "data", None) or []
        stock_ids = list(dict.fromkeys(
            row["stock_id"]
            for row in link_rows
            if row.get("stock_id") is not None
        ))
        if not stock_ids:
            logger.warning(f"No stocks linked to MarketIndex '{VN100_INDEX_NAME}'")
            return {}

        stocks: dict[str, str] = {}
        for chunk in _chunked(stock_ids, CHUNK_SIZE):
            try:
                stock_resp = (
                    supabase.table("Stock")
                    .select("id,stock_symbol")
                    .in_("id", chunk)
                    .execute()
                )
                stock_rows = getattr(stock_resp, "data", None) or []
                for row in stock_rows:
                    symbol = str(row.get("stock_symbol") or "").strip().upper()
                    stock_id = row.get("id")
                    if not symbol or stock_id is None:
                        continue
                    normalized_id = str(stock_id)
                    previous_id = stocks.get(symbol)
                    if previous_id is not None and previous_id != normalized_id:
                        logger.error(
                            "Duplicate Stock.stock_symbol '%s' has multiple ids",
                            symbol,
                        )
                        return {}
                    stocks[symbol] = normalized_id
            except Exception as e:
                logger.error(f"Failed to fetch Stock chunk ({len(chunk)} ids): {e}")

        logger.info(f"Loaded {len(stocks)} VN100 stock ids from DB")
        return stocks
    except Exception as e:
        logger.error(f"Failed to fetch VN100 stock ids from DB: {e}")
        return {}


def get_vn100_symbols(supabase) -> set[str]:
    """Return the uppercase symbols of all VN100 stocks."""
    return set(get_vn100_stock_ids(supabase))
