"""
app/utils/market_index.py

Resolve the stock symbols that belong to a market index (e.g. VN30, VN100)
from Supabase. Mirrors update_stock_price/vn30_symbols.py but is generic over
the index name.

Table relationships:
    MarketIndex(id, name)                       name = 'VN30' | 'VN100' | ...
    Stock_MarketIndex(id, stock_id, market_index_id)
    Stock(id, stock_symbol)
"""

import logging

from supabase import create_client, Client

from app.config import settings

logger = logging.getLogger(__name__)

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def get_index_symbols(index_name: str) -> list[str]:
    """
    Return the sorted list of uppercase stock symbols belonging to the given
    market index. Returns an empty list if the index is unknown or has no
    linked stocks.
    """
    name = (index_name or "").strip().upper()
    if not name:
        return []

    idx_resp = (
        supabase.table("MarketIndex")
        .select("id")
        .eq("name", name)
        .limit(1)
        .execute()
    )
    idx_rows = getattr(idx_resp, "data", None) or []
    if not idx_rows:
        logger.warning("MarketIndex '%s' not found", name)
        return []
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
        logger.warning("No stocks linked to MarketIndex '%s'", name)
        return []

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
    logger.info("Loaded %d symbols for index '%s'", len(symbols), name)
    return sorted(symbols)
