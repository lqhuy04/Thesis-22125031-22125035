"""
Agentic AI Analysis Routes
API endpoints for AI-powered stock analysis
Uses the AgenticAI workflow (Fundamental, Technical, News, RiskAppetite → Summary)
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models.base_schemas import success_response, error_response
from app.services.ssi_service import SSIService
from app.services.agentic_ai_service import AgenticAIService
from datetime import datetime, timedelta
import uuid

router = APIRouter(prefix="/api/analysis", tags=["AI Analysis"])


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

        # Re-use mock data defined in the AgenticAI module
        from app.services.agentic_ai_service import _agentic_module
        mock_price_data = _agentic_module.mock_price_data
        mock_news_data = _agentic_module.mock_news_data

        # Run the full AgenticAI workflow
        analysis_result = await AgenticAIService.analyze_stock(
            symbol=symbol,
            company_name="Công ty cổ phần Sữa Việt Nam" if symbol == "VNM" else symbol,
            price_data=mock_price_data,
            news_data=mock_news_data,
        )

        return {
            "data": {
                "symbol": symbol,
                "fundamental_analysis": analysis_result["fundamental_analysis"],
                "technical_analysis": analysis_result["technical_analysis"],
                "news_analysis": analysis_result["news_analysis"],
                "recommendation": analysis_result["recommendation"],
                "confidence": analysis_result["confidence"],
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


@router.get("/{symbol}", 
            summary="AI-Powered Stock Analysis",
            description="Get comprehensive AI analysis combining fundamental, technical, news, and risk analysis")
async def analyze_stock(
    symbol: str,
    year: Optional[str] = Query(None, description="Year for fundamental data (e.g., '2024')"),
    days: Optional[int] = Query(21, ge=1, le=90, description="Number of days for price data (default: 21)")
):
    """
    Get AI-powered comprehensive stock analysis

    This endpoint runs the AgenticAI workflow which combines:
    - **Fundamental Analysis**: Company financial health
    - **Technical Analysis**: Price trends and signals
    - **News Analysis**: Recent news sentiment
    - **Risk Appetite**: User risk profile evaluation
    - **Summary / Recommendation**: AI-generated investment recommendation

    Parameters:
    - **symbol**: Stock symbol (e.g., VNM, FPT, SSI)
    - **year**: Optional year for fundamental data (uses latest if not specified)
    - **days**: Number of days of price data for technical analysis (default: 21, max: 90)
    """
    request_id = str(uuid.uuid4())

    try:
        if not symbol or len(symbol) > 10:
            raise HTTPException(status_code=400, detail="Invalid symbol format")

        symbol = symbol.upper()

        # 1. Fetch price data from SSI for technical analysis
        price_data = []
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 10)

            price_response = await SSIService.get_historical_price(
                symbol=symbol,
                from_date=start_date.strftime("%d/%m/%Y"),
                to_date=end_date.strftime("%d/%m/%Y")
            )

            if price_response and "data" in price_response:
                raw_price_data = price_response["data"]
                price_data = raw_price_data[:days] if len(raw_price_data) > days else raw_price_data
                price_data = [
                    {k: v for k, v in record.items() if k not in ["Symbol", "Market"]}
                    for record in price_data
                ]
        except Exception as e:
            print(f"Warning: Could not fetch price data: {e}")

        # 2. Fetch news data (placeholder – extend with a real news service when available)
        news_data: list = []

        # 3. Run the AgenticAI workflow
        analysis_result = await AgenticAIService.analyze_stock(
            symbol=symbol,
            company_name=symbol,
            price_data=price_data,
            news_data=news_data,
        )

        return {
            "data": {
                "symbol": symbol,
                "fundamental_analysis": analysis_result["fundamental_analysis"],
                "technical_analysis": analysis_result["technical_analysis"],
                "news_analysis": analysis_result["news_analysis"],
                "recommendation": analysis_result["recommendation"],
                "confidence": analysis_result["confidence"],
            },
            "errorCode": 0,
            "errorDesc": "",
            "requestId": request_id,
            "result": True
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in analyze_stock: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during AI analysis"
        )
