"""
routes/agentic.py
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.models.base_schemas import success_response, error_response
from app.models.agentic_schemas import StockAnalysisRequest
from app.services.agentic_service import run_stock_analysis

router = APIRouter(prefix="/api/agentic", tags=["agentic-ai"])


@router.post(
    "/analyze",
    summary="Phân tích cổ phiếu",
    description="Chạy multi-agent pipeline: thu thập tin tức, phân tích cơ bản và kỹ thuật.",
)
async def analyze_stock(body: StockAnalysisRequest):
    try:
        recommendation = run_stock_analysis(
            symbol=body.symbol,
            risk_appetite=body.risk_appetite.model_dump(),
        )
        
        return success_response(data=recommendation)

    except RuntimeError as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(error_code=500, error_desc=str(e)),
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(error_code=500, error_desc=f"Lỗi hệ thống: {e}"),
        )