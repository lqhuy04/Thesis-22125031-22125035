"""
Search history schemas.
"""
from pydantic import BaseModel, Field


class SearchHistoryCreateRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=64, description="Stock symbol (e.g. VNM)")


class SearchHistoryItem(BaseModel):
    symbol: str = Field(..., description="Stock symbol")
    company_name: str = Field("", description="Company name")
    current_price: float = Field(0.0, description="Current price")
    per_price_change: float = Field(0.0, description="Percent price change")