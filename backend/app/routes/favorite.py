"""
Favorite Routes
CRUD API endpoints for the flat favorite table.
"""
import uuid

from fastapi import APIRouter, HTTPException, Depends

from app.models.base_schemas import error_response, success_response
from app.models.favorite_schemas import FavoriteCreateRequest, CheckFavoriteRequest
from app.services.favorite_service import FavoriteService
from app.middleware.auth_middleware import get_current_user
from pydantic import BaseModel
from typing import List


router = APIRouter(prefix="/api/favorite", tags=["Favorite"])


@router.get("", summary="List Favorites For Current User")
async def list_favorites_by_user_id(current_user: dict = Depends(get_current_user)):
    request_id = str(uuid.uuid4())
    try:
        user_id = current_user.get("user_id")
        data = await FavoriteService.list_favorites_by_user_id(user_id)
        return success_response(data=data, request_id=request_id)
    except ValueError as e:
        return error_response(error_code=500001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)


@router.post("", summary="Add Favorite")
async def add_favorite(request: FavoriteCreateRequest, current_user: dict = Depends(get_current_user)):
    request_id = str(uuid.uuid4())

    try:
        data = await FavoriteService.add_favorite(
            symbol=request.symbol,
            user_id=current_user.get("user_id"),
        )
        return success_response(data=data, request_id=request_id)
    except ValueError as e:
        return error_response(error_code=400001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)


class DeleteFavoriteRequest(BaseModel):
    favorite_ids: List[str]


@router.delete("", summary="Delete Multiple Favorites")
async def delete_favorites(req: DeleteFavoriteRequest):
    request_id = str(uuid.uuid4())

    try:
        deleted = await FavoriteService.delete_favorites(req.favorite_ids)

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
async def check_is_favorited(request: CheckFavoriteRequest, current_user: dict = Depends(get_current_user)):
    request_id = str(uuid.uuid4())

    try:
        user_id = current_user.get("user_id")
        data = await FavoriteService.check_is_favorited(
            symbol=request.symbol,
            user_id=user_id,
        )
        return success_response(data=data, request_id=request_id)
    except ValueError as e:
        return error_response(error_code=400001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)
