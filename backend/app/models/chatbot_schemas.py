from typing import Literal

from pydantic import BaseModel, Field


class ChatbotRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message for chatbot")
    symbol: str | None = Field(
        default=None,
        description="Optional stock symbol (e.g. VNM). If provided, chatbot uses live market data for grounding",
    )
    time_horizon: Literal["short", "mid", "long"] = Field(
        default="short",
        description="Lookback horizon for 1m data: short, mid, or long",
    )
    system_prompt: str | None = Field(
        default=None,
        description="Optional system prompt to guide chatbot behavior",
    )


class ChatbotData(BaseModel):
    model: str = Field(description="Model used to generate response")
    reply: str = Field(description="Assistant response text")
