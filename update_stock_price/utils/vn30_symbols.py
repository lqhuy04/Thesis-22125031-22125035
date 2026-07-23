"""
vn30_symbols.py
Helper dùng chung: lấy danh sách 30 mã cổ phiếu thuộc rổ VN30 từ Supabase.

Quan hệ bảng:
    MarketIndex(id, name)               name = 'VN30'
    Stock_MarketIndex(id, stock_id, market_index_id)
    Stock(id, stock_symbol)

Cách lấy: MarketIndex(name='VN30').id
          → Stock_MarketIndex.market_index_id
          → Stock.id → Stock.stock_symbol
"""

import logging

logger = logging.getLogger(__name__)

VN30_INDEX_NAME = "VN30"

# Stock.id là uuid (~36 ký tự). Gọi .in_("id", stock_ids) với danh sách quá dài
# có thể khiến query string vượt giới hạn độ dài URL (HTTP 414) hoặc bị proxy
# cắt bớt âm thầm. Chia nhỏ theo từng lô để tránh rủi ro này khi rổ mở rộng
# (vd VNINDEX ~400 mã thay vì chỉ 30 mã VN30).
CHUNK_SIZE = 100


def _chunked(seq: list, size: int):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


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

        logger.info(f"Loaded {len(symbols)} VN30 symbols from DB")
        return symbols
    except Exception as e:
        logger.error(f"Failed to fetch VN30 symbols from DB: {e}")
        return set()
