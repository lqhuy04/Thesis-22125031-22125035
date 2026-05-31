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
    stop_loss_pct: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Stop loss percentage",
    )
    take_profit_pct: float = Field(
        default=0.10,
        ge=0.0,
        le=5.0,
        description="Take profit percentage",
    )
    max_hold_candles: int = Field(
        default=20,
        ge=1,
        le=200,
        description="Maximum holding period in candles",
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
