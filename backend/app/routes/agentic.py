"""
routes/agentic.py
"""

import logging
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Path as ApiPath, Request, status
from fastapi.responses import FileResponse, JSONResponse, Response

from app.middleware.auth_middleware import get_current_user, get_current_admin
from app.models.base_schemas import success_response, error_response
from app.models.agentic_schemas import StockAnalysisRequest, ChatRequest, ChatSeedRequest, AdminAnalysisRequest
from app.models.backtest_pipeline_schemas import BacktestPipelineRequest
from app.services.backtest_pipeline_service import run_backtest_pipeline
from app.utils.rate_limit import enforce_rate_limit
from app.services.agentic_service import (
    run_chat,
    seed_chat_session,
    run_stock_analysis,
    run_admin_analysis,
    list_chat_sessions,
    get_chat_history,
    delete_chat_session,
)

router = APIRouter(prefix="/api/agentic", tags=["agentic-ai"])
logger = logging.getLogger(__name__)
_BACKTEST_FILENAME = re.compile(r"^[A-Za-z0-9._-]{1,160}_backtest\.json$")
_LOCAL_BACKTEST_DIR = Path(__file__).resolve().parents[1] / "backtest" / "visualizations"


def _internal_error_response():
    logger.exception("Unhandled agentic API error")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            error_code=500001, error_desc="Internal server error"
        ),
    )


async def _limit_ai(
    request: Request, current_user: dict = Depends(get_current_user)
):
    await enforce_rate_limit(
        "agentic-ai", current_user["user_id"], limit=30, window_seconds=60
    )


async def _limit_admin_ai(
    request: Request, current_admin: dict = Depends(get_current_admin)
):
    await enforce_rate_limit(
        "agentic-admin-ai",
        current_admin["user_id"],
        limit=120,
        window_seconds=600,
    )


async def _limit_backtest(
    request: Request, current_admin: dict = Depends(get_current_admin)
):
    await enforce_rate_limit(
        "agentic-backtest",
        current_admin["user_id"],
        limit=40,
        window_seconds=3600,
    )


# ─── API mode: structured output ─────────────────────────────────────────────

@router.post(
    "/analyze",
    summary="Phân tích cổ phiếu",
    description="Chạy full pipeline: tin tức + cơ bản + kỹ thuật → structured output. Không có memory.",
)
def analyze_stock(
    body: StockAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    _rate_limit: None = Depends(_limit_ai),
):
    try:
        recommendation = run_stock_analysis(
            mode=body.mode,
            symbol=body.symbol,
            risk_appetite=body.risk_appetite.model_dump(),
            data_selection=body.data_selection.model_dump(),
        )
        return success_response(data=recommendation)

    except RuntimeError:
        return _internal_error_response()
    except Exception:
        return _internal_error_response()


# ─── Admin API mode: structured output, role = admin only ────────────────────

@router.post(
    "/admin-analyze",
    summary="Phân tích cổ phiếu (Admin)",
    description=(
        "Giống /analyze nhưng chỉ dành cho admin. Hỗ trợ chạy theo rổ chỉ số "
        "VN30 (30 mã) hoặc VN100 (100 mã); bỏ trống `universe` để phân tích 1 mã."
    ),
)
def admin_analyze(
    body: AdminAnalysisRequest,
    current_user: dict = Depends(get_current_admin),
    _rate_limit: None = Depends(_limit_admin_ai),
):
    try:
        result = run_admin_analysis(
            mode=body.mode,
            universe=body.universe,
            symbol=body.symbol,
            risk_appetite=body.risk_appetite.model_dump(),
            data_selection=body.data_selection.model_dump(),
        )
        return success_response(data=result)

    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(error_code=400001, error_desc=str(e)),
        )
    except RuntimeError:
        return _internal_error_response()
    except Exception:
        return _internal_error_response()


@router.get(
    "/admin-universe/{name}",
    summary="Danh sách mã của một rổ chỉ số (Admin)",
    description="Trả về danh sách mã cổ phiếu thuộc rổ VN30 / VN100 từ Supabase.",
)
def admin_universe(name: str, current_user: dict = Depends(get_current_admin)):
    try:
        from app.utils.market_index import get_index_symbols
        symbols = get_index_symbols(name)
        return success_response(data={
            "universe": name.strip().upper(),
            "count": len(symbols),
            "symbols": symbols,
        })
    except Exception:
        return _internal_error_response()


# ─── Chatbot mode: plain text + memory ───────────────────────────────────────

@router.post(
    "/chat",
    summary="Chat với AI phân tích chứng khoán",
    description=(
        "Gửi tin nhắn và nhận phản hồi dạng text. Yêu cầu đăng nhập. "
        "Giữ nguyên session_id giữa các lần gọi để duy trì lịch sử hội thoại."
    ),
)
def chat(
    body: ChatRequest,
    current_user: dict = Depends(get_current_user),
    _rate_limit: None = Depends(_limit_ai),
):
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
    except RuntimeError:
        return _internal_error_response()
    except Exception:
        return _internal_error_response()


