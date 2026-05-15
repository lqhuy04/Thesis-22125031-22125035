"""
app/models/agentic_schemas.py
Request / Response schemas cho agentic AI endpoints.
"""

from typing import Literal, Any
from pydantic import BaseModel, Field


# ─── Shared ───────────────────────────────────────────────────────────────────

class RiskAppetite(BaseModel):
    capital_ratio: str = Field(description="Tỷ lệ vốn, ví dụ: 'Dưới 10%'")
    comfort_zone: str = Field(description="Ngưỡng lợi nhuận / lỗ chấp nhận được")
    expectation: str = Field(description="Kỳ vọng đầu tư")
    experience: str = Field(description="Kinh nghiệm của nhà đầu tư")
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
    risk_appetite: RiskAppetite | None = Field(
        default=None,
        description="Khẩu vị rủi ro. Chỉ cần gửi ở tin nhắn đầu tiên, các turn sau bỏ qua."
    )


class ChatResponse(BaseModel):
    session_id: str
    reply: str                          # plain text trả về cho user
    intent_type: str                    # để client biết loại intent (có thể dùng để render UI)
    instant_reply: bool = Field(
        description="True nếu reply đến từ intent_classifier (không qua full pipeline)"
    )