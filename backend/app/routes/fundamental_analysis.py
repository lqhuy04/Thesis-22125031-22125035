"""
Financial Analysis Routes
API endpoints for financial metrics and fundamental analysis
"""
from fastapi import APIRouter, HTTPException, Query

from app.models.base_schemas import success_response
from app.services.fundamental_analysis_service import FundamentalAnalysisService
import uuid

router = APIRouter(prefix="/api/fundamental-analysis", tags=["Fundamental Metrics"])

@router.get("/{symbol}/balance-sheets", summary="Get Balance Sheets")
async def get_balance_sheets(symbol: str):
    try:
        data = await FundamentalAnalysisService.get_balance_sheets(symbol)
        return success_response(data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}/cash-flows", summary="Get Cash Flows")
async def get_cash_flows(symbol: str):
    try:
        data = await FundamentalAnalysisService.get_cash_flows(symbol)
        return success_response(data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}/financial-indicators", summary="Get Financial Indicators")
async def get_financial_indicators(symbol: str):
    try:
        data = await FundamentalAnalysisService.get_indicators(symbol)
        return success_response(data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}/income-statements", summary="Get Income Statements")
async def get_income_statements(symbol: str):
    try:
        data = await FundamentalAnalysisService.get_income_statements(symbol)
        return success_response(data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/summary",
            summary="Get Fundamental Summary",
            description="Get AI-generated fundamental analysis summary for a stock symbol")
async def get_fundamental_summary(symbol: str):
    request_id = str(uuid.uuid4())

    try:
        if not symbol or len(symbol) > 10:
            raise HTTPException(
                status_code=400,
                detail="Invalid symbol format"
            )

        summary_data = await FundamentalAnalysisService.get_summary(symbol.upper())

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
