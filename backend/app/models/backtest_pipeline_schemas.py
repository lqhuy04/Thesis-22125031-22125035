"""
Schemas for the LLM-backed backtest endpoint.
"""

from pydantic import BaseModel, Field

from app.models.agentic_schemas import DataSelection


class BacktestPipelineRequest(BaseModel):
    symbol: str = Field(description="Stock symbol, for example: VNM, FPT, VIC")
    mode: str = Field(
        default="auto",
        description="auto = phân tích toàn bộ dữ liệu; manual = chỉ dùng data_selection",
    )
    data_selection: DataSelection = Field(
        default_factory=DataSelection,
        description="Chọn nguồn/chỉ số cho AI phân tích (chỉ áp dụng khi mode = manual)",
    )
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
    transaction_cost_pct: float = Field(
        default=0.0015,
        ge=0.0,
        le=0.05,
        description="Transaction cost per side as a decimal (0.0015 = 0.15%). Applied both at entry and exit.",
    )
