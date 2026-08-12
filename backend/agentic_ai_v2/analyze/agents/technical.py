"""Technical-data preparation node for the v2 analysis graph."""

import logging
from datetime import date
from typing import Any

import pandas as pd

from agentic_ai_v2.analyze.state import AgentState
from agentic_ai_v2.analyze.technical_scoring import (
    TECHNICAL_INDICATORS,
    score_indicators,
    to_finite_float,
)
from app.services.market_service import MarketService
from app.services.technical_indicators_service import TechnicalIndicatorsService

logger = logging.getLogger(__name__)

_INTERVAL_SOURCE_TABLE = {
    "1h": "Stock_Price_1m",
    "1d": "Stock_Price_1d",
    "1w": "Stock_Price_1d",
}
_PRICE_COLUMNS = ["open", "high", "low", "close", "volume"]
_TREND_LOOKBACK_CANDLES = 20
_RETURN_HORIZONS = (1, 5, 10, 20)
_INDICATOR_FIELDS = {
    "ma": ("sma_20", "sma_50"),
    "boll": ("bb_upper", "bb_middle", "bb_lower"),
    "rsi": ("rsi_14",),
    "macd": ("macd", "macd_signal", "macd_histogram"),
    "kdj": ("kdj_k", "kdj_d", "kdj_j"),
}


def _parse_plan_date(value: Any, field_name: str) -> date:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Missing technical plan field: {field_name}")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"Invalid technical plan field {field_name}: {value}"
        ) from exc


def _selected_indicators(state: AgentState) -> set[str]:
    if state.get("mode") == "auto":
        return set(TECHNICAL_INDICATORS)

    selection = (state.get("data_selection") or {}).get("technical") or {}
    return {
        indicator
        for indicator in TECHNICAL_INDICATORS
        if selection.get(indicator) is True
    }


def _fetch_current_price(symbol: str) -> float | None:
    """Return the latest matched price in real VND for the trading plan.

    Indicator comparisons continue to use the latest OHLCV candle close, whose
    stored unit can differ from Current_Stock_Price.
    """
    price_data = MarketService.get_current_stock_price(symbol)
    current_price_vnd = to_finite_float(price_data.get("CurrentPrice"))
    if current_price_vnd is None or current_price_vnd <= 0:
        return None
    return current_price_vnd


