"""
routes/agentic.py
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.models.base_schemas import success_response, error_response
from app.models.agentic_schemas import StockAnalysisRequest, ChatRequest, ChatResponse
from app.services.agentic_service import run_stock_analysis, run_chat

router = APIRouter(prefix="/api/agentic", tags=["agentic-ai"])


# ─── API mode: structured output ─────────────────────────────────────────────

@router.post(
    "/analyze",
    summary="Phân tích cổ phiếu",
    description="Chạy full pipeline: tin tức + cơ bản + kỹ thuật → structured output. Không có memory.",
)
async def analyze_stock(body: StockAnalysisRequest):
    try:
        recommendation = run_stock_analysis(
            symbol=body.symbol,
            risk_appetite=body.risk_appetite.model_dump(),
            user_input=body.user_input,
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


# ─── Chatbot mode: plain text + memory ───────────────────────────────────────

@router.post(
    "/chat",
    summary="Chat với AI phân tích chứng khoán",
    description=(
        "Gửi tin nhắn và nhận phản hồi dạng text. "
        "Giữ nguyên session_id giữa các lần gọi để duy trì lịch sử hội thoại. "
        "risk_appetite chỉ cần gửi ở turn đầu tiên."
    ),
)
async def chat(body: ChatRequest):
    try:
        result = run_chat(
            session_id=body.session_id,
            message=body.message,
            risk_appetite=body.risk_appetite.model_dump() if body.risk_appetite else None,
        )
        return success_response(data={
            "session_id": body.session_id,
            "reply": result["reply"],
        })

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