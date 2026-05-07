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


class CheckFavoriteRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=64, description="Stock symbol (e.g. VNM)")


class CheckFavoriteResponse(BaseModel):
    is_favorited: bool = Field(..., description="Whether the stock is in user's favorites")
    symbol: str = Field(..., description="Stock symbol")