@router.post(
    "/chat/seed",
    summary="Tạo phiên chat với 1 lượt phân tích có sẵn",
    description=(
        "Nạp sẵn cặp Q&A (câu hỏi + kết quả phân tích đã hiển thị ở màn AI) vào "
        "memory của một session mới. Không chạy pipeline, không gọi LLM. "
        "Sau đó client điều hướng sang màn chat và hỏi tiếp bình thường."
    ),
)
def seed_chat(
    body: ChatSeedRequest,
    current_user: dict = Depends(get_current_user),
    _rate_limit: None = Depends(_limit_ai),
):
    try:
        seed_chat_session(
            session_id=body.session_id,
            user_message=body.user_message,
            assistant_message=body.assistant_message,
            user_id=current_user["user_id"],
        )
        return success_response(data={"session_id": body.session_id})

    except PermissionError as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=error_response(error_code=403001, error_desc=str(e)),
        )
    except Exception:
        return _internal_error_response()


@router.get(
    "/chat/sessions",
    summary="Danh sách cuộc trò chuyện của user",
    description="Trả về danh sách session chat của người dùng đang đăng nhập, mới nhất trước.",
)
def chat_sessions(current_user: dict = Depends(get_current_user)):
    try:
        data = list_chat_sessions(user_id=current_user["user_id"])
        return success_response(data=data)
    except Exception:
        return _internal_error_response()


@router.get(
    "/chat/history/{session_id}",
    summary="Lịch sử tin nhắn của một cuộc trò chuyện",
    description="Trả về toàn bộ tin nhắn (role + content) của một session, kiểm tra quyền sở hữu.",
)
def chat_history(
    session_id: str = ApiPath(
        ..., min_length=36, max_length=36,
        pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$",
    ),
    current_user: dict = Depends(get_current_user),
):
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
    except Exception:
        return _internal_error_response()


@router.delete(
    "/chat/session/{session_id}",
    summary="Xóa một cuộc trò chuyện",
    description="Xóa session và toàn bộ lịch sử hội thoại, kiểm tra quyền sở hữu.",
)
def remove_chat_session(
    session_id: str = ApiPath(
        ..., min_length=36, max_length=36,
        pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$",
    ),
    current_user: dict = Depends(get_current_user),
):
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
    except Exception:
        return _internal_error_response()


@router.post(
    "/backtest",
    summary="Backtest LLM pipeline",
    description=(
        "Chay backtest end-to-end voi LLM, goi technical + article + fundamental + aggregator "
        "tren du lieu lich su, chi goi LLM tai cac ngay co tin hieu ky thuat."
    ),
)
def backtest_pipeline(
    body: BacktestPipelineRequest,
    current_user: dict = Depends(get_current_admin),
    _rate_limit: None = Depends(_limit_backtest),
):
    try:
        result = run_backtest_pipeline(body)
        return success_response(data=result)

    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(error_code=400001, error_desc=str(e)),
        )
    except RuntimeError:
        return _internal_error_response()
    except Exception:
        return _internal_error_response()


@router.get(
    "/backtests",
    summary="Danh sách kết quả backtest từ Supabase Storage",
)
def list_backtests(current_user: dict = Depends(get_current_admin)):
    try:
        from app.utils.supabase_storage import list_backtest_files
        res = list_backtest_files()
        return success_response(data=res)
    except Exception:
        return _internal_error_response()


def _validated_backtest_filename(filename: str) -> str:
    if not _BACKTEST_FILENAME.fullmatch(filename):
        raise HTTPException(status_code=404, detail="Backtest file not found")
    return filename


@router.get("/backtests/local/{filename}", summary="Read a local backtest result")
def get_local_backtest(
    filename: str, current_user: dict = Depends(get_current_admin)
):
    safe_name = _validated_backtest_filename(filename)
    path = (_LOCAL_BACKTEST_DIR / safe_name).resolve()
    try:
        path.relative_to(_LOCAL_BACKTEST_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=404, detail="Backtest file not found")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Backtest file not found")
    return FileResponse(
        path,
        media_type="application/json",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/backtests/files/{filename}", summary="Read a private cloud backtest result")
def get_cloud_backtest(
    filename: str, current_user: dict = Depends(get_current_admin)
):
    safe_name = _validated_backtest_filename(filename)
    try:
        from app.utils.supabase_storage import download_backtest_file

        content = download_backtest_file(safe_name)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Cache-Control": "no-store"},
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unable to download backtest file")
        raise HTTPException(status_code=404, detail="Backtest file not found")
