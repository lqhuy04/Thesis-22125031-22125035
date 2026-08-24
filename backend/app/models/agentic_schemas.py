"""
app/models/agentic_schemas.py
Request / Response schemas cho agentic AI endpoints.
"""

from typing import Literal
from pydantic import BaseModel, Field, model_validator


# ─── Shared ───────────────────────────────────────────────────────────────────

class RiskAppetite(BaseModel):
    period: Literal["short_term", "mid_term", "long_term"] = Field(
        description="Kỳ hạn đầu tư: short_term, mid_term hoặc long_term"
    )


# ─── Data selection (toggle nguồn dữ liệu cho AI) ──────────────────────────────

class TechnicalSelection(BaseModel):
    """Bật/tắt từng chỉ số kỹ thuật mà AI được phép phân tích."""
    ma: bool = Field(default=True, description="Đường trung bình động (MA/SMA20, SMA50)")
    boll: bool = Field(default=True, description="Bollinger Bands")
    rsi: bool = Field(default=True, description="Chỉ số sức mạnh tương đối RSI")
    macd: bool = Field(default=True, description="MACD")
    kdj: bool = Field(default=True, description="KDJ")


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
    """Data-source selection for the public v2 analysis endpoint."""
    news: bool = Field(default=True, description="Tin tức / sentiment bài viết")
    technical: TechnicalSelection = Field(default_factory=TechnicalSelection)
    fundamental: bool = Field(
        default=True,
        description="Bật hoặc tắt toàn bộ phân tích cơ bản",
    )
    weight: WeightSelection | None = Field(
        default=None,
        description="Trọng số thủ công cho news/technical/fundamental. Bỏ trống = dùng mặc định theo kỳ hạn.",
    )

    @model_validator(mode="after")
    def _require_technical_indicator(self):
        if not any(self.technical.model_dump().values()):
            raise ValueError(
                "Phân tích kỹ thuật phải bật ít nhất một chỉ báo"
            )
        return self


# ─── /analyze (API mode) ──────────────────────────────────────────────────────

class StockAnalysisRequest(BaseModel):
    mode: Literal["auto", "manual"] = Field(description="Chế độ tự động(auto) hoặc thủ công(manual)")
    symbol: str = Field(min_length=1, max_length=16, pattern=r"^[A-Za-z0-9._-]+$", description="Mã cổ phiếu, ví dụ: VNM, FPT, VIC")
    language: Literal["vi", "en"] = Field(
        default="vi",
        description="Ngôn ngữ kết quả phân tích theo cài đặt app: vi hoặc en",
    )
    risk_appetite: RiskAppetite
    data_selection: DataSelection = Field(
        default_factory=DataSelection,
        description="Chọn nguồn/chỉ số dữ liệu cho AI phân tích. Bỏ trống = bật tất cả.",
    )


# ─── /experiments/analyze (Stockrium Lab) ──────────────────────────────────────────

class ExperimentAnalysisRequest(BaseModel):
    """Yêu cầu phân tích thử nghiệm cho một mã hoặc rổ chỉ số."""
    experiment_name: str | None = Field(default=None, max_length=160)
    mode: Literal["auto", "manual"] = Field(description="Chế độ tự động(auto) hoặc thủ công(manual)")
    universe: Literal["VN30", "VN100"] | None = Field(
        default=None,
        description="Rổ phân tích: 'VN30' | 'VN100'. Bỏ trống = phân tích 1 mã (symbol).",
    )
    symbol: str | None = Field(
        default=None,
        min_length=1,
        max_length=16,
        pattern=r"^[A-Za-z0-9._-]+$",
        description="Mã cổ phiếu khi không dùng rổ, ví dụ: VNM, FPT, VIC",
    )
    risk_appetite: RiskAppetite
    data_selection: DataSelection = Field(
        default_factory=DataSelection,
        description="Chọn nguồn/chỉ số dữ liệu cho AI phân tích. Bỏ trống = bật tất cả.",
    )


# Backward-compatible import for older clients/tests during the API rename.
AdminAnalysisRequest = ExperimentAnalysisRequest


# ─── /chat (Chatbot mode) ─────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str = Field(
        min_length=36,
        max_length=36,
        pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$",
        description="ID phiên hội thoại. Client tự tạo (UUID) và giữ nguyên suốt cuộc trò chuyện."
    )
    message: str = Field(min_length=1, max_length=4000, description="Tin nhắn của user")


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
        min_length=36,
        max_length=36,
        pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$",
        description="ID phiên hội thoại. Client tự tạo (UUID) và giữ nguyên suốt cuộc trò chuyện."
    )
    user_message: str = Field(min_length=1, max_length=4000, description="Câu hỏi của user cho lượt đầu tiên")
    assistant_message: str = Field(min_length=1, max_length=20000, description="Nội dung phân tích dựng sẵn làm câu trả lời của trợ lý")
