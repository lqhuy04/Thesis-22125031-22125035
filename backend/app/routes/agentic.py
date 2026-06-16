"""
routes/agentic.py
"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.middleware.auth_middleware import get_current_user
from app.models.base_schemas import success_response, error_response
from app.models.agentic_schemas import StockAnalysisRequest, ChatRequest
from app.models.backtest_pipeline_schemas import BacktestPipelineRequest
from app.services.backtest_pipeline_service import run_backtest_pipeline
from app.services.agentic_service import (
    run_chat,
    run_stock_analysis,
    list_chat_sessions,
    get_chat_history,
    delete_chat_session,
)

router = APIRouter(prefix="/api/agentic", tags=["agentic-ai"])


# ─── API mode: structured output ─────────────────────────────────────────────

@router.post(
    "/analyze",
    summary="Phân tích cổ phiếu",
    description="Chạy full pipeline: tin tức + cơ bản + kỹ thuật → structured output. Không có memory.",
)
async def analyze_stock(body: StockAnalysisRequest, current_user: dict = Depends(get_current_user)):
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
        "Gửi tin nhắn và nhận phản hồi dạng text. Yêu cầu đăng nhập. "
        "Giữ nguyên session_id giữa các lần gọi để duy trì lịch sử hội thoại."
    ),
)
async def chat(body: ChatRequest, current_user: dict = Depends(get_current_user)):
    try:
        result = run_chat(
            session_id=body.session_id,
            message=body.message,
            user_id=current_user["user_id"],
        )
        return success_response(data={
            "session_id": body.session_id,
            "reply": result,
        })

    except PermissionError as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=error_response(error_code=403001, error_desc=str(e)),
        )
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


@router.get(
    "/chat/sessions",
    summary="Danh sách cuộc trò chuyện của user",
    description="Trả về danh sách session chat của người dùng đang đăng nhập, mới nhất trước.",
)
async def chat_sessions(current_user: dict = Depends(get_current_user)):
    try:
        data = list_chat_sessions(user_id=current_user["user_id"])
        return success_response(data=data)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(error_code=500, error_desc=f"Lỗi hệ thống: {e}"),
        )


@router.get(
    "/chat/history/{session_id}",
    summary="Lịch sử tin nhắn của một cuộc trò chuyện",
    description="Trả về toàn bộ tin nhắn (role + content) của một session, kiểm tra quyền sở hữu.",
)
async def chat_history(session_id: str, current_user: dict = Depends(get_current_user)):
    try:
        data = get_chat_history(session_id=session_id, user_id=current_user["user_id"])
        return success_response(data={"session_id": session_id, "messages": data})

    except PermissionError as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=error_response(error_code=403001, error_desc=str(e)),
        )
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(error_code=404001, error_desc=str(e)),
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(error_code=500, error_desc=f"Lỗi hệ thống: {e}"),
        )


@router.delete(
    "/chat/session/{session_id}",
    summary="Xóa một cuộc trò chuyện",
    description="Xóa session và toàn bộ lịch sử hội thoại, kiểm tra quyền sở hữu.",
)
async def remove_chat_session(session_id: str, current_user: dict = Depends(get_current_user)):
    try:
        delete_chat_session(session_id=session_id, user_id=current_user["user_id"])
        return success_response(data={"session_id": session_id})

    except PermissionError as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=error_response(error_code=403001, error_desc=str(e)),
        )
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(error_code=404001, error_desc=str(e)),
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


@router.get(
    "/backtests",
    summary="Danh sách kết quả backtest từ Supabase Storage",
)
async def list_backtests():
    try:
        from app.utils.supabase_storage import list_backtest_files
        res = list_backtest_files()
        return success_response(data=res)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(error_code=500001, error_desc=f"Loi lay danh sach: {e}"),
        )