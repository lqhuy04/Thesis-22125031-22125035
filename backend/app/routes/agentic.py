"""
routes/agentic.py
"""

import logging
import re
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path as ApiPath, Query, Request, status
from fastapi.responses import FileResponse, JSONResponse, Response

from app.middleware.auth_middleware import get_current_user
from app.models.base_schemas import success_response, error_response
from app.models.agentic_schemas import StockAnalysisRequest, ChatRequest, ChatSeedRequest, ExperimentAnalysisRequest
from app.models.backtest_pipeline_schemas import BacktestPipelineRequest
from app.models.experiment_schemas import (
    ExperimentComparisonRequest,
    ExperimentStatus,
    ExperimentType,
)
from app.services.backtest_pipeline_service import run_backtest_pipeline
from app.services.experiment_service import ExperimentService
from app.utils.rate_limit import enforce_rate_limit
from app.utils.reproducibility import investment_disclaimer
from app.services.agentic_service import (
    run_chat,
    seed_chat_session,
    run_stock_analysis_v2,
    run_experiment_analysis,
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


def _fail_experiment_safely(
    experiment_id: str | None,
    user_id: str,
    error: Exception,
) -> None:
    if not experiment_id:
        return
    try:
        ExperimentService.fail(
            experiment_id=experiment_id,
            user_id=user_id,
            error_message=str(error),
        )
    except Exception:
        logger.exception("Unable to mark experiment as failed")


def _analysis_result_summary(result: dict) -> dict:
    entries = result.get("results") if isinstance(result, dict) else []
    entries = entries if isinstance(entries, list) else []
    successful = [entry for entry in entries if entry.get("status") == "ok"]
    failed = [entry for entry in entries if entry.get("status") != "ok"]
    summary = {
        "count": len(entries),
        "successful": len(successful),
        "failed": len(failed),
        "symbols": [entry.get("symbol") for entry in entries if entry.get("symbol")],
    }
    if len(successful) == 1:
        recommendation = successful[0].get("recommendation") or {}
        score = recommendation.get("score")
        summary.update({
            "recommendation": recommendation.get("recommendation"),
            "buy": recommendation.get("buy"),
            "confidence": recommendation.get("confidence"),
            "score": score.get("total") if isinstance(score, dict) else score,
        })
    return summary


def _backtest_result_summary(result: dict, symbol: str) -> dict:
    metrics = result.get("full_metrics") or {}
    return {
        "symbol": symbol,
        "net_profit": (metrics.get("pnl") or {}).get("total_return"),
        "win_rate": (metrics.get("volume") or {}).get("win_rate"),
        "total_trades": (metrics.get("volume") or {}).get("n_trades"),
        "sharpe_ratio": (metrics.get("risk") or {}).get("sharpe_ratio"),
        "max_drawdown": (metrics.get("risk") or {}).get("max_drawdown"),
    }


def _backtest_history_data(result: dict) -> dict:
    keys = (
        "configuration",
        "full_metrics",
        "engine_metrics",
        "benchmarks",
        "regime",
        "confidence",
        "stats",
        "visualization_file",
        "visualization_data_url",
        "reproducibility",
        "investment_disclaimer",
    )
    return {key: result.get(key) for key in keys}


async def _limit_ai(
    request: Request, current_user: dict = Depends(get_current_user)
):
    await enforce_rate_limit(
        "agentic-ai", current_user["user_id"], limit=30, window_seconds=60
    )


async def _limit_experiment_ai(
    request: Request, current_user: dict = Depends(get_current_user)
):
    await enforce_rate_limit(
        "agentic-experiment-ai",
        current_user["user_id"],
        limit=120,
        window_seconds=600,
    )


async def _limit_backtest(
    request: Request, current_user: dict = Depends(get_current_user)
):
    await enforce_rate_limit(
        "agentic-backtest",
        current_user["user_id"],
        limit=40,
        window_seconds=3600,
    )


# ─── API mode: structured output ─────────────────────────────────────────────

@router.post(
    "/analyze",
    summary="Phân tích cổ phiếu",
    description="Chạy pipeline phân tích agentic AI v2. Không có memory.",
)
def analyze_stock(
    body: StockAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    _rate_limit: None = Depends(_limit_ai),
):
    try:
        recommendation = run_stock_analysis_v2(
            mode=body.mode,
            symbol=body.symbol,
            language=body.language,
            risk_appetite=body.risk_appetite.model_dump(),
            data_selection=body.data_selection.model_dump(),
        )
        return success_response(data=recommendation)

    except RuntimeError:
        return _internal_error_response()
    except Exception:
        return _internal_error_response()


# ─── Stockrium Lab: structured output, authentication required ────────

@router.post("/admin-analyze", include_in_schema=False)
@router.post(
    "/experiments/analyze",
    summary="Phân tích cổ phiếu (Stockrium Lab)",
    description=(
        "Phân tích thử nghiệm, hỗ trợ chạy theo rổ chỉ số "
        "VN30 (30 mã) hoặc VN100 (100 mã); bỏ trống `universe` để phân tích 1 mã."
    ),
)
def analyze_experiment(
    body: ExperimentAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    _rate_limit: None = Depends(_limit_experiment_ai),
):
    user_id = current_user["user_id"]
    experiment_id = None
    try:
        scope = body.universe or "single"
        symbol = body.symbol.strip().upper() if body.symbol else None
        experiment = ExperimentService.create(
            user_id=user_id,
            experiment_type=ExperimentType.ANALYSIS,
            scope=scope,
            symbol=symbol,
            mode=body.mode,
            configuration=body.model_dump(mode="json"),
            name=body.experiment_name,
        )
        experiment_id = experiment["id"]
        result = run_experiment_analysis(
            mode=body.mode,
            universe=body.universe,
            symbol=body.symbol,
            risk_appetite=body.risk_appetite.model_dump(),
            data_selection=body.data_selection.model_dump(),
        )
        result["experiment_id"] = experiment_id
        result["reproducibility"] = experiment.get("reproducibility", {})
        result["investment_disclaimer"] = investment_disclaimer()
        ExperimentService.complete(
            experiment_id=experiment_id,
            user_id=user_id,
            result_summary=_analysis_result_summary(result),
            result_data=result,
        )
        return success_response(data=result)

    except ValueError as e:
        _fail_experiment_safely(experiment_id, user_id, e)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(error_code=400001, error_desc=str(e)),
        )
    except RuntimeError as e:
        _fail_experiment_safely(experiment_id, user_id, e)
        return _internal_error_response()
    except Exception as e:
        _fail_experiment_safely(experiment_id, user_id, e)
        return _internal_error_response()


