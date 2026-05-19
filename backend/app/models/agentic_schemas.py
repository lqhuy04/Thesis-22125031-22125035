"""
app/models/agentic_schemas.py
Request / Response schemas cho agentic AI endpoints.
"""

from typing import Literal, Any
from pydantic import BaseModel, ConfigDict, Field


# ─── Shared ───────────────────────────────────────────────────────────────────

class RiskAppetite(BaseModel):
    """
    Khẩu vị rủi ro của nhà đầu tư.

    Bắt buộc:
      - period

    Tùy chọn (có fallback default theo period nếu thiếu):
      - target_profit_pct, max_loss_pct
      - risk_tolerance, preference

    Field cũ (capital_ratio, comfort_zone, expectation, experience) vẫn được
    nhận nhờ `extra="ignore"` nhưng KHÔNG còn được dùng để quyết định gì.
    """

    model_config = ConfigDict(extra="ignore")

    period: str = Field(
        description=(
            "Kỳ hạn đầu tư. Chấp nhận:\n"
            "  - 'short_term' / 'Ngắn hạn (...)' — vài tuần đến dưới 1 năm\n"
            "  - 'mid_term'   / 'Trung hạn (...)' — 1 đến 3 năm\n"
            "  - 'long_term'  / 'Dài hạn (...)'  — trên 3 năm"
        )
    )

    target_profit_pct: float | None = Field(
        default=None,
        ge=3,
        le=200,
        description=(
            "Lợi nhuận kỳ vọng mỗi lệnh (%). Phạm vi 3–200.\n"
            "Bỏ trống → fallback theo period: short=10, mid=20, long=40."
        ),
    )

    max_loss_pct: float | None = Field(
        default=None,
        ge=2,
        le=30,
        description=(
            "Mức lỗ tối đa chấp nhận (%). Phạm vi 2–30.\n"
            "Bỏ trống → fallback theo period: short=5, mid=10, long=15."
        ),
    )

    risk_tolerance: Literal["cautious", "balanced", "aggressive"] = Field(
        default="balanced",
        description=(
            "Khẩu vị rủi ro tổng thể:\n"
            "  - cautious   : siết ngưỡng technical (cần score ≥ 6/9 để Mua)\n"
            "  - balanced   : mặc định (score ≥ 5/9)\n"
            "  - aggressive : nới ngưỡng (score ≥ 4/9)"
        ),
    )

    preference: Literal["growth", "income", "balanced"] = Field(
        default="balanced",
        description=(
            "Ưu tiên đầu tư:\n"
            "  - growth   : nghiêng về fundamental TỐT (mã tăng trưởng)\n"
            "  - income   : ưu tiên ROE cao, CFO dương, cổ tức ổn định\n"
            "  - balanced : không điều chỉnh"
        ),
    )


# ─── /analyze (API mode) ──────────────────────────────────────────────────────

class StockAnalysisRequest(BaseModel):
    mode: str = Field(description="Chế độ tự động (auto) hoặc thủ công (manual)")
    symbol: str = Field(description="Mã cổ phiếu, ví dụ: VNM, FPT, VIC")
    risk_appetite: RiskAppetite
    plan: Any | None = Field(
        default=None,
        description="Kế hoạch phân tích thủ công, bỏ trống nếu dùng auto",
    )


# ─── /chat (Chatbot mode) ─────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str = Field(
        description=(
            "ID phiên hội thoại. Client tự tạo (UUID) và giữ nguyên suốt cuộc trò chuyện."
        )
    )
    message: str = Field(description="Tin nhắn của user")
    risk_appetite: RiskAppetite | None = Field(
        default=None,
        description=(
            "Khẩu vị rủi ro. Chỉ cần gửi ở tin nhắn đầu tiên, các turn sau bỏ qua."
        ),
    )


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    intent_type: str
    instant_reply: bool = Field(
        description="True nếu reply đến từ intent_classifier (không qua full pipeline)"
    )
