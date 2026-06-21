"""
Favorite Routes
CRUD API endpoints for the flat favorite table.
"""
import uuid

from fastapi import APIRouter, HTTPException, Depends

from app.models.base_schemas import error_response, success_response
from app.models.favorite_schemas import FavoriteCreateRequest, CheckFavoriteRequest, DeleteFavoriteRequest
from app.services.favorite_service import FavoriteService
from app.middleware.auth_middleware import get_current_user


router = APIRouter(prefix="/api/favorite", tags=["Favorite"])


@router.get("", summary="List Favorites For Current User")
def list_favorites_by_user_id(current_user: dict = Depends(get_current_user)):
    request_id = str(uuid.uuid4())
    try:
        user_id = current_user.get("user_id")
        data = FavoriteService.list_favorites_by_user_id(user_id)
        return success_response(data=data, request_id=request_id)
    except ValueError as e:
        return error_response(error_code=500001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)


@router.post("", summary="Add Favorite")
def add_favorite(request: FavoriteCreateRequest, current_user: dict = Depends(get_current_user)):
    request_id = str(uuid.uuid4())

    try:
        data = FavoriteService.add_favorite(
            symbol=request.symbol,
            user_id=current_user.get("user_id"),
        )
        return success_response(data=data, request_id=request_id)
    except ValueError as e:
        return error_response(error_code=400001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)
@router.delete("", summary="Delete Favorite")
def delete_favorites(request: DeleteFavoriteRequest, current_user: dict = Depends(get_current_user)):
    request_id = str(uuid.uuid4())

    try:
        deleted = FavoriteService.remove_favorite_by_symbol(
            symbol=request.symbol,
            user_id=current_user.get("user_id"),
        )

        if not deleted:
            raise HTTPException(status_code=404, detail="Favorites not found")

        return success_response(
            data={"deleted": True},
            request_id=request_id
        )

    except HTTPException:
        raise
    except ValueError as e:
        return error_response(
            error_code=500001,
            error_desc=str(e),
            request_id=request_id
        )
    except Exception:
        return error_response(
            error_code=500001,
            error_desc="Internal server error",
            request_id=request_id
        )


@router.post("/check", summary="Check If Stock Is Favorited")
def check_is_favorited(request: CheckFavoriteRequest, current_user: dict = Depends(get_current_user)):
    request_id = str(uuid.uuid4())

    try:
        user_id = current_user.get("user_id")
        data = FavoriteService.check_is_favorited(
            symbol=request.symbol,
            user_id=user_id,
        )
        return success_response(data=data, request_id=request_id)
    except ValueError as e:
        return error_response(error_code=400001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)