@router.post("/experiments/compare", summary="So sánh nhiều thử nghiệm của user")
def compare_experiments(
    body: ExperimentComparisonRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        requested_ids = [str(item) for item in body.experiment_ids]
        items = ExperimentService.get_many_for_user(
            experiment_ids=requested_ids,
            user_id=current_user["user_id"],
        )
        if len(items) != len(requested_ids):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=error_response(
                    error_code=404001,
                    error_desc="Không tìm thấy một hoặc nhiều thử nghiệm của bạn",
                ),
            )
        return success_response(data={
            "items": items,
            "investment_disclaimer": investment_disclaimer(),
        })
    except Exception:
        return _internal_error_response()


@router.get("/experiments", summary="Lịch sử thử nghiệm của user")
def list_experiments(
    experiment_type: ExperimentType | None = Query(default=None),
    experiment_status: ExperimentStatus | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    try:
        items = ExperimentService.list_for_user(
            user_id=current_user["user_id"],
            experiment_type=experiment_type,
            status=experiment_status,
            limit=limit,
            offset=offset,
        )
        return success_response(data={
            "items": items,
            "limit": limit,
            "offset": offset,
            "investment_disclaimer": investment_disclaimer(),
        })
    except Exception:
        return _internal_error_response()


@router.get("/experiments/{experiment_id}", summary="Chi tiết một thử nghiệm")
def get_experiment(
    experiment_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    try:
        experiment = ExperimentService.get_for_user(
            experiment_id=str(experiment_id),
            user_id=current_user["user_id"],
        )
        if experiment is None:
            raise HTTPException(status_code=404, detail="Experiment not found")
        experiment["investment_disclaimer"] = investment_disclaimer()
        return success_response(data=experiment)
    except HTTPException:
        raise
    except Exception:
        return _internal_error_response()


@router.get("/admin-universe/{name}", include_in_schema=False)
@router.get(
    "/market-universes/{name}",
    summary="Danh sách mã của một rổ chỉ số",
    description="Trả về danh sách mã cổ phiếu thuộc rổ VN30 / VN100 từ Supabase.",
)
def market_universe(name: str, current_user: dict = Depends(get_current_user)):
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
    current_user: dict = Depends(get_current_user),
    _rate_limit: None = Depends(_limit_backtest),
):
    user_id = current_user["user_id"]
    experiment_id = None
    try:
        symbol = body.symbol.strip().upper()
        experiment = ExperimentService.create(
            user_id=user_id,
            experiment_type=ExperimentType.BACKTEST,
            scope="single",
            symbol=symbol,
            mode=body.mode,
            configuration=body.model_dump(mode="json"),
            name=body.experiment_name,
        )
        experiment_id = experiment["id"]
        result = run_backtest_pipeline(
            body,
            user_id=user_id,
        )
        result["experiment_id"] = experiment_id
        result["reproducibility"] = experiment.get("reproducibility", {})
        result["investment_disclaimer"] = investment_disclaimer()
        ExperimentService.complete(
            experiment_id=experiment_id,
            user_id=user_id,
            result_summary=_backtest_result_summary(result, symbol),
            result_data=_backtest_history_data(result),
            result_reference=result.get("visualization_data_url"),
        )
        return success_response(data=result)

    except ValueError as e:
        _fail_experiment_safely(experiment_id, user_id, e)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(error_code=400001, error_desc=str(e)),
        )
    except RuntimeError as e:
        _fail_experiment_safely(experiment_id, user_id, e)
        return _internal_error_response()
    except Exception as e:
        _fail_experiment_safely(experiment_id, user_id, e)
        return _internal_error_response()


