"""
Service to run the LLM-backed backtest pipeline.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
import pandas as pd

from app.backtest.run import run_full_backtest
from app.models.backtest_pipeline_schemas import BacktestPipelineRequest
from app.services.market_service import MarketService


def _parse_dt(trading_time: str) -> datetime:
    clean_time = trading_time.split("+")[0].replace("Z", "")
    try:
        return datetime.fromisoformat(clean_time)
    except ValueError:
        return datetime.strptime(clean_time[:19], "%Y-%m-%dT%H:%M:%S")


def _parse_date_boundary(value: str | None, end_of_day: bool) -> datetime | None:
    if not value:
        return None

    parsed = datetime.fromisoformat(value)
    if len(value) == 10:
        if end_of_day:
            return parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
        return parsed.replace(hour=0, minute=0, second=0, microsecond=0)
    return parsed


def _build_dataframe(
    symbol: str,
    interval: str,
    start_date: str | None,
    end_date: str | None,
) -> pd.DataFrame:
    rows = MarketService.get_stock_price_by_interval(symbol=symbol, interval=interval)
    if not rows:
        raise ValueError(f"No market data for {symbol} at interval {interval}")

    df = pd.DataFrame(rows)
    if df.empty or "trading_time" not in df.columns:
        raise ValueError(f"Missing trading_time column for {symbol} at interval {interval}")

    df["datetime"] = df["trading_time"].apply(_parse_dt)
    df = df.sort_values("datetime").reset_index(drop=True)

    for column in ["open", "high", "low", "close", "volume"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["open", "high", "low", "close", "volume"]).reset_index(drop=True)

    start_boundary = _parse_date_boundary(start_date, end_of_day=False)
    end_boundary = _parse_date_boundary(end_date, end_of_day=True)

    if start_boundary is not None:
        df = df[df["datetime"] >= start_boundary].reset_index(drop=True)
    if end_boundary is not None:
        df = df[df["datetime"] <= end_boundary].reset_index(drop=True)

    if df.empty:
        raise ValueError(f"No data after filtering for {symbol} at interval {interval}")

    return df


def _resolve_end_date(df: pd.DataFrame, fallback_end: str | None) -> datetime:
    if fallback_end:
        return _parse_date_boundary(fallback_end, end_of_day=True) or df["datetime"].max()
    return df["datetime"].max()


def run_backtest_pipeline(request: BacktestPipelineRequest) -> dict[str, Any]:
    symbol = request.symbol.upper().strip()
    market_symbol = request.market_symbol.upper().strip()

    df_1d = _build_dataframe(symbol=symbol, interval="1d", start_date=request.start_date, end_date=request.end_date)

    if request.use_intraday:
        end_dt = _resolve_end_date(df_1d, request.end_date)
        one_minute_start = end_dt - timedelta(days=request.one_minute_lookback_days)

        try:
            df_1m = _build_dataframe(
                symbol=symbol,
                interval="1m",
                start_date=one_minute_start.strftime("%Y-%m-%d"),
                end_date=end_dt.strftime("%Y-%m-%d"),
            )
        except ValueError:
            df_1m_all = _build_dataframe(symbol=symbol, interval="1m", start_date=None, end_date=None)
            latest_dt = df_1m_all["datetime"].max()
            cutoff = latest_dt - timedelta(days=request.one_minute_lookback_days)
            df_1m = df_1m_all[df_1m_all["datetime"] >= cutoff].reset_index(drop=True)
            if df_1m.empty:
                raise ValueError("No 1m data available for fallback window")
    else:
        df_1m = df_1d.copy()

    market_df = _build_dataframe(
        symbol=market_symbol,
        interval="1d",
        start_date=request.start_date,
        end_date=request.end_date,
    )

    trade_config = {
        "max_hold_candles": request.max_hold_candles,
        "exit_on_score_drop": request.exit_on_score_drop,
    }

    return run_full_backtest(
        df_1d=df_1d,
        df_1m=df_1m,
        market_df=market_df,
        symbol=symbol,
        min_signal_score=request.min_signal_score,
        **trade_config,
    )
