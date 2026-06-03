"""
app/models/agentic_schemas.py
Request / Response schemas cho agentic AI endpoints.
"""

from typing import Literal, Any
from pydantic import BaseModel, Field


# ─── Shared ───────────────────────────────────────────────────────────────────

class RiskAppetite(BaseModel):
    period: str = Field(description="Kỳ hạn đầu tư, ví dụ: 'Ngắn hạn (Dưới 1 năm)'")


# ─── /analyze (API mode) ──────────────────────────────────────────────────────

class StockAnalysisRequest(BaseModel):
    mode: str = Field(description="Chế độ tự động(auto) hoặc thủ công(manual)")
    symbol: str = Field(description="Mã cổ phiếu, ví dụ: VNM, FPT, VIC")
    risk_appetite: RiskAppetite
    plan: Any | None = Field(default=None, description="Kế hoạch phân tích thủ công, bỏ trống nếu dùng auto")


class InvestmentRecommendation(BaseModel):
    summary: str
    recommendation: Literal["Mua", "Giữ", "Chờ", "Bán"]
    reasoning: str
    confidence: float = Field(ge=0, le=1)


# ─── /chat (Chatbot mode) ─────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str = Field(
        description="ID phiên hội thoại. Client tự tạo (UUID) và giữ nguyên suốt cuộc trò chuyện."
    )
    message: str = Field(description="Tin nhắn của user")


class ChatResponse(BaseModel):
    session_id: str
    reply: str                          # plain text trả về cho user