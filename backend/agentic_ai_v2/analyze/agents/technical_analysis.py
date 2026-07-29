"""Technical analysis node for the v2 analysis graph."""

import logging
import math
from datetime import date
from typing import Any

import pandas as pd

from agentic_ai_v2.analyze.state import AgentState
from app.services.market_service import MarketService
from app.services.technical_indicators_service import TechnicalIndicatorsService

logger = logging.getLogger(__name__)

_INTERVAL_SOURCE_TABLE = {
    "1h": "Stock_Price_1m",
    "1d": "Stock_Price_1d",
    "1w": "Stock_Price_1d",
}
_TECHNICAL_INDICATORS = {"ma", "boll", "rsi", "macd", "kdj"}
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
        return set(_TECHNICAL_INDICATORS)

    selection = (state.get("data_selection") or {}).get("technical") or {}
    return {
        indicator
        for indicator in _TECHNICAL_INDICATORS
        if selection.get(indicator) is True
    }


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


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


def _score_rsi(current: pd.Series, previous: pd.Series) -> tuple[int, str]:
    value = _to_float(current.get("rsi_14"))
    previous_value = _to_float(previous.get("rsi_14"))
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


def _score_ma(current: pd.Series, previous: pd.Series) -> tuple[int, str]:
    sma20 = _to_float(current.get("sma_20"))
    sma50 = _to_float(current.get("sma_50"))
    previous_sma20 = _to_float(previous.get("sma_20"))
    previous_sma50 = _to_float(previous.get("sma_50"))
    close = _to_float(current.get("close"))

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


def _score_boll(current: pd.Series, previous: pd.Series) -> tuple[int, str]:
    close = _to_float(current.get("close"))
    previous_close = _to_float(previous.get("close"))
    upper = _to_float(current.get("bb_upper"))
    middle = _to_float(current.get("bb_middle"))
    lower = _to_float(current.get("bb_lower"))
    previous_middle = _to_float(previous.get("bb_middle"))

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


def _score_macd(current: pd.Series, previous: pd.Series) -> tuple[int, str]:
    macd = _to_float(current.get("macd"))
    signal = _to_float(current.get("macd_signal"))
    histogram = _to_float(current.get("macd_histogram"))
    previous_macd = _to_float(previous.get("macd"))
    previous_signal = _to_float(previous.get("macd_signal"))
    previous_histogram = _to_float(previous.get("macd_histogram"))

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


def _score_kdj(current: pd.Series, previous: pd.Series) -> tuple[int, str]:
    k = _to_float(current.get("kdj_k"))
    d = _to_float(current.get("kdj_d"))
    j = _to_float(current.get("kdj_j"))
    previous_k = _to_float(previous.get("kdj_k"))
    previous_d = _to_float(previous.get("kdj_d"))
    previous_j = _to_float(previous.get("kdj_j"))

    if None in (k, d, j, previous_k, previous_d, previous_j):
        return 0, "Không đủ dữ liệu KDJ."
    if previous_k < previous_d and k >= d:
        return 1, "K vừa cắt lên D."
    if k > d and j > previous_j:
        return 1, "K trên D và J đang tăng."
    if k < 20 and k > previous_k:
        return 1, "K hồi phục từ vùng quá bán."
    if k > 80:
        return 0, "KDJ ở vùng quá mua."
    return 0, "KDJ chưa có tín hiệu tăng rõ ràng."


def _indicator_result(
    name: str,
    current: pd.Series,
    previous: pd.Series,
) -> dict:
    scorers = {
        "rsi": _score_rsi,
        "ma": _score_ma,
        "boll": _score_boll,
        "macd": _score_macd,
        "kdj": _score_kdj,
    }
    value_fields = {
        "rsi": ("rsi_14",),
        "ma": ("sma_20", "sma_50"),
        "boll": ("bb_upper", "bb_middle", "bb_lower"),
        "macd": ("macd", "macd_signal", "macd_histogram"),
        "kdj": ("kdj_k", "kdj_d", "kdj_j"),
    }
    score, reason = scorers[name](current, previous)

    return {
        "value": {
            field: {
                "current": _to_float(current.get(field)),
                "previous": _to_float(previous.get(field)),
            }
            for field in value_fields[name]
        },
        "score": score,
        "reason": reason,
    }


def _format_output(
    symbol: str,
    interval: str,
    source_table: str,
    requested_from_date: date,
    requested_to_date: date,
    frame: pd.DataFrame,
    selected_indicators: set[str],
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
    indicator_results = {
        name: _indicator_result(name, current, previous)
        for name in ("ma", "boll", "rsi", "macd", "kdj")
        if name in selected_indicators
    }
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
            "value": _to_float(current.get("close")),
            "time": current["trading_time"].isoformat(),
        },
        "total_score": total_score,
        "max_score": len(indicator_results),
        "indicators": indicator_results,
    }


def technical_analysis_agent(state: AgentState) -> dict:
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

        frame = _attach_indicators(_build_price_frame(rows))
        output = _format_output(
            symbol=symbol,
            interval=interval,
            source_table=_INTERVAL_SOURCE_TABLE[interval],
            requested_from_date=from_date,
            requested_to_date=to_date,
            frame=frame,
            selected_indicators=_selected_indicators(state),
        )
    except Exception as exc:
        logger.exception("Technical analysis failed for %s", symbol)
        output = {"error": str(exc)}
        
    print(f"Technical analysis output for {symbol}:\n{output}")

    return {
        "agent_results": {
            "technical_analysis_agent": output,
        },
    }
