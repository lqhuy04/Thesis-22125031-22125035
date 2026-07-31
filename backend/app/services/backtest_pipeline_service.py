"""
Service to run the LLM-backed backtest pipeline.
"""

from __future__ import annotations

from datetime import datetime
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


def run_backtest_pipeline(request: BacktestPipelineRequest) -> dict[str, Any]:
    symbol = request.symbol.upper().strip()
    market_symbol = request.market_symbol.upper().strip()

    # Keep all history before start_date so rolling/EMA indicators at the
    # evaluation boundary are identical to the production v2 technical agent.
    # run_full_backtest trims the scored frame back to the requested period.
    df_1d = _build_dataframe(
        symbol=symbol,
        interval="1d",
        start_date=None,
        end_date=request.end_date,
    )

    # Kept as a compatibility argument for run_full_backtest. The migrated v2
    # pipeline is explicitly daily/mid-term and does not read intraday prices.
    df_1m = df_1d

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

    # Chỉ chế độ manual mới tôn trọng lựa chọn dữ liệu; auto dùng toàn bộ ({}).
    effective_selection = (
        request.data_selection.model_dump() if request.mode == "manual" else {}
    )

    return run_full_backtest(
        df_1d=df_1d,
        df_1m=df_1m,
        market_df=market_df,
        symbol=symbol,
        evaluation_start_date=request.start_date,
        mode=request.mode,
        data_selection=effective_selection,
        **trade_config,
    )
