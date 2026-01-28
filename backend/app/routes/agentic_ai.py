"""
Agentic AI Analysis Routes
API endpoints for AI-powered stock analysis
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models.base_schemas import success_response, error_response
from app.services.financial_db_service import FinancialDBService
from app.services.ssi_service import SSIService
from app.services.agentic_ai_service import AgenticAIService
from datetime import datetime, timedelta
import uuid

router = APIRouter(prefix="/api/agentic-ai", tags=["Agentic AI Analysis"])


@router.get("/test/analyze/{symbol}", 
            summary="AI-Powered Stock Analysis (Test with Hard-coded Data)",
            description="Test endpoint using hard-coded data for VNM stock")
async def test_analyze_stock(symbol: str):
    """
    Test endpoint with hard-coded data
    
    - **symbol**: Stock symbol (currently only supports VNM for testing)
    
    Returns AI analysis based on hard-coded sample data
    """
    request_id = str(uuid.uuid4())
    
    try:
        symbol = symbol.upper()
        
        # Hard-coded financial metrics (từ file main.py gốc)
        metrics_data = [
            {
                "pe_ratio": 14.54,
                "pb_ratio": 3.38,
                "eps": 4022.0,
                "market_cap_billion": 122239.4,
                "shares_outstanding_million": 2089.96,
                "roe": 25.96,
                "gross_margin": 41.42,
                "net_margin": None,
                "roa": None,
                "revenue_yoy": 2.34,
                "eps_yoy": 5.95,
                "profit_yoy": None,
                "debt_to_equity": 0.52,
                "current_ratio": 2.03,
                "ev_ebitda": 11.11,
                "bvps": None,
                "fcf": 5946.85,
                "beta": None
            }
        ]
        
        # Hard-coded price data (từ file main.py gốc)
        price_data = [
            {
                "TradingDate": "29/12/2025",
                "Time": None,
                "Open": "61500",
                "High": "62200",
                "Low": "61400",
                "Close": "62100",
                "Volume": "1943000",
                "Value": "120157180000"
            },
            {
                "TradingDate": "30/12/2025",
                "Time": None,
                "Open": "62100",
                "High": "62300",
                "Low": "61700",
                "Close": "61800",
                "Volume": "1581000",
                "Value": "97858410000"
            },
            {
                "TradingDate": "31/12/2025",
                "Time": None,
                "Open": "61900",
                "High": "62000",
                "Low": "61200",
                "Close": "61200",
                "Volume": "1879600",
                "Value": "115569960000"
            },
            {
                "TradingDate": "05/01/2026",
                "Time": None,
                "Open": "61300",
                "High": "61500",
                "Low": "60000",
                "Close": "60300",
                "Volume": "2814700",
                "Value": "170865710000"
            },
            {
                "TradingDate": "06/01/2026",
                "Time": None,
                "Open": "60500",
                "High": "60900",
                "Low": "60300",
                "Close": "60800",
                "Volume": "2963300",
                "Value": "179693170000"
            },
            {
                "TradingDate": "07/01/2026",
                "Time": None,
                "Open": "60800",
                "High": "61500",
                "Low": "60500",
                "Close": "60900",
                "Volume": "3228100",
                "Value": "196941770000"
            },
            {
                "TradingDate": "08/01/2026",
                "Time": None,
                "Open": "61100",
                "High": "63400",
                "Low": "61100",
                "Close": "62200",
                "Volume": "5636400",
                "Value": "351659430000"
            },
            {
                "TradingDate": "09/01/2026",
                "Time": None,
                "Open": "62400",
                "High": "62500",
                "Low": "61000",
                "Close": "61000",
                "Volume": "4184100",
                "Value": "258465510000"
            },
            {
                "TradingDate": "12/01/2026",
                "Time": None,
                "Open": "61100",
                "High": "62700",
                "Low": "61100",
                "Close": "62700",
                "Volume": "4146300",
                "Value": "257857700000"
            },
            {
                "TradingDate": "13/01/2026",
                "Time": None,
                "Open": "62900",
                "High": "64900",
                "Low": "62800",
                "Close": "63300",
                "Volume": "6761300",
                "Value": "430840390000"
            },
            {
                "TradingDate": "14/01/2026",
                "Time": None,
                "Open": "63600",
                "High": "67700",
                "Low": "63400",
                "Close": "67700",
                "Volume": "24838300",
                "Value": "1662222120000"
            },
            {
                "TradingDate": "15/01/2026",
                "Time": None,
                "Open": "70000",
                "High": "72400",
                "Low": "69500",
                "Close": "71000",
                "Volume": "19260600",
                "Value": "1377961380000"
            },
            {
                "TradingDate": "16/01/2026",
                "Time": None,
                "Open": "71100",
                "High": "73000",
                "Low": "69100",
                "Close": "69600",
                "Volume": "13372500",
                "Value": "944442320000"
            },
            {
                "TradingDate": "19/01/2026",
                "Time": None,
                "Open": "69800",
                "High": "71000",
                "Low": "68300",
                "Close": "70600",
                "Volume": "10385300",
                "Value": "722125070000"
            },
            {
                "TradingDate": "20/01/2026",
                "Time": None,
                "Open": "71500",
                "High": "75500",
                "Low": "71100",
                "Close": "73400",
                "Volume": "21521900",
                "Value": "1596348490000"
            },
            {
                "TradingDate": "21/01/2026",
                "Time": None,
                "Open": "73000",
                "High": "73000",
                "Low": "70000",
                "Close": "70300",
                "Volume": "11234100",
                "Value": "800042790000"
            },
            {
                "TradingDate": "22/01/2026",
                "Time": None,
                "Open": "71100",
                "High": "72800",
                "Low": "70000",
                "Close": "70900",
                "Volume": "8055200",
                "Value": "573373780000"
            },
            {
                "TradingDate": "23/01/2026",
                "Time": None,
                "Open": "69400",
                "High": "70100",
                "Low": "67200",
                "Close": "67200",
                "Volume": "16050400",
                "Value": "1097314610000"
            },
            {
                "TradingDate": "26/01/2026",
                "Time": None,
                "Open": "67400",
                "High": "69300",
                "Low": "67400",
                "Close": "68900",
                "Volume": "8864800",
                "Value": "607858160000"
            },
            {
                "TradingDate": "27/01/2026",
                "Time": None,
                "Open": "68400",
                "High": "68600",
                "Low": "66100",
                "Close": "67700",
                "Volume": "8357800",
                "Value": "562221360000"
            },
            {
                "TradingDate": "28/01/2026",
                "Time": None,
                "Open": "67700",
                "High": "69500",
                "Low": "67200",
                "Close": "68000",
                "Volume": "6303300",
                "Value": "429824490000"
            }
        ]
        
        # Run AI analysis
        analysis_result = await AgenticAIService.analyze_stock(
            symbol=symbol,
            metrics=metrics_data,
            price_data=price_data
        )
        
        return {
            "data": {
                "symbol": symbol,
                "fundamental_analysis": analysis_result["fundamental_analysis"],
                "technical_analysis": analysis_result["technical_analysis"],
                "final_report": analysis_result["final_report"],
                "data_sources": {
                    "metrics_count": len(metrics_data),
                    "price_data_count": len(price_data),
                    "note": "Using hard-coded test data"
                }
            },
            "errorCode": 0,
            "errorDesc": "",
            "requestId": request_id,
            "result": True
        }
        
    except Exception as e:
        print(f"Error in test_analyze_stock: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during AI analysis: {str(e)}"
        )


@router.get("/analyze/{symbol}", 
            summary="AI-Powered Stock Analysis",
            description="Get comprehensive AI analysis combining fundamental and technical analysis")
async def analyze_stock(
    symbol: str,
    year: Optional[str] = Query(None, description="Year for fundamental data (e.g., '2024')"),
    days: Optional[int] = Query(21, ge=1, le=90, description="Number of days for price data (default: 21)")
):
    """
    Get AI-powered comprehensive stock analysis
    
    This endpoint combines:
    - **Fundamental Analysis**: Based on financial metrics (P/E, ROE, debt ratios, etc.)
    - **Technical Analysis**: Based on recent price movements and volume
    - **Final Report**: AI-generated investment recommendation
    
    Parameters:
    - **symbol**: Stock symbol (e.g., VNM, FPT, SSI)
    - **year**: Optional year for fundamental data (uses latest if not specified)
    - **days**: Number of days of price data for technical analysis (default: 21, max: 90)
    
    Returns comprehensive analysis with:
    - Fundamental analysis insights
    - Technical analysis insights
    - Combined investment recommendation
    """
    request_id = str(uuid.uuid4())
    
    try:
        # Validate symbol
        if not symbol or len(symbol) > 10:
            raise HTTPException(
                status_code=400,
                detail="Invalid symbol format"
            )
        
        symbol = symbol.upper()
        
        # 1. Fetch fundamental data (financial metrics)
        metrics_data = await FinancialDBService.get_financial_metrics_by_symbol(
            symbol=symbol,
            year=year,
            limit=1  # Get latest record
        )
        
        if not metrics_data:
            raise HTTPException(
                status_code=404,
                detail=f"No financial metrics found for symbol: {symbol}"
            )
        
        # 2. Fetch technical data (price history)
        price_data = []
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 10)  # Add buffer for weekends/holidays
            
            # Fetch price data from SSI
            price_response = await SSIService.get_historical_price(
                symbol=symbol,
                from_date=start_date.strftime("%d/%m/%Y"),
                to_date=end_date.strftime("%d/%m/%Y")
            )
            
            if price_response and "data" in price_response:
                raw_price_data = price_response["data"]
                # Take only the requested number of days
                price_data = raw_price_data[:days] if len(raw_price_data) > days else raw_price_data
                
                # Remove Symbol and Market fields from each record
                price_data = [
                    {k: v for k, v in record.items() if k not in ["Symbol", "Market"]}
                    for record in price_data
                ]
        except Exception as e:
            # If price data fetch fails, continue without it
            print(f"Warning: Could not fetch price data: {e}")
            price_data = []
        
        # 3. Run AI analysis
        analysis_result = await AgenticAIService.analyze_stock(
            symbol=symbol,
            metrics=metrics_data,
            price_data=price_data
        )
        
        return {
            "data": {
                "symbol": symbol,
                "fundamental_analysis": analysis_result["fundamental_analysis"],
                "technical_analysis": analysis_result["technical_analysis"],
                "final_report": analysis_result["final_report"],
                "data_sources": {
                    "metrics_count": len(metrics_data),
                    "price_data_count": len(price_data)
                }
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
        print(f"Error in analyze_stock: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during AI analysis"
        )


@router.get("/analyze/{symbol}/fundamental-only", 
            summary="AI Fundamental Analysis Only",
            description="Get AI-powered fundamental analysis without technical analysis")
async def analyze_fundamental_only(
    symbol: str,
    year: Optional[str] = Query(None, description="Year for fundamental data")
):
    """
    Get AI-powered fundamental analysis only
    
    - **symbol**: Stock symbol (e.g., VNM, FPT, SSI)
    - **year**: Optional year filter
    
    Returns only fundamental analysis based on financial metrics
    """
    request_id = str(uuid.uuid4())
    
    try:
        symbol = symbol.upper()
        
        # Fetch fundamental data
        metrics_data = await FinancialDBService.get_financial_metrics_by_symbol(
            symbol=symbol,
            year=year,
            limit=1
        )
        
        if not metrics_data:
            raise HTTPException(
                status_code=404,
                detail=f"No financial metrics found for symbol: {symbol}"
            )
        
        # Run AI analysis (fundamental only)
        analysis_result = await AgenticAIService.analyze_stock(
            symbol=symbol,
            metrics=metrics_data,
            price_data=None  # No technical analysis
        )
        
        return {
            "data": {
                "symbol": symbol,
                "fundamental_analysis": analysis_result["fundamental_analysis"],
                "metrics_count": len(metrics_data)
            },
            "errorCode": 0,
            "errorDesc": "",
            "requestId": request_id,
            "result": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in analyze_fundamental_only: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
