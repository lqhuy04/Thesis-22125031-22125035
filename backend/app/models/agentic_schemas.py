"""
app/models/agentic_schemas.py
Request / Response schemas cho agentic AI endpoints.
"""

from typing import Literal, Any
from pydantic import BaseModel, Field


# ─── Shared ───────────────────────────────────────────────────────────────────

class RiskAppetite(BaseModel):
    period: str = Field(description="Kỳ hạn đầu tư, ví dụ: 'Ngắn hạn (Dưới 1 năm)'")


# ─── Data selection (toggle nguồn dữ liệu cho AI) ──────────────────────────────

class TechnicalSelection(BaseModel):
    """Bật/tắt từng chỉ số kỹ thuật mà AI được phép phân tích."""
    ma: bool = Field(default=True, description="Đường trung bình động (MA/SMA20, SMA50)")
    boll: bool = Field(default=True, description="Bollinger Bands")
    rsi: bool = Field(default=True, description="Chỉ số sức mạnh tương đối RSI")
    macd: bool = Field(default=True, description="MACD")
    kdj: bool = Field(default=True, description="KDJ")


class FundamentalSelection(BaseModel):
    """Bật/tắt từng nhóm chỉ số cơ bản mà AI được phép phân tích."""
    valuation: bool = Field(default=True, description="Chỉ số định giá: P/E, P/B, EV/EBITDA, EPS")
    profitability: bool = Field(default=True, description="Khả năng sinh lời: ROE, ROA, biên LN gộp, biên LN ròng")
    growth: bool = Field(default=True, description="Tăng trưởng: doanh thu YoY, lợi nhuận YoY, doanh thu thuần, lợi nhuận ròng")
    financial_health: bool = Field(default=True, description="Sức khỏe tài chính: thanh khoản hiện tại, Nợ/VCSH, khả năng trả lãi")
    cash_flow: bool = Field(default=True, description="Dòng tiền: CFO, CAPEX, cổ tức đã trả")


class DataSelection(BaseModel):
    """Cấu hình người dùng chọn dữ liệu nào để AI phân tích. Mặc định bật tất cả."""
    news: bool = Field(default=True, description="Tin tức / sentiment bài viết")
    technical: TechnicalSelection = Field(default_factory=TechnicalSelection)
    fundamental: FundamentalSelection = Field(default_factory=FundamentalSelection)


# ─── /analyze (API mode) ──────────────────────────────────────────────────────

class StockAnalysisRequest(BaseModel):
    mode: str = Field(description="Chế độ tự động(auto) hoặc thủ công(manual)")
    symbol: str = Field(description="Mã cổ phiếu, ví dụ: VNM, FPT, VIC")
    risk_appetite: RiskAppetite
    plan: Any | None = Field(default=None, description="Kế hoạch phân tích thủ công, bỏ trống nếu dùng auto")
    data_selection: DataSelection = Field(
        default_factory=DataSelection,
        description="Chọn nguồn/chỉ số dữ liệu cho AI phân tích. Bỏ trống = bật tất cả.",
    )


# ─── /admin-analyze (Admin API mode) ──────────────────────────────────────────

class AdminAnalysisRequest(BaseModel):
    """Như /analyze nhưng dành cho admin và hỗ trợ chạy theo rổ chỉ số."""
    mode: str = Field(description="Chế độ tự động(auto) hoặc thủ công(manual)")
    universe: str | None = Field(
        default=None,
        description="Rổ phân tích: 'VN30' | 'VN100'. Bỏ trống = phân tích 1 mã (symbol).",
    )
    symbol: str | None = Field(
        default=None,
        description="Mã cổ phiếu khi không dùng rổ, ví dụ: VNM, FPT, VIC",
    )
    risk_appetite: RiskAppetite
    plan: Any | None = Field(default=None, description="Kế hoạch phân tích thủ công, bỏ trống nếu dùng auto")
    data_selection: DataSelection = Field(
        default_factory=DataSelection,
        description="Chọn nguồn/chỉ số dữ liệu cho AI phân tích. Bỏ trống = bật tất cả.",
    )


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