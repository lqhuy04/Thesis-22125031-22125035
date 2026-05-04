"""
orchestrator.py — Orchestrator Agent với Structured Output (Pydantic)
"""
 
import json
from datetime import datetime
from typing import Literal
 
from pydantic import BaseModel, Field
from agentic_ai.service.openai_service import _get_openai_client
from agentic_ai.chatbot.state import AgentState
 
 
# ─── Schema định nghĩa output của LLM ────────────────────────────────────────
 
class ArticleAgentParams(BaseModel):
    from_date: str = Field(description="Ngày bắt đầu lấy tin tức, định dạng YYYY-MM-DD")
    to_date: str = Field(description="Ngày kết thúc lấy tin tức, định dạng YYYY-MM-DD")
 
 
class FundamentalAgentParams(BaseModel):
    indicators: list[Literal[
        # Valuation (định giá)
        "pe_ratio",
        "pb_ratio",
        "ps_ratio",

        # Profitability (khả năng sinh lời)
        "roe",
        "roa",
        "net_margin",
        "gross_margin",
        "ebit_margin",

        # Growth (tăng trưởng)
        "revenue_yoy",
        "profit_yoy",

        # Financial health (sức khỏe tài chính)
        "debt_to_equity",
        "current_ratio",
        "quick_ratio",
        "interest_coverage",

        # Efficiency (hiệu quả hoạt động)
        "asset_turnover",
        "inventory_turnover",
        "days_receivable",
        "days_payable",

        # Cash flow / core metrics
        "eps",
        "p_cash_flow",

        # Scale (quy mô – optional nhưng hữu ích)
        "market_cap"
    ]] = Field(description="Danh sách chỉ số cơ bản cần phân tích, chọn lọc theo kỳ vọng và khẩu vị rủi ro")
 
 
class TechnicalAgentParams(BaseModel):
    interval: Literal["1m", "5m", "15m", "30m", "1h", "1d", "1w", "1M"] = Field(description="Khung thời gian nến")
    from_date: str = Field(description="Ngày bắt đầu, định dạng YYYY-MM-DD")
    to_date: str = Field(description="Ngày kết thúc, định dạng YYYY-MM-DD")
    indicators: list[Literal[
        "sma_20", "sma_50", "rsi_14", "macd", "macd_signal",
        "macd_histogram", "bb_upper", "bb_middle", "bb_lower",
        "kdj_k", "kdj_d", "kdj_j"
    ]] = Field(description="Danh sách chỉ số kỹ thuật cần phân tích, chọn lọc theo kỳ vọng và khẩu vị rủi ro")
 
 
class OrchestratorPlan(BaseModel):
    article_agent: ArticleAgentParams = Field(
        description="Tham số cho agent thu thập tin tức"
    )
    fundamental_analysis_agent: FundamentalAgentParams = Field(
        description="Tham số cho agent phân tích cơ bản"
    )
    technical_analysis_agent: TechnicalAgentParams = Field(
        description="Tham số cho agent phân tích kỹ thuật"
    )
 
 
# ─── Prompt ──────────────────────────────────────────────────────────────────
 
ORCHESTRATOR_SYSTEM_PROMPT = """Bạn là orchestrator cho hệ thống phân tích đầu tư chứng khoán Việt Nam.
 
Nhiệm vụ: Đọc yêu cầu và khẩu vị rủi ro của nhà đầu tư, sau đó lên kế hoạch gọi các agent phân tích.
 
Quy tắc chọn indicator:
- Ngắn hạn (Dưới 1 năm) → from_date lùi 30 ngày, ưu tiên RSI, MACD, Volume
- Trung hạn (1–3 năm)   → from_date lùi 180 ngày, ưu tiên MA50, Bollinger_Bands
- Dài hạn  (Trên 3 năm) → from_date lùi 365 ngày, ưu tiên MA200, ATR
- Rủi ro thấp / vốn nhỏ → thêm pe_ratio, pb_ratio, debt_to_equity vào fundamental
- Kỳ vọng thu nhập thụ động → thêm dividend_yield, roe vào fundamental"""
 
ORCHESTRATOR_USER_PROMPT = """Hôm nay là {today}.
 
Yêu cầu: {user_input}
 
Khẩu vị rủi ro:
{risk_appetite}"""
 
 
# ─── Node ────────────────────────────────────────────────────────────────────
 
def orchestrator_agent(state: AgentState) -> dict:
    """Node chính: gọi LLM với Structured Output để tạo plan."""
    print(f"[Orchestrator] Nhận input: {state['user_input']}")
 
    client = _get_openai_client()
 
    risk_appetite = state.get("risk_appetite", {})
    symbol = state.get("symbol", "")  # Mặc định nếu không có
 
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT},
            {"role": "user", "content": ORCHESTRATOR_USER_PROMPT.format(
                today=datetime.today().strftime("%Y-%m-%d"),
                user_input=state["user_input"],
                risk_appetite=json.dumps(risk_appetite, ensure_ascii=False, indent=2),
                symbol=symbol
            )},
        ],
        response_format=OrchestratorPlan,   # Pydantic model truyền thẳng vào đây
    )
 
    plan: OrchestratorPlan = response.choices[0].message.parsed
 
    # Chuyển về dict để lưu vào AgentState
    plan_dict = plan.model_dump()
 
    print(f"[Orchestrator] Kế hoạch:\n{json.dumps(plan_dict, ensure_ascii=False, indent=2)}")
    return {"plan": plan_dict}