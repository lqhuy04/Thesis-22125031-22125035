"""
Company Profile Routes
GET endpoints for company profiles, leaders, and subsidiaries.
"""
from fastapi import APIRouter, HTTPException, Depends
from uuid import uuid4
from app.services.company_service import CompanyService
from app.middleware.auth_middleware import get_current_user
from app.models.company_schemas import (
    CompanyProfileAPIResponse,
    LeadersAPIResponse,
    SubsidiariesAPIResponse,
)

router = APIRouter(prefix="/api/company", tags=["Company Profile"], dependencies=[Depends(get_current_user)])


@router.get("/{symbol}/profile", response_model=CompanyProfileAPIResponse)
def get_company_profile(symbol: str):
    """Get company profile by stock symbol (e.g. VNM, ACB)."""
    data = CompanyService.get_profile(symbol)
    if not data:
        raise HTTPException(status_code=404, detail=f"Company profile not found for symbol '{symbol.upper()}'")
    return CompanyProfileAPIResponse(data=data, requestId=str(uuid4()))


@router.get("/{symbol}/leaders", response_model=LeadersAPIResponse)
def get_company_leaders(symbol: str):
    """Get leadership board (Ban lãnh đạo) for a stock symbol."""
    data = CompanyService.get_leaders(symbol)
    return LeadersAPIResponse(data=data, requestId=str(uuid4()))


@router.get("/{symbol}/subsidiaries", response_model=SubsidiariesAPIResponse)
def get_company_subsidiaries(symbol: str):
    """Get subsidiaries and associates (Công ty con / liên kết) for a stock symbol."""
    data = CompanyService.get_subsidiaries(symbol)
    return SubsidiariesAPIResponse(data=data, requestId=str(uuid4()))
