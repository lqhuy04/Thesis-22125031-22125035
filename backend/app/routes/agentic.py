"""
routes/agentic.py
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.models.base_schemas import success_response, error_response
from app.models.agentic_schemas import StockAnalysisRequest, ChatRequest
from app.models.backtest_pipeline_schemas import BacktestPipelineRequest
from app.services.backtest_pipeline_service import run_backtest_pipeline
from app.services.agentic_service import run_chat, run_stock_analysis

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
            mode=body.mode,
            symbol=body.symbol,
            risk_appetite=body.risk_appetite.model_dump(),
            plan=body.plan,
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
            "reply": result,
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


@router.post(
    "/backtest",
    summary="Backtest LLM pipeline",
    description=(
        "Chay backtest end-to-end voi LLM, goi technical + article + fundamental + aggregator "
        "tren du lieu lich su, chi goi LLM tai cac ngay co tin hieu ky thuat."
    ),
)
async def backtest_pipeline(body: BacktestPipelineRequest):
    try:
        result = run_backtest_pipeline(body)
        return success_response(data=result)

    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(error_code=400001, error_desc=str(e)),
        )
    except RuntimeError as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(error_code=500001, error_desc=str(e)),
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(error_code=500001, error_desc=f"Loi he thong: {e}"),
        )


# ─── Xóa session ─────────────────────────────────────────────────────────────

# @router.delete(
#     "/chat/session/{session_id}",
#     summary="Xóa session chat",
#     description="Xóa toàn bộ lịch sử hội thoại của một session. Gọi khi user thoát màn hình chatbot.",
# )
# async def remove_session(session_id: str):
#     try:
#         delete_session(session_id)
#         return success_response(data={"session_id": session_id})

#     except Exception as e:
#         return JSONResponse(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             content=error_response(error_code=500, error_desc=f"Lỗi hệ thống: {e}"),
#         )