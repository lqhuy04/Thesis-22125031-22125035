"""
Portfolio Routes
CRUD API endpoints for portfolios (auth temporarily disabled for testing).
"""
from fastapi import APIRouter, HTTPException, Query
import uuid

from app.models.base_schemas import success_response, error_response
from app.models.portfolio_schemas import (
    PortfolioCreateRequest,
    PortfolioUpdateRequest,
    HoldingCreateRequest,
    HoldingUpdateRequest,
)
from app.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])


@router.get("/{user_id}", summary="Get Portfolio By User ID")
async def get_portfolio_by_user_id(user_id: str):
    request_id = str(uuid.uuid4())

    try:
        data = await PortfolioService.get_portfolio_by_user_id(user_id)
        if not data:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        return success_response(data=data, request_id=request_id)
    except HTTPException:
        raise
    except ValueError as e:
        return error_response(error_code=500001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)


@router.post("/", summary="Create Portfolio")
async def create_portfolio(request: PortfolioCreateRequest):
    request_id = str(uuid.uuid4())

    try:
        data = await PortfolioService.create_portfolio(
            user_id=request.user_id,
            name=request.name,
            description=request.description,
        )
        return success_response(data=data, request_id=request_id)
    except ValueError as e:
        return error_response(error_code=500001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)


@router.put("/{user_id}", summary="Update Portfolio By User ID")
async def update_portfolio_by_user_id(user_id: str, request: PortfolioUpdateRequest):
    request_id = str(uuid.uuid4())

    try:
        portfolio = await PortfolioService.get_portfolio_by_user_id(user_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        data = await PortfolioService.update_portfolio(
            portfolio_id=portfolio["id"],
            name=request.name,
            description=request.description,
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


@router.delete("/{user_id}", summary="Delete Portfolio By User ID")
async def delete_portfolio_by_user_id(user_id: str):
    request_id = str(uuid.uuid4())

    try:
        portfolio = await PortfolioService.get_portfolio_by_user_id(user_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        deleted = await PortfolioService.delete_portfolio(portfolio["id"])
        if not deleted:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        return success_response(data={"deleted": True}, request_id=request_id)
    except HTTPException:
        raise
    except ValueError as e:
        return error_response(error_code=500001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)


@router.get("/{user_id}/holdings", summary="List Holdings By User ID")
async def list_holdings_by_user_id(user_id: str):
    request_id = str(uuid.uuid4())

    try:
        portfolio = await PortfolioService.get_portfolio_by_user_id(user_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        data = await PortfolioService.list_holdings(portfolio["id"])
        return success_response(data=data, request_id=request_id)
    except HTTPException:
        raise
    except ValueError as e:
        return error_response(error_code=500001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)


@router.get("/{user_id}/holdings/summary", summary="Get Holdings Summary By User ID")
async def get_holdings_summary_by_user_id(user_id: str):
    request_id = str(uuid.uuid4())

    try:
        portfolio = await PortfolioService.get_portfolio_by_user_id(user_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        data = await PortfolioService.get_holdings_summary(portfolio["id"])
        return success_response(data=data, request_id=request_id)
    except HTTPException:
        raise
    except ValueError as e:
        return error_response(error_code=500001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)


@router.get("/{user_id}/holdings/{holding_id}", summary="Get Holding By User ID")
async def get_holding_by_user_id(user_id: str, holding_id: str):
    request_id = str(uuid.uuid4())

    try:
        portfolio = await PortfolioService.get_portfolio_by_user_id(user_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        data = await PortfolioService.get_holding_by_id(portfolio_id=portfolio["id"], holding_id=holding_id)
        if not data:
            raise HTTPException(status_code=404, detail="Holding not found")

        return success_response(data=data, request_id=request_id)
    except HTTPException:
        raise
    except ValueError as e:
        return error_response(error_code=500001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)


@router.post("/{user_id}/holdings", summary="Add Holding By User ID")
async def add_holding_by_user_id(user_id: str, request: HoldingCreateRequest):
    request_id = str(uuid.uuid4())

    try:
        portfolio = await PortfolioService.get_portfolio_by_user_id(user_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        data = await PortfolioService.add_holding(
            portfolio_id=portfolio["id"],
            ticker=request.ticker,
            shares=request.shares,
            buy_price=request.buy_price,
            company_name=request.company_name,
        )
        return success_response(data=data, request_id=request_id)
    except HTTPException:
        raise
    except ValueError as e:
        return error_response(error_code=400001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)


@router.put("/{user_id}/holdings/{holding_id}", summary="Update Holding By User ID")
async def update_holding_by_user_id(user_id: str, holding_id: str, request: HoldingUpdateRequest):
    request_id = str(uuid.uuid4())

    try:
        portfolio = await PortfolioService.get_portfolio_by_user_id(user_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        data = await PortfolioService.update_holding(
            portfolio_id=portfolio["id"],
            holding_id=holding_id,
            shares=request.shares,
            avg_buy_price=request.avg_buy_price,
            company_name=request.company_name,
        )

        if not data:
            raise HTTPException(status_code=404, detail="Holding not found")

        return success_response(data=data, request_id=request_id)
    except HTTPException:
        raise
    except ValueError as e:
        return error_response(error_code=400001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)


@router.delete("/{user_id}/holdings/{holding_id}", summary="Delete Holding By User ID")
async def delete_holding_by_user_id(user_id: str, holding_id: str):
    request_id = str(uuid.uuid4())

    try:
        portfolio = await PortfolioService.get_portfolio_by_user_id(user_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        deleted = await PortfolioService.delete_holding(portfolio_id=portfolio["id"], holding_id=holding_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Holding not found")
        return success_response(data={"deleted": True}, request_id=request_id)
    except HTTPException:
        raise
    except ValueError as e:
        return error_response(error_code=500001, error_desc=str(e), request_id=request_id)
    except Exception:
        return error_response(error_code=500001, error_desc="Internal server error", request_id=request_id)
