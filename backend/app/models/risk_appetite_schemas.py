"""
Risk Appetite Schemas
Pydantic models for risk appetite API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class InvestmentPeriod(str, Enum):
    short_term = "short_term"
    mid_term = "mid_term"
    long_term = "long_term"


class RiskAppetiteRequest(BaseModel):
    period: InvestmentPeriod = Field(..., description="Investment period / time horizon")


class RiskAppetiteData(BaseModel):
    id: Optional[str] = None
    userId: Optional[str] = None
    period: Optional[str] = None
