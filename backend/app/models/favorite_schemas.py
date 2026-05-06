"""
Favorite Schemas
Pydantic models for the flat favorite table.
"""
from pydantic import BaseModel, Field


class FavoriteCreateRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=64, description="Stock symbol (e.g. VNM)")
    # `user_id` is derived from the bearer token; do not include in request body


class FavoriteData(BaseModel):
    id: str
    stock_id: str
    user_id: str
    symbol: str
    company_name: str
    exchange: str
