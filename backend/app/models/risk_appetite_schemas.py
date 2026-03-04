"""
Risk Appetite Schemas
Pydantic models for risk appetite API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional


class RiskAppetiteRequest(BaseModel):
    experience: Optional[str] = Field(None, description="Investment experience level")
    expectation: Optional[str] = Field(None, description="Return expectation")
    period: Optional[str] = Field(None, description="Investment period / time horizon")
    comfort_zone: Optional[str] = Field(None, description="Risk comfort zone")
    capital_ratio: Optional[str] = Field(None, description="Capital ratio for investment")


class RiskAppetiteData(BaseModel):
    id: Optional[str] = None
    userId: Optional[str] = None
    experience: Optional[str] = None
    expectation: Optional[str] = None
    period: Optional[str] = None
    comfort_zone: Optional[str] = None
    capital_ratio: Optional[str] = None
