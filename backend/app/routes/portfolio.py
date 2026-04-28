"""
Portfolio Routes
CRUD API endpoints for the flat portfolio table.
"""
import uuid

from fastapi import APIRouter, HTTPException, Query, Depends

from app.models.base_schemas import error_response, success_response
from app.models.portfolio_schemas import PortfolioCreateRequest, PortfolioUpdateRequest
from app.services.portfolio_service import PortfolioService
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])


@router.get("", summary="List Portfolios For Current User")
async def list_portfolios_by_user_id(current_user: dict = Depends(get_current_user)):
    request_id = str(uuid.uuid4())
    try:
        user_id = current_user.get("user_id")
        data = await PortfolioService.list_portfolios_by_user_id(user_id)
        return success_response(data=data, request_id=request_id)
    except ValueError as e:
        return error_response(error_code=500001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)


@router.post("", summary="Create Portfolio")
async def create_portfolio(request: PortfolioCreateRequest, current_user: dict = Depends(get_current_user)):
    request_id = str(uuid.uuid4())

    try:
        data = await PortfolioService.create_portfolio(
            symbol=request.symbol,
            user_id=current_user.get("user_id"),
            amount=request.amount,
            buy_price=request.buy_price,
            time=request.time,
        )
        return success_response(data=data, request_id=request_id)
    except ValueError as e:
        return error_response(error_code=400001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)


@router.put("/{portfolio_id}", summary="Update Portfolio By ID")
async def update_portfolio_by_id(portfolio_id: str, request: PortfolioUpdateRequest, current_user: dict = Depends(get_current_user)):
    request_id = str(uuid.uuid4())

    try:
        # ensure the user owns the transaction? Service handles authorization if needed.
        data = await PortfolioService.update_portfolio(
            portfolio_id=portfolio_id,
            amount=request.amount,
            buy_price=request.buy_price,
            time=request.time,
        )

        if not data:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        return success_response(data=data, request_id=request_id)
    except HTTPException:
        raise
    except ValueError as e:
        return error_response(error_code=400001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)


@router.delete("/{portfolio_id}", summary="Delete Portfolio By ID")
async def delete_portfolio_by_id(portfolio_id: str):
    request_id = str(uuid.uuid4())

    try:
        deleted = await PortfolioService.delete_portfolio(portfolio_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        return success_response(data={"deleted": True}, request_id=request_id)
    except HTTPException:
        raise
    except ValueError as e:
        return error_response(error_code=500001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)
