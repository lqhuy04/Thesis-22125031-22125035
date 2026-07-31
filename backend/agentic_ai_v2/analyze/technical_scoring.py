"""Shared deterministic scoring rules for technical analysis and backtesting."""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any


TECHNICAL_INDICATORS = ("ma", "boll", "rsi", "macd", "kdj")
SCORE_COLUMN_BY_INDICATOR = {
    "ma": "ma_score",
    "boll": "boll_score",
    "rsi": "rsi_score",
    "macd": "macd_score",
    "kdj": "kdj_score",
}

_VALUE_FIELDS = {
    "rsi": ("rsi_14",),
    "ma": ("sma_20", "sma_50"),
    "boll": ("bb_upper", "bb_middle", "bb_lower"),
    "macd": ("macd", "macd_signal", "macd_histogram"),
    "kdj": ("kdj_k", "kdj_d", "kdj_j"),
}


def to_finite_float(value: Any) -> float | None:
    """Convert a scalar to a finite float, returning ``None`` when invalid."""
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def score_rsi(current: Any, previous: Any) -> tuple[int, str]:
    value = to_finite_float(current.get("rsi_14"))
    previous_value = to_finite_float(previous.get("rsi_14"))
    if value is None or previous_value is None:
        return 0, "Không đủ dữ liệu RSI."
    if previous_value < 50 <= value:
        return 1, f"RSI vượt 50 từ dưới lên ({previous_value:.2f} → {value:.2f})."
    if 50 <= value <= 70 and value > previous_value:
        return 1, f"RSI trong vùng động lượng tăng và đang đi lên ({value:.2f})."
    if value < 35 and value > previous_value:
        return 1, f"RSI hồi phục từ vùng quá bán ({previous_value:.2f} → {value:.2f})."
    if value >= 70:
        return 0, f"RSI ở vùng quá mua ({value:.2f})."
    return 0, f"RSI chưa xác nhận động lượng tăng ({value:.2f})."


def score_ma(current: Any, previous: Any) -> tuple[int, str]:
    sma20 = to_finite_float(current.get("sma_20"))
    sma50 = to_finite_float(current.get("sma_50"))
    previous_sma20 = to_finite_float(previous.get("sma_20"))
    previous_sma50 = to_finite_float(previous.get("sma_50"))
    close = to_finite_float(current.get("close"))

    if None in (sma20, sma50, previous_sma20, previous_sma50, close):
        return 0, "Không đủ dữ liệu MA."
    if previous_sma20 < previous_sma50 and sma20 >= sma50:
        return 1, "SMA20 vừa cắt lên SMA50 (Golden Cross)."
    if (
        sma20 > sma50
        and sma20 - sma50 > previous_sma20 - previous_sma50
    ):
        return 1, "SMA20 trên SMA50 và khoảng cách đang mở rộng."
    if close > sma20 > sma50:
        return 1, "Giá trên SMA20 và SMA20 trên SMA50."
    if sma20 < sma50:
        return 0, "SMA20 dưới SMA50, xu hướng trung hạn còn yếu."
    return 0, "MA chưa có tín hiệu tăng rõ ràng."


def score_boll(current: Any, previous: Any) -> tuple[int, str]:
    close = to_finite_float(current.get("close"))
    previous_close = to_finite_float(previous.get("close"))
    upper = to_finite_float(current.get("bb_upper"))
    middle = to_finite_float(current.get("bb_middle"))
    lower = to_finite_float(current.get("bb_lower"))
    previous_middle = to_finite_float(previous.get("bb_middle"))

    if None in (
        close,
        previous_close,
        upper,
        middle,
        lower,
        previous_middle,
    ):
        return 0, "Không đủ dữ liệu Bollinger Bands."
    if previous_close < previous_middle and close >= middle:
        return 1, "Giá vừa vượt lên trên đường giữa Bollinger."
    if close > middle and close - middle > previous_close - previous_middle:
        return 1, "Giá trên đường giữa Bollinger và động lượng đang mở rộng."
    if close <= lower and close > previous_close:
        return 1, "Giá đang hồi phục tại vùng biên dưới Bollinger."
    if close > upper:
        return 0, "Giá vượt biên trên Bollinger, rủi ro quá mua."
    return 0, "Bollinger Bands chưa có tín hiệu tăng rõ ràng."


