"""
Schemas for the LLM-backed backtest endpoint.
"""

from pydantic import BaseModel, Field


class BacktestPipelineRequest(BaseModel):
    symbol: str = Field(description="Stock symbol, for example: VNM, FPT, VIC")
    start_date: str | None = Field(
        default=None,
        description="Optional inclusive start date in ISO format, for example 2021-01-01",
    )
    end_date: str | None = Field(
        default=None,
        description="Optional inclusive end date in ISO format, for example 2024-12-31",
    )
    market_symbol: str = Field(
        default="VNINDEX",
        description="Benchmark symbol for regime analysis",
    )
    max_hold_candles: int = Field(
        default=20,
        ge=1,
        le=200,
        description="Maximum holding period in candles",
    )
    min_signal_score: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Minimum technical total_score required to trigger a BUY signal",
    )
    exit_on_score_drop: bool = Field(
        default=False,
        description="Exit when total_score drops below 3",
    )
    one_minute_lookback_days: int = Field(
        default=30,
        ge=7,
        le=120,
        description="Lookback window for 1m data",
    )
    use_intraday: bool = Field(
        default=True,
        description="Whether to load 1m data for current-price precision",
    )
