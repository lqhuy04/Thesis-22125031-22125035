"""
horizon.py — Ánh xạ kỳ hạn đầu tư (risk_appetite.period) sang:

  - Khung nến phân tích kỹ thuật (interval):
        short → 1d, mid → 1w, long → 1M
    (DB chỉ lưu nến 1d; MarketService tự aggregate 1d → 1w / 1M.)

  - Giới hạn cứng TP / SL / max_hold_candles theo PHẦN IV của aggregator.

`period` đến từ app dưới dạng 'short_term' / 'mid_term' / 'long_term', hoặc nhãn
tiếng Việt ('Ngắn hạn' / 'Trung hạn' / 'Dài hạn'). normalize_horizon nhận cả hai.
"""

from typing import Optional


def normalize_horizon(period: Optional[str]) -> str:
    """Chuẩn hóa period về 'short' | 'mid' | 'long' (mặc định 'mid')."""
    p = (period or "").strip().lower()
    if "short" in p or "ngắn" in p or "ngan" in p:
        return "short"
    if "long" in p or "dài" in p or "dai" in p:
        return "long"
    return "mid"


_INTERVAL = {"short": "1d", "mid": "1w", "long": "1M"}


def interval_for(period: Optional[str]) -> str:
    """Khung nến phân tích kỹ thuật tương ứng kỳ hạn."""
    return _INTERVAL[normalize_horizon(period)]


# Giới hạn cứng theo % so với giá mua: (min, max). Khớp PHẦN IV của aggregator.
PRICE_BOUNDS = {
    "short": {"tp": (0.08, 0.15), "sl": (0.04, 0.07), "hold": (5, 15)},
    "mid":   {"tp": (0.15, 0.30), "sl": (0.07, 0.12), "hold": (15, 60)},
    "long":  {"tp": (0.40, 0.80), "sl": (0.15, 0.20), "hold": (120, 260)},
}


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(value, hi))


def enforce_price_boundaries(
    period: Optional[str],
    entry_price: Optional[float],
    take_profit_price: Optional[float],
    stop_loss_price: Optional[float],
    max_hold_candles: Optional[int],
) -> dict:
    """
    Ép TP / SL / max_hold_candles nằm trong giới hạn cứng của kỳ hạn.

    LLM thường bỏ qua các giới hạn này (đặc biệt SL hay tụ về ~6% cho mọi kỳ hạn),
    nên ta tính lại bằng Python để đảm bảo đúng PHẦN IV:
      - TP/SL hiểu theo % so với entry_price.
      - Giá trị LLM đề xuất nếu nằm trong khoảng → giữ; nếu lệch → kẹp vào biên.
      - Nếu thiếu (None) → dùng điểm giữa khoảng.

    Trả về dict {entry_price, take_profit_price, stop_loss_price, max_hold_candles}.
    Nếu không có entry_price hợp lệ → trả nguyên giá trị đầu vào (không thể tính %).
    """
    h = normalize_horizon(period)
    b = PRICE_BOUNDS[h]
    tp_lo, tp_hi = b["tp"]
    sl_lo, sl_hi = b["sl"]
    hold_lo, hold_hi = b["hold"]

    if not entry_price or entry_price <= 0:
        return {
            "entry_price": entry_price,
            "take_profit_price": take_profit_price,
            "stop_loss_price": stop_loss_price,
            "max_hold_candles": max_hold_candles,
        }

    if take_profit_price and take_profit_price > entry_price:
        tp_pct = (take_profit_price - entry_price) / entry_price
    else:
        tp_pct = (tp_lo + tp_hi) / 2
    tp_pct = _clamp(tp_pct, tp_lo, tp_hi)

    if stop_loss_price and 0 < stop_loss_price < entry_price:
        sl_pct = (entry_price - stop_loss_price) / entry_price
    else:
        sl_pct = (sl_lo + sl_hi) / 2
    sl_pct = _clamp(sl_pct, sl_lo, sl_hi)

    if max_hold_candles and max_hold_candles > 0:
        hold = int(_clamp(int(max_hold_candles), hold_lo, hold_hi))
    else:
        hold = (hold_lo + hold_hi) // 2

    return {
        "entry_price": round(entry_price, 2),
        "take_profit_price": round(entry_price * (1 + tp_pct), 2),
        "stop_loss_price": round(entry_price * (1 - sl_pct), 2),
        "max_hold_candles": hold,
    }