def score_macd(current: Any, previous: Any) -> tuple[int, str]:
    macd = to_finite_float(current.get("macd"))
    signal = to_finite_float(current.get("macd_signal"))
    histogram = to_finite_float(current.get("macd_histogram"))
    previous_macd = to_finite_float(previous.get("macd"))
    previous_signal = to_finite_float(previous.get("macd_signal"))
    previous_histogram = to_finite_float(
        previous.get("macd_histogram")
    )

    if None in (
        macd,
        signal,
        histogram,
        previous_macd,
        previous_signal,
        previous_histogram,
    ):
        return 0, "Không đủ dữ liệu MACD."
    if previous_macd < previous_signal and macd >= signal:
        return 1, "MACD vừa cắt lên Signal."
    if macd > signal and histogram > previous_histogram:
        return 1, "MACD trên Signal và histogram đang mở rộng."
    if previous_histogram < 0 <= histogram:
        return 1, "MACD histogram vừa chuyển sang dương."
    if macd < signal:
        return 0, "MACD dưới Signal."
    return 0, "MACD chưa có tín hiệu tăng rõ ràng."


def score_kdj(current: Any, previous: Any) -> tuple[int, str]:
    k = to_finite_float(current.get("kdj_k"))
    d = to_finite_float(current.get("kdj_d"))
    j = to_finite_float(current.get("kdj_j"))
    previous_k = to_finite_float(previous.get("kdj_k"))
    previous_d = to_finite_float(previous.get("kdj_d"))
    previous_j = to_finite_float(previous.get("kdj_j"))

    if None in (k, d, j, previous_k, previous_d, previous_j):
        return 0, "Không đủ dữ liệu KDJ."
    if k > 80:
        return 0, "KDJ ở vùng quá mua."
    if k < 20 and k > previous_k:
        return 1, "K hồi phục từ vùng quá bán."
    if previous_k < previous_d and k >= d:
        return 1, "K vừa cắt lên D."
    if k > d and j > previous_j:
        return 1, "K trên D và J đang tăng."
    return 0, "KDJ chưa có tín hiệu tăng rõ ràng."


_SCORERS = {
    "rsi": score_rsi,
    "ma": score_ma,
    "boll": score_boll,
    "macd": score_macd,
    "kdj": score_kdj,
}


def score_indicator(
    name: str,
    current: Any,
    previous: Any,
) -> dict[str, Any]:
    """Return the production score, explanation, and compared values."""
    if name not in _SCORERS:
        raise ValueError(f"Unsupported technical indicator: {name}")

    score, reason = _SCORERS[name](current, previous)
    return {
        "value": {
            field: {
                "current": to_finite_float(current.get(field)),
                "previous": to_finite_float(previous.get(field)),
            }
            for field in _VALUE_FIELDS[name]
        },
        "score": score,
        "reason": reason,
    }


def score_indicators(
    current: Any,
    previous: Any,
    selected_indicators: Iterable[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Score selected indicators in the stable production display order."""
    selected = (
        set(TECHNICAL_INDICATORS)
        if selected_indicators is None
        else set(selected_indicators)
    )
    unsupported = selected.difference(TECHNICAL_INDICATORS)
    if unsupported:
        raise ValueError(
            "Unsupported technical indicators: "
            + ", ".join(sorted(unsupported))
        )
    return {
        name: score_indicator(name, current, previous)
        for name in TECHNICAL_INDICATORS
        if name in selected
    }
