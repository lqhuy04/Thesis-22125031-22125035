"""
Portfolio Schemas
Pydantic models for the flat portfolio table.
"""
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class PortfolioCreateRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=64, description="Stock symbol (e.g. VNM)")
    # `user_id` is derived from the bearer token; do not include in request body
    amount: float = Field(..., gt=0, description="Transaction amount")
    buy_price: float = Field(..., gt=0, description="Buy price per unit")
    time: Optional[datetime] = Field(None, description="Transaction time (ISO8601). If omitted server will use now")


class PortfolioUpdateRequest(BaseModel):
    amount: Optional[float] = Field(None, gt=0, description="Transaction amount")
    buy_price: Optional[float] = Field(None, gt=0, description="Buy price per unit")
    time: Optional[datetime] = Field(None, description="Transaction time (ISO8601)")


class PortfolioData(BaseModel):
    id: str
    stock_id: str
    user_id: str
    amount: float
    buy_price: float
    time: Optional[datetime] = None
