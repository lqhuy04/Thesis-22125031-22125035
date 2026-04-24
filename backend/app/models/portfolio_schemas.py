"""
Portfolio Schemas
Pydantic models for portfolio API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Optional


class PortfolioCreateRequest(BaseModel):
    user_id: str = Field(..., description="Owner user ID (temporary for testing without auth)")
    name: str = Field(..., min_length=1, max_length=255, description="Portfolio name")
    description: Optional[str] = Field(None, description="Portfolio description")


class PortfolioUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Portfolio name")
    description: Optional[str] = Field(None, description="Portfolio description")


class PortfolioData(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None


class HoldingCreateRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10, description="Stock symbol")
    shares: float = Field(..., gt=0, description="Number of shares bought")
    buy_price: float = Field(..., gt=0, description="Buy price per share for this transaction")
    company_name: Optional[str] = Field(None, description="Company name override")


class HoldingUpdateRequest(BaseModel):
    shares: Optional[float] = Field(None, gt=0, description="Current total shares")
    avg_buy_price: Optional[float] = Field(None, gt=0, description="Average buy price")
    company_name: Optional[str] = Field(None, description="Company name")
