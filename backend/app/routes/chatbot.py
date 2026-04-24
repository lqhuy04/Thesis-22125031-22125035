from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.base_schemas import success_response, error_response
from app.models.chatbot_schemas import ChatbotRequest
from app.services.chatbot_service import ChatbotService

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])


def verify_chatbot_api_key(x_chatbot_key: str | None = Header(default=None, alias="x-chatbot-key")):
    configured_key = settings.CHATBOT_API_KEY

    if not configured_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chatbot API key is not configured on server",
        )

    if x_chatbot_key != configured_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid chatbot API key",
        )


@router.post("/")
async def chat(body: ChatbotRequest, _: None = Depends(verify_chatbot_api_key)):
    try:
        data = ChatbotService.chat(
            message=body.message,
            system_prompt=body.system_prompt,
            symbol=body.symbol,
            time_horizon=body.time_horizon,
        )
        return success_response(data=data.model_dump())

    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(error_code=500001, error_desc=str(e)),
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(error_code=500001, error_desc=f"Chatbot error: {e}"),
        )
