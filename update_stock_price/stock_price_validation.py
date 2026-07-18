"""Shared validation helpers for stock/index OHLCV ingestion."""

from __future__ import annotations

import math
from typing import Any


PRICE_FIELDS = ("open", "high", "low", "close")


def _parse_finite_number(value: Any) -> float | None:
    """Return a finite float, or None when the provider value is unusable."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    return number if math.isfinite(number) else None


def normalize_ohlcv(
    open_value: Any,
    high_value: Any,
    low_value: Any,
    close_value: Any,
    volume_value: Any,
    *,
    price_multiplier: float = 1.0,
    allow_zero_volume: bool = False,
) -> tuple[dict[str, float] | None, str | None]:
    """Parse and validate an OHLCV payload.

    A zero-volume candle is rejected for stocks because a trade-based candle
    must contain matched volume. It may be allowed for market indices, whose
    volume does not have the same meaning as a security's matched volume.
    """
    raw_values = {
        "open": open_value,
        "high": high_value,
        "low": low_value,
        "close": close_value,
        "volume": volume_value,
    }
    parsed = {name: _parse_finite_number(value) for name, value in raw_values.items()}

    for field, value in parsed.items():
        if value is None:
            return None, f"missing_or_invalid_{field}"

    ohlcv = {field: parsed[field] * price_multiplier for field in PRICE_FIELDS}
    ohlcv["volume"] = parsed["volume"]

    for field in PRICE_FIELDS:
        if ohlcv[field] <= 0:
            return None, f"non_positive_{field}"

    if ohlcv["volume"] < 0:
        return None, "negative_volume"
    if ohlcv["volume"] == 0 and not allow_zero_volume:
        return None, "zero_volume"

    if ohlcv["high"] < max(ohlcv["open"], ohlcv["low"], ohlcv["close"]):
        return None, "high_below_ohlc"
    if ohlcv["low"] > min(ohlcv["open"], ohlcv["high"], ohlcv["close"]):
        return None, "low_above_ohlc"

    return ohlcv, None
