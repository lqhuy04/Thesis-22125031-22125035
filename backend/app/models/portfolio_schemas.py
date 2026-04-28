"""
Portfolio Schemas
Pydantic models for the flat portfolio table.
"""
from typing import Optional

from pydantic import BaseModel, Field


class PortfolioCreateRequest(BaseModel):
    stock_id: str = Field(..., min_length=1, max_length=64, description="Stock ID or symbol")
    user_id: str = Field(..., min_length=1, max_length=64, description="Owner user ID")
    amount: float = Field(..., gt=0, description="Holding amount")
    avg_price: float = Field(..., gt=0, description="Average buy price")


class PortfolioUpdateRequest(BaseModel):
    amount: Optional[float] = Field(None, gt=0, description="Holding amount")
    avg_price: Optional[float] = Field(None, gt=0, description="Average buy price")


class PortfolioData(BaseModel):
    id: str
    stock_id: str
    user_id: str
    amount: float
    avg_price: float
