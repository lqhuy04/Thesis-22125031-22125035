"""
Search history routes.
CRUD API endpoints for recent searched symbols.
"""
import uuid

from fastapi import APIRouter, Depends

from app.middleware.auth_middleware import get_current_user
from app.models.base_schemas import error_response, success_response
from app.models.search_history_schemas import SearchHistoryCreateRequest
from app.services.search_history_service import SearchHistoryService


router = APIRouter(prefix="/api/search-history", tags=["Search History"])


@router.get("", summary="List Search History For Current User")
def list_search_history(current_user: dict = Depends(get_current_user)):
    request_id = str(uuid.uuid4())
    try:
        user_id = current_user.get("user_id")
        data = SearchHistoryService.list_search_history_by_user_id(user_id)
        return success_response(data=data, request_id=request_id)
    except ValueError as e:
        return error_response(error_code=500001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)


@router.post("", summary="Add Search History")
def add_search_history(request: SearchHistoryCreateRequest, current_user: dict = Depends(get_current_user)):
    request_id = str(uuid.uuid4())
    try:
        data = SearchHistoryService.add_search_history(
            symbol=request.symbol,
            user_id=current_user.get("user_id"),
        )
        return success_response(data=data, request_id=request_id)
    except ValueError as e:
        return error_response(error_code=400001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)


@router.delete("/{symbol}", summary="Remove Search History Item")
def remove_search_history(symbol: str, current_user: dict = Depends(get_current_user)):
    request_id = str(uuid.uuid4())
    try:
        data = SearchHistoryService.remove_search_history_by_symbol(
            symbol=symbol,
            user_id=current_user.get("user_id"),
        )
        return success_response(data=data, request_id=request_id)
    except ValueError as e:
        return error_response(error_code=400001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)


@router.delete("", summary="Clear Search History")
def clear_search_history(current_user: dict = Depends(get_current_user)):
    request_id = str(uuid.uuid4())
    try:
        data = SearchHistoryService.clear_search_history(current_user.get("user_id"))
        return success_response(data=data, request_id=request_id)
    except ValueError as e:
        return error_response(error_code=400001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)