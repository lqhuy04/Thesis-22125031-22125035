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
