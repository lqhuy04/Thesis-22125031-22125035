"""
Company profile data models and schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CompanyProfileResponse(BaseModel):
    symbol: str
    company_name: Optional[str] = None

    # Tab: Giới thiệu
    description: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    fax: Optional[str] = None

    # Tab: TT cơ bản
    sic_code: Optional[str] = None
    industry_name: Optional[str] = None
    icb_code: Optional[str] = None
    founded_date: Optional[str] = None
    charter_capital_billion: Optional[float] = None
    employee_count: Optional[int] = None
    branch_count: Optional[int] = None

    # Tab: TT niêm yết
    listing_date: Optional[str] = None
    exchange: Optional[str] = None
    ipo_price: Optional[float] = None
    listed_volume: Optional[int] = None
    market_cap_billion: Optional[float] = None
    shares_outstanding: Optional[int] = None

    data_source: Optional[str] = None
    crawled_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LeaderResponse(BaseModel):
    symbol: str
    full_name: Optional[str] = None
    position: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubsidiaryResponse(BaseModel):
    symbol: str
    company_name: Optional[str] = None
    sub_symbol: Optional[str] = None
    charter_capital_billion: Optional[float] = None
    ownership_pct: Optional[float] = None
    relationship_type: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Envelope responses ──────────────────────────────────────

class CompanyProfileAPIResponse(BaseModel):
    data: CompanyProfileResponse
    errorCode: int = Field(default=0)
    errorDesc: str = Field(default="")
    requestId: str = Field(default="")
    result: bool = Field(default=True)


class LeadersAPIResponse(BaseModel):
    data: list[LeaderResponse]
    errorCode: int = Field(default=0)
    errorDesc: str = Field(default="")
    requestId: str = Field(default="")
    result: bool = Field(default=True)


class SubsidiariesAPIResponse(BaseModel):
    data: list[SubsidiaryResponse]
    errorCode: int = Field(default=0)
    errorDesc: str = Field(default="")
    requestId: str = Field(default="")
    result: bool = Field(default=True)
