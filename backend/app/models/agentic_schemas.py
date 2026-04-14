"""
app/models/agentic_schema.py
Request / Response schemas riêng cho agentic AI endpoints.
"""

from typing import Literal
from pydantic import BaseModel, Field


# ─── Request ──────────────────────────────────────────────────────────────────

class RiskAppetite(BaseModel):
    capital_ratio: str = Field(description="Tỷ lệ vốn, ví dụ: 'Dưới 10%'")
    comfort_zone: str = Field(description="Ngưỡng lợi nhuận / lỗ chấp nhận được")
    expectation: str = Field(description="Kỳ vọng đầu tư")
    experience: str = Field(description="Kinh nghiệm của nhà đầu tư")
    period: str = Field(description="Kỳ hạn đầu tư, ví dụ: 'Ngắn hạn (Dưới 1 năm)'")


class StockAnalysisRequest(BaseModel):
    symbol: str = Field(description="Mã cổ phiếu, ví dụ: VNM, FPT, VIC")
    risk_appetite: RiskAppetite


# ─── Output của LLM (Structured Output) ──────────────────────────────────────

class InvestmentRecommendation(BaseModel):
    summary: str = Field(
        description="Phân tích tổng thể đầy đủ về tình hình cổ phiếu từ 3 nguồn: tin tức, phân tích cơ bản, kỹ thuật"
    )
    recommendation: Literal["Mua", "Giữ", "Chờ", "Bán"] = Field(
        description="Hành động đề xuất"
    )
    reasoning: str = Field(
        description="Giải thích cho recommendation từ khẩu vị rủi ro của user, kết hợp dẫn chứng số liệu từ các nguồn phân tích"
    )
    confidence: float = Field(
        description="Độ tin cậy từ 0 đến 1",
        ge=0,
        le=1,
    )