def _build_price_frame(rows: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    required_columns = {"trading_time", *_PRICE_COLUMNS}
    missing_columns = required_columns.difference(frame.columns)
    if missing_columns:
        raise ValueError(
            "Price data is missing columns: "
            + ", ".join(sorted(missing_columns))
        )

    frame["trading_time"] = pd.to_datetime(
        frame["trading_time"],
        errors="coerce",
        utc=True,
    )
    for column in _PRICE_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame = (
        frame.dropna(subset=["trading_time", *_PRICE_COLUMNS])
        .sort_values("trading_time")
        .drop_duplicates(subset=["trading_time"], keep="last")
        .reset_index(drop=True)
    )
    if len(frame) < 50:
        raise ValueError(
            "Không đủ dữ liệu để tính chỉ báo kỹ thuật; cần ít nhất 50 nến."
        )
    return frame


def _attach_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    indicators = TechnicalIndicatorsService.calculate_all_indicators(frame)
    output = frame.copy()

    for name, values in indicators.items():
        if len(values) != len(output):
            raise ValueError(
                f"Indicator {name} has {len(values)} values "
                f"for {len(output)} price rows"
            )
        output[name] = values
    return output


def _rounded_float(value: Any) -> float | None:
    parsed = to_finite_float(value)
    return round(parsed, 4) if parsed is not None else None


def _percentage_change(current: Any, previous: Any) -> float | None:
    current_value = to_finite_float(current)
    previous_value = to_finite_float(previous)
    if (
        current_value is None
        or previous_value is None
        or previous_value == 0
    ):
        return None
    return round((current_value / previous_value - 1) * 100, 4)


def _absolute_change(current: Any, previous: Any) -> float | None:
    current_value = to_finite_float(current)
    previous_value = to_finite_float(previous)
    if current_value is None or previous_value is None:
        return None
    return round(current_value - previous_value, 4)


def _mean(values: pd.Series) -> float | None:
    finite_values = [
        parsed
        for value in values
        if (parsed := to_finite_float(value)) is not None
    ]
    if not finite_values:
        return None
    return round(sum(finite_values) / len(finite_values), 4)


def _indicator_fields(selected_indicators: set[str]) -> list[str]:
    return [
        field
        for indicator in TECHNICAL_INDICATORS
        if indicator in selected_indicators
        for field in _INDICATOR_FIELDS[indicator]
    ]


def _build_price_action(window: pd.DataFrame) -> dict[str, Any]:
    closes = window["close"] if "close" in window else pd.Series(dtype=float)
    highs = window["high"] if "high" in window else pd.Series(dtype=float)
    lows = window["low"] if "low" in window else pd.Series(dtype=float)

    latest_close = _rounded_float(closes.iloc[-1]) if not closes.empty else None
    returns = {}
    for horizon in _RETURN_HORIZONS:
        returns[f"{horizon}_candles"] = (
            _percentage_change(closes.iloc[-1], closes.iloc[-1 - horizon])
            if len(closes) > horizon
            else None
        )

    finite_highs = [
        parsed
        for value in highs
        if (parsed := to_finite_float(value)) is not None
    ]
    finite_lows = [
        parsed
        for value in lows
        if (parsed := to_finite_float(value)) is not None
    ]
    highest_high = max(finite_highs) if finite_highs else None
    lowest_low = min(finite_lows) if finite_lows else None
    range_position = None
    if (
        latest_close is not None
        and highest_high is not None
        and lowest_low is not None
        and highest_high > lowest_low
    ):
        range_position = round(
            (latest_close - lowest_low) / (highest_high - lowest_low),
            4,
        )

    finite_closes = [
        parsed
        for value in closes
        if (parsed := to_finite_float(value)) is not None
    ]
    close_changes = [
        current - previous
        for previous, current in zip(finite_closes, finite_closes[1:])
    ]
    return {
        "latest_close": latest_close,
        "returns_pct": returns,
        "highest_high": _rounded_float(highest_high),
        "lowest_low": _rounded_float(lowest_low),
        "close_position_in_range": range_position,
        "up_candles": sum(change > 0 for change in close_changes),
        "down_candles": sum(change < 0 for change in close_changes),
        "unchanged_candles": sum(change == 0 for change in close_changes),
    }


def _build_volume_trend(window: pd.DataFrame) -> dict[str, Any]:
    if "volume" not in window or window.empty:
        return {}

    volumes = window["volume"]
    current_volume = _rounded_float(volumes.iloc[-1])
    average_5 = _mean(volumes.iloc[-5:])
    average_20 = _mean(volumes.iloc[-20:])
    return {
        "current": current_volume,
        "change_1_candle_pct": (
            _percentage_change(volumes.iloc[-1], volumes.iloc[-2])
            if len(volumes) > 1
            else None
        ),
        "average_5": average_5,
        "average_20": average_20,
        "current_vs_average_5": (
            round(current_volume / average_5, 4)
            if current_volume is not None and average_5
            else None
        ),
        "current_vs_average_20": (
            round(current_volume / average_20, 4)
            if current_volume is not None and average_20
            else None
        ),
    }


def _build_indicator_trends(
    window: pd.DataFrame,
    selected_indicators: set[str],
) -> dict[str, Any]:
    trends = {}
    for field in _indicator_fields(selected_indicators):
        if field not in window or window.empty:
            continue
        values = window[field]
        current = _rounded_float(values.iloc[-1])
        finite_values = [
            parsed
            for value in values
            if (parsed := to_finite_float(value)) is not None
        ]
        trends[field] = {
            "current": current,
            "change_1_candle": (
                None
                if len(values) <= 1
                else _absolute_change(values.iloc[-1], values.iloc[-2])
            ),
            "change_5_candles": (
                None
                if len(values) <= 5
                else _absolute_change(values.iloc[-1], values.iloc[-6])
            ),
            "minimum": (
                _rounded_float(min(finite_values)) if finite_values else None
            ),
            "maximum": (
                _rounded_float(max(finite_values)) if finite_values else None
            ),
        }
    return trends


def _build_recent_candles(
    window: pd.DataFrame,
    selected_indicators: set[str],
) -> list[dict[str, Any]]:
    fields = [
        *_PRICE_COLUMNS,
        *_indicator_fields(selected_indicators),
        "volume_ma_20",
        "volume_ma_50",
    ]
    candles = []
    for _, row in window.iterrows():
        candle = {"time": row["trading_time"].isoformat()}
        for field in fields:
            if field in row.index:
                candle[field] = _rounded_float(row.get(field))
        candles.append(candle)
    return candles


def _build_trend_context(
    frame: pd.DataFrame,
    current_position: int,
    selected_indicators: set[str],
) -> dict[str, Any]:
    # N-period returns require N + 1 closing-price observations.
    start_position = max(0, current_position - _TREND_LOOKBACK_CANDLES)
    window = frame.iloc[start_position : current_position + 1]
    return {
        "lookback_candles": max(len(window) - 1, 0),
        "observations": len(window),
        "from": window.iloc[0]["trading_time"].isoformat(),
        "to": window.iloc[-1]["trading_time"].isoformat(),
        "price_action": _build_price_action(window),
        "volume": _build_volume_trend(window),
        "indicator_trends": _build_indicator_trends(
            window,
            selected_indicators,
        ),
        "recent_candles": _build_recent_candles(
            window,
            selected_indicators,
        ),
    }


def _format_output(
    symbol: str,
    interval: str,
    source_table: str,
    requested_from_date: date,
    requested_to_date: date,
    frame: pd.DataFrame,
    selected_indicators: set[str],
    current_price: float | None = None,
) -> dict:
    dates = frame["trading_time"].dt.date
    period_frame = frame[
        (dates >= requested_from_date)
        & (dates <= requested_to_date)
    ]
    if period_frame.empty:
        raise ValueError(
            "Không có dữ liệu giá trong khoảng thời gian được chỉ định."
        )

    current_position = int(period_frame.index[-1])
    if current_position == 0:
        raise ValueError("Không đủ nến trước đó để so sánh chỉ báo.")

    current = frame.iloc[current_position]
    previous = frame.iloc[current_position - 1]
    indicator_results = score_indicators(
        current,
        previous,
        selected_indicators,
    )
    total_score = sum(
        result["score"] for result in indicator_results.values()
    )

    first_period_row = period_frame.iloc[0]
    return {
        "symbol": symbol,
        "interval": interval,
        "source_table": source_table,
        "requested_period": {
            "from_date": requested_from_date.isoformat(),
            "to_date": requested_to_date.isoformat(),
        },
        "actual_period": {
            "from": first_period_row["trading_time"].isoformat(),
            "to": current["trading_time"].isoformat(),
            "candles": len(period_frame),
        },
        "current_price": {
            "value": (
                current_price
                if current_price is not None
                else to_finite_float(current.get("close"))
            ),
            "time": (
                None
                if current_price is not None
                else current["trading_time"].isoformat()
            ),
            "source": (
                "Current_Stock_Price"
                if current_price is not None
                else source_table
            ),
        },
        "total_score": total_score,
        "max_score": len(indicator_results),
        "indicators": indicator_results,
        "trend_context": _build_trend_context(
            frame,
            current_position,
            selected_indicators,
        ),
    }


def technical_agent(state: AgentState) -> dict:
    """Analyze aggregated OHLCV data using the orchestrator technical plan."""
    symbol = state.get("symbol", "").strip().upper()
    technical_plan = (state.get("plan") or {}).get("technical") or {}

    try:
        from_date = _parse_plan_date(
            technical_plan.get("from_date"),
            "from_date",
        )
        to_date = _parse_plan_date(
            technical_plan.get("to_date"),
            "to_date",
        )
        if from_date > to_date:
            raise ValueError("Technical plan from_date is after to_date")

        interval = technical_plan.get("interval")
        if interval not in _INTERVAL_SOURCE_TABLE:
            raise ValueError(f"Unsupported technical interval: {interval}")

        rows = MarketService.get_stock_price_by_interval(
            symbol=symbol,
            interval=interval,
        )
        if not rows:
            raise ValueError(
                f"Không có dữ liệu giá {interval} cho mã {symbol}."
            )

        use_current_price = technical_plan.get("use_current_price", True)
        current_price = (
            _fetch_current_price(symbol)
            if use_current_price
            else None
        )
        frame = _attach_indicators(_build_price_frame(rows))
        output = _format_output(
            symbol=symbol,
            interval=interval,
            source_table=_INTERVAL_SOURCE_TABLE[interval],
            requested_from_date=from_date,
            requested_to_date=to_date,
            frame=frame,
            selected_indicators=_selected_indicators(state),
            current_price=current_price,
        )
    except Exception as exc:
        logger.exception("Technical data preparation failed for %s", symbol)
        output = {"error": str(exc)}

    print(f"Technical output for {symbol}:\n{output}")

    return {
        "agent_results": {
            "technical_agent": output,
        },
    }
