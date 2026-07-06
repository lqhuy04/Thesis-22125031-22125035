"""
app/models/agentic_schemas.py
Request / Response schemas cho agentic AI endpoints.
"""

from typing import Literal
from pydantic import BaseModel, Field, model_validator


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
    liquidity: bool = Field(default=True, description="Khả năng thanh toán: tỷ lệ thanh toán hiện hành, thanh toán nhanh, tiền mặt")
    leverage: bool = Field(default=True, description="Đòn bẩy tài chính: Nợ/VCSH, đòn bẩy tài chính, khả năng trả lãi")
    efficiency: bool = Field(default=True, description="Hiệu quả hoạt động: vòng quay tài sản, vòng quay TSCĐ, số ngày tồn kho, số ngày phải thu")
    profitability: bool = Field(default=True, description="Khả năng sinh lời: ROE, ROA, biên LN gộp, biên LN ròng")
    valuation: bool = Field(default=True, description="Nhóm định giá: P/E, P/B, EV/EBITDA, EPS")


class WeightSelection(BaseModel):
    """Trọng số thủ công người dùng gán cho từng nguồn khi tính confidence.

    Mỗi giá trị trong [0, 1], tối đa 2 chữ số thập phân, và tổng 3 giá trị phải = 1.0.
    Bỏ trống toàn bộ (None) → hệ thống dùng trọng số mặc định theo kỳ hạn đầu tư
    (xem CONFIDENCE_WEIGHTS_BY_HORIZON trong aggregator.py).
    """
    news: float = Field(ge=0, le=1, description="Trọng số cho tin tức")
    technical: float = Field(ge=0, le=1, description="Trọng số cho phân tích kỹ thuật")
    fundamental: float = Field(ge=0, le=1, description="Trọng số cho phân tích cơ bản")

    @model_validator(mode="after")
    def _validate_weights(self):
        for name, value in (("news", self.news), ("technical", self.technical), ("fundamental", self.fundamental)):
            if round(value, 2) != value:
                raise ValueError(f"weight.{name} chỉ được tối đa 2 chữ số thập phân")

        total = round(self.news + self.technical + self.fundamental, 2)
        if total != 1.0:
            raise ValueError(f"Tổng weight (news + technical + fundamental) phải bằng 1.0, hiện tại: {total}")

        return self


class DataSelection(BaseModel):
    """Cấu hình người dùng chọn dữ liệu nào để AI phân tích. Mặc định bật tất cả."""
    news: bool = Field(default=True, description="Tin tức / sentiment bài viết")
    technical: TechnicalSelection = Field(default_factory=TechnicalSelection)
    fundamental: FundamentalSelection = Field(default_factory=FundamentalSelection)
    weight: WeightSelection | None = Field(
        default=None,
        description="Trọng số thủ công cho news/technical/fundamental. Bỏ trống = dùng mặc định theo kỳ hạn.",
    )


# ─── /analyze (API mode) ──────────────────────────────────────────────────────

class StockAnalysisRequest(BaseModel):
    mode: str = Field(description="Chế độ tự động(auto) hoặc thủ công(manual)")
    symbol: str = Field(description="Mã cổ phiếu, ví dụ: VNM, FPT, VIC")
    risk_appetite: RiskAppetite
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


# ─── /chat/seed (nạp sẵn 1 lượt hội thoại từ kết quả phân tích) ────────────────

class ChatSeedRequest(BaseModel):
    """Tạo phiên chat mới với 1 lượt Q&A đã có sẵn (từ màn phân tích AI).

    Client tự dựng nội dung câu trả lời từ dữ liệu đã hiển thị rồi gửi lên để
    nạp thẳng vào memory (checkpoint) của session — nhờ đó các câu hỏi tiếp theo
    có đầy đủ ngữ cảnh phân tích mà không phải chạy lại pipeline.
    """
    session_id: str = Field(
        description="ID phiên hội thoại. Client tự tạo (UUID) và giữ nguyên suốt cuộc trò chuyện."
    )
    user_message: str = Field(description="Câu hỏi của user cho lượt đầu tiên")
    assistant_message: str = Field(description="Nội dung phân tích dựng sẵn làm câu trả lời của trợ lý")