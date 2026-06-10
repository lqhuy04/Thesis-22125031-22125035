"""
Risk Appetite Routes
API endpoints for user risk appetite questionnaire
"""
from fastapi import APIRouter, Depends
from app.models.risk_appetite_schemas import RiskAppetiteRequest, RiskAppetiteData
from app.models.base_schemas import success_response, error_response
from app.services.risk_appetite_service import RiskAppetiteService
from app.middleware.auth_middleware import get_current_user
import uuid

router = APIRouter(prefix="/api/risk-appetite", tags=["Risk Appetite"])


@router.get("/",
            summary="Get Risk Appetite",
            description="Retrieve the authenticated user's risk appetite profile.")
async def get_risk_appetite(current_user: dict = Depends(get_current_user)):
    """
    Get risk appetite for the currently authenticated user.
    Requires a valid Bearer token.
    """
    request_id = str(uuid.uuid4())

    try:
        user_id = current_user["user_id"]
        data = await RiskAppetiteService.get_risk_appetite_by_user(user_id)

        if not data:
            return error_response(
                error_code=404001,
                error_desc="No risk appetite record found for this user",
                request_id=request_id,
            )

        risk_data = RiskAppetiteData(
            id=data.get("id"),
            userId=data.get("userid"),
            period=data.get("period"),
        ).model_dump()

        return success_response(data=risk_data, request_id=request_id)

    except ValueError as e:
        return error_response(
            error_code=500001,
            error_desc=str(e),
            request_id=request_id,
        )
    except Exception:
        return error_response(
            error_code=500001,
            error_desc="Internal server error",
            request_id=request_id,
        )


@router.post("/",
             summary="Create or Update Risk Appetite",
             description="Save or update the authenticated user's risk appetite profile.")
async def save_risk_appetite(
    request: RiskAppetiteRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Create or update risk appetite for the currently authenticated user.
    Requires a valid Bearer token.
    """
    request_id = str(uuid.uuid4())

    try:
        user_id = current_user["user_id"]

        data = await RiskAppetiteService.upsert_risk_appetite(
            user_id=user_id,
            period=request.period.value,
        )

        risk_data = RiskAppetiteData(
            id=data.get("id"),
            userId=data.get("userid"),
            period=data.get("period"),
        ).model_dump()

        return success_response(data=risk_data, request_id=request_id)

    except ValueError as e:
        return error_response(
            error_code=500001,
            error_desc=str(e),
            request_id=request_id,
        )
    except Exception:
        return error_response(
            error_code=500001,
            error_desc="Internal server error",
            request_id=request_id,
        )
