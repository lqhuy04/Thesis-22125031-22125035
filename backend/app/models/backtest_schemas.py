"""
Schemas for the technical backtest endpoint.
"""

from typing import Any

from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    symbol: str = Field(description="Stock symbol, for example: VNM, FPT, VIC")
    interval: str = Field(default="1d", description="Interval: 1m, 5m, 15m, 30m, 1h, 1d, 1w, 1M")
    start_date: str | None = Field(
        default=None,
        description="Optional inclusive start date in ISO format, for example 2024-01-01",
    )
    end_date: str | None = Field(
        default=None,
        description="Optional inclusive end date in ISO format, for example 2024-12-31",
    )
    holding_period: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Number of candles to hold each trade after entry",
    )
    min_total_score: int = Field(
        default=3,
        ge=0,
        le=5,
        description="Minimum technical score required to enter a trade",
    )
    transaction_cost_bps: float = Field(
        default=20.0,
        ge=0,
        description="Round-trip transaction fee per side in basis points",
    )
    slippage_bps: float = Field(
        default=10.0,
        ge=0,
        description="Execution slippage per side in basis points",
    )
    initial_capital: float = Field(
        default=100_000_000.0,
        gt=0,
        description="Starting capital in VND",
    )
    benchmark_symbol: str | None = Field(
        default="VNINDEX",
        description="Optional benchmark symbol to compare buy-and-hold performance",
    )


class BacktestTrade(BaseModel):
    signal_time: str
    entry_time: str
    exit_time: str
    signal_index: int
    entry_index: int
    exit_index: int
    recommendation: str
    total_score: int
    entry_price: float
    exit_price: float
    gross_return_pct: float
    net_return_pct: float
    signal_snapshot: dict[str, Any]


class BacktestSummary(BaseModel):
    symbol: str
    interval: str
    start_date: str | None
    end_date: str | None
    holding_period: int
    min_total_score: int
    transaction_cost_bps: float
    slippage_bps: float
    initial_capital: float
    final_equity: float
    total_return_pct: float
    buy_and_hold_return_pct: float | None
    benchmark_symbol: str | None
    benchmark_return_pct: float | None
    total_bars: int
    signals_generated: int
    trades_taken: int
    win_rate_pct: float
    avg_trade_return_pct: float
    profit_factor: float | None
    max_drawdown_pct: float
    sharpe_ratio: float | None


class BacktestResponse(BaseModel):
    summary: BacktestSummary
    trades: list[BacktestTrade]
    equity_curve: list[dict[str, Any]]
    assumptions: list[str]