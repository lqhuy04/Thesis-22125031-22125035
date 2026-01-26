"""
Financial Analysis Routes
API endpoints for financial metrics and fundamental analysis
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.models.financial_schemas import (
    FinancialRatiosSchema,
    FinancialAnalysisResponse
)
from app.models.base_schemas import success_response, error_response
from app.services.financial_db_service import FinancialDBService
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/financial", tags=["Financial Analysis"])


@router.get("/metrics/{symbol}", 
            summary="Get Financial Metrics by Symbol",
            description="Retrieve financial metrics for a specific stock symbol. Optionally filter by year.")
async def get_financial_metrics(
    symbol: str,
    year: Optional[str] = Query(None, description="Specific year (e.g., '2024')"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum number of records to return")
):
    """
    Get financial metrics for a specific stock symbol
    
    - **symbol**: Stock symbol (e.g., VNM, FPT, SSI)
    - **year**: Optional year filter (e.g., '2024', '2023')
    - **limit**: Optional limit on number of records returned (default: all)
    
    Returns financial metrics including:
    - Valuation metrics (P/E, P/B, EPS, Market Cap)
    - Profitability metrics (ROE, Gross Margin)
    - Growth metrics (Revenue YoY, EPS YoY)
    - Leverage metrics (Debt/Equity, Current Ratio)
    - Cash flow metrics (FCF, EV/EBITDA)
    """
    request_id = str(uuid.uuid4())
    
    try:
        # Validate symbol
        if not symbol or len(symbol) > 10:
            raise HTTPException(
                status_code=400,
                detail="Invalid symbol format"
            )
        
        # Fetch data from database
        metrics_data = await FinancialDBService.get_financial_metrics_by_symbol(
            symbol=symbol.upper(),
            year=year,
            limit=limit
        )
        
        if not metrics_data:
            raise HTTPException(
                status_code=404,
                detail=f"No financial metrics found for symbol: {symbol}"
            )
        
        return {
            "data": {
                "symbol": symbol.upper(),
                "total_records": len(metrics_data),
                "metrics": metrics_data
            },
            "errorCode": 0,
            "errorDesc": "",
            "requestId": request_id,
            "result": True
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error in get_financial_metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/metrics/{symbol}/latest",
            summary="Get Latest Financial Metrics",
            description="Retrieve the most recent financial metrics for a stock symbol")
async def get_latest_metrics(symbol: str):
    """
    Get the most recent financial metrics for a stock symbol
    
    - **symbol**: Stock symbol (e.g., VNM, FPT, SSI)
    
    Returns the latest year's financial metrics
    """
    request_id = str(uuid.uuid4())
    
    try:
        # Fetch latest data
        latest_data = await FinancialDBService.get_latest_financial_metrics(symbol.upper())
        
        if not latest_data:
            raise HTTPException(
                status_code=404,
                detail=f"No financial metrics found for symbol: {symbol}"
            )
        
        return {
            "data": {
                "symbol": symbol.upper(),
                "metrics": latest_data
            },
            "errorCode": 0,
            "errorDesc": "",
            "requestId": request_id,
            "result": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_latest_metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/metrics/{symbol}/years",
            summary="Get Available Years",
            description="Get list of years with available financial data for a symbol")
async def get_available_years(symbol: str):
    """
    Get list of available years for a stock symbol
    
    - **symbol**: Stock symbol (e.g., VNM, FPT, SSI)
    
    Returns list of years that have financial data available
    """
    request_id = str(uuid.uuid4())
    
    try:
        years = await FinancialDBService.get_available_years(symbol.upper())
        
        if not years:
            raise HTTPException(
                status_code=404,
                detail=f"No financial data found for symbol: {symbol}"
            )
        
        return {
            "data": {
                "symbol": symbol.upper(),
                "years": years,
                "total_years": len(years)
            },
            "errorCode": 0,
            "errorDesc": "",
            "requestId": request_id,
            "result": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_available_years: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/analysis/{symbol}",
            summary="Get Comprehensive Financial Analysis",
            description="Get a comprehensive financial analysis with formatted metrics")
async def get_financial_analysis(
    symbol: str,
    year: Optional[str] = Query(None, description="Specific year for analysis")
):
    """
    Get comprehensive financial analysis for a stock
    
    - **symbol**: Stock symbol (e.g., VNM, FPT, SSI)
    - **year**: Optional year (defaults to latest available)
    
    Returns structured financial analysis with all key metrics
    """
    request_id = str(uuid.uuid4())
    
    try:
        # Get data from database
        if year:
            metrics_data = await FinancialDBService.get_financial_metrics_by_symbol(
                symbol=symbol.upper(),
                year=year,
                limit=1
            )
            data = metrics_data[0] if metrics_data else None
        else:
            data = await FinancialDBService.get_latest_financial_metrics(symbol.upper())
        
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No financial data found for {symbol}" + (f" in {year}" if year else "")
            )
        
        # Build metrics schema
        metrics = FinancialRatiosSchema(
            pe_ratio=data.get("pe_ratio"),
            pb_ratio=data.get("pb_ratio"),
            eps=data.get("eps"),
            market_cap_billion=data.get("market_cap"),
            shares_outstanding_million=data.get("shares_outstanding"),
            roe=data.get("roe"),
            gross_margin=data.get("gross_margin"),
            revenue_yoy=data.get("revenue_yoy"),
            eps_yoy=data.get("eps_yoy"),
            debt_to_equity=data.get("debt_to_equity"),
            current_ratio=data.get("current_ratio"),
            fcf=data.get("fcf"),
            ev_ebitda=data.get("ev_ebitda"),
            beta=data.get("beta")
        )
        
        # Build response data
        analysis_data = {
            "symbol": symbol.upper(),
            "company_name": data.get("company_name"),
            "analysis_date": datetime.now().isoformat(),
            "year": data.get("year"),
            "metrics": metrics.model_dump(),
            "data_source": data.get("data_source", "SSI iBoard")
        }
        
        return success_response(data=analysis_data, request_id=request_id)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_financial_analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
