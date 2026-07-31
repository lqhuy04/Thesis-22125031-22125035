"""
Schemas for the LLM-backed backtest endpoint.
"""

from typing import Literal

from pydantic import BaseModel, Field

from app.models.agentic_schemas import DataSelection


class BacktestPipelineRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=16, pattern=r"^[A-Za-z0-9._-]+$", description="Stock symbol, for example: VNM, FPT, VIC")
    mode: Literal["auto", "manual"] = Field(
        default="auto",
        description="auto = phân tích toàn bộ dữ liệu; manual = chỉ dùng data_selection",
    )
    data_selection: DataSelection = Field(
        default_factory=DataSelection,
        description="Chọn nguồn/chỉ số cho AI phân tích (chỉ áp dụng khi mode = manual)",
    )
    start_date: str | None = Field(
        default=None,
        min_length=10,
        max_length=10,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Optional inclusive start date in ISO format, for example 2021-01-01",
    )
    end_date: str | None = Field(
        default=None,
        min_length=10,
        max_length=10,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Optional inclusive end date in ISO format, for example 2024-12-31",
    )
    market_symbol: str = Field(
        default="VNINDEX",
        min_length=1,
        max_length=16,
        pattern=r"^[A-Za-z0-9._-]+$",
        description="Benchmark symbol for regime analysis",
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