@router.get(
    "/backtests",
    summary="Danh sách kết quả backtest từ Supabase Storage",
)
def list_backtests(current_user: dict = Depends(get_current_user)):
    try:
        from app.utils.supabase_storage import list_backtest_files
        res = list_backtest_files(current_user["user_id"])
        return success_response(data=res)
    except Exception:
        return _internal_error_response()


def _validated_backtest_filename(filename: str) -> str:
    if not _BACKTEST_FILENAME.fullmatch(filename):
        raise HTTPException(status_code=404, detail="Backtest file not found")
    return filename


@router.get("/backtests/local/{filename}", summary="Read a local backtest result")
def get_local_backtest(
    filename: str, current_user: dict = Depends(get_current_user)
):
    from app.utils.user_namespace import user_namespace

    safe_name = _validated_backtest_filename(filename)
    owner_dir = (
        _LOCAL_BACKTEST_DIR / user_namespace(current_user["user_id"])
    ).resolve()
    path = (owner_dir / safe_name).resolve()
    try:
        path.relative_to(owner_dir)
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
    filename: str, current_user: dict = Depends(get_current_user)
):
    safe_name = _validated_backtest_filename(filename)
    try:
        from app.utils.supabase_storage import download_backtest_file

        content = download_backtest_file(
            current_user["user_id"],
            safe_name,
        )
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
