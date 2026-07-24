"""
Financial Analysis Routes
API endpoints for financial metrics and fundamental analysis
"""
from fastapi import APIRouter, HTTPException, Query, Depends

from app.models.base_schemas import success_response
from app.services.fundamental_analysis_service import FundamentalAnalysisService
from app.middleware.auth_middleware import get_current_user
import uuid

router = APIRouter(prefix="/api/fundamental-analysis", tags=["Fundamental Metrics"], dependencies=[Depends(get_current_user)])

@router.get("/{symbol}/cash-flows", summary="Get Cash Flows")
def get_cash_flows(symbol: str):
    try:
        data = FundamentalAnalysisService.get_cash_flows(symbol)
        return success_response(data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}/financial-indicators", summary="Get Financial Indicators")
def get_financial_indicators(symbol: str):
    try:
        data = FundamentalAnalysisService.get_indicators(symbol)
        return success_response(data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}/income-statements", summary="Get Income Statements")
def get_income_statements(symbol: str):
    try:
        data = FundamentalAnalysisService.get_income_statements(symbol)
        return success_response(data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/summary",
            summary="Get Fundamental Summary",
            description="Get AI-generated fundamental analysis summary for a stock symbol")
def get_fundamental_summary(symbol: str):
    request_id = str(uuid.uuid4())

    try:
        if not symbol or len(symbol) > 10:
            raise HTTPException(
                status_code=400,
                detail="Invalid symbol format"
            )

        summary_data = FundamentalAnalysisService.get_summary(symbol.upper())

        if not summary_data:
            raise HTTPException(
                status_code=404,
                detail=f"No fundamental summary found for symbol: {symbol}"
            )

        return success_response(data=summary_data, request_id=request_id)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_fundamental_summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
