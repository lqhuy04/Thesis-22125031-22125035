"""
orchestrator.py — Orchestrator Agent với Structured Output (Pydantic)
"""
 
import json
from datetime import datetime
from typing import Literal
 
from pydantic import BaseModel, Field
from agentic_ai.service.openai_service import _get_openai_client
from agentic_ai.analyze.state import AgentState
 
 
# ─── Schema định nghĩa output của LLM ────────────────────────────────────────
class ArticleAgentParams(BaseModel):
    from_date: str = Field(description="Ngày bắt đầu lấy tin tức, định dạng YYYY-MM-DD")
    to_date: str = Field(description="Ngày kết thúc lấy tin tức, định dạng YYYY-MM-DD")
class TechnicalAgentParams(BaseModel):
    interval: Literal["1m", "5m", "15m", "30m", "1h", "1d", "1w", "1M"] = Field(
        description="Khung thời gian nến, chọn theo khẩu vị rủi ro"
    )
    from_date: str = Field(description="Ngày bắt đầu, định dạng YYYY-MM-DD")
    to_date: str = Field(description="Ngày kết thúc, định dạng YYYY-MM-DD")
 
 
class OrchestratorPlan(BaseModel):
    article_agent: ArticleAgentParams = Field(
        description="Tham số cho agent thu thập tin tức"
    )
    technical_analysis_agent: TechnicalAgentParams = Field(
        description="Tham số cho agent phân tích kỹ thuật"
    )
 
 
# ─── Prompt ──────────────────────────────────────────────────────────────────
ORCHESTRATOR_SYSTEM_PROMPT = """Bạn là orchestrator cho hệ thống phân tích đầu tư chứng khoán Việt Nam.

Nhiệm vụ:
- Đọc yêu cầu của người dùng và khẩu vị rủi ro
- Xác định khoảng thời gian cần phân tích (from_date, to_date)
- Xác định interval phù hợp cho technical analysis
- Sinh ra kế hoạch (plan) với tham số phù hợp cho từng agent

────────────────────────────
QUY TẮC CHỌN INTERVAL & KHOẢNG THỜI GIAN
────────────────────────────

Dựa vào trường `period` trong khẩu vị rủi ro:

┌─────────────┬──────────────┬──────────────────────────────┐
│ Kỳ hạn      │ interval     │ Khoảng thời gian nhìn lại    │
├─────────────┼──────────────┼──────────────────────────────┤
│ Ngắn hạn    │ 1h           │ 60 ngày gần nhất             │
│ (vài ngày   │ (xác nhận:   │ (đủ chi tiết cho swing,      │
│ – vài tuần) │  1d)         │  không quá nhiễu)            │
├─────────────┼──────────────┼──────────────────────────────┤
│ Trung hạn   │ 1d           │ 180 ngày gần nhất            │
│ (vài tháng) │ (xác nhận:   │ (bao phủ 1–2 chu kỳ ngành)   │
│             │  1w)         │                              │
├─────────────┼──────────────┼──────────────────────────────┤
│ Dài hạn     │ 1w           │ 365 ngày gần nhất            │
│ (> 1 năm)   │ (xác nhận:   │ (nhìn thấy xu hướng lớn,     │
│             │  1M)         │  lọc nhiễu ngắn hạn)         │
└─────────────┴──────────────┴──────────────────────────────┘

Quy tắc:
- `interval` là khung chính — truyền vào technical_analysis_agent
- `to_date` luôn = ngày hôm nay
- `from_date` tính lùi theo bảng trên
- Nếu `investment_horizon` không có → mặc định mid_term (1d, 180 ngày)

────────────────────────────
NGUYÊN TẮC QUAN TRỌNG
────────────────────────────

- Không suy đoán symbol nếu không có trong input
- Các ngày phải đúng format YYYY-MM-DD
- Luôn gọi đủ cả 3 agent: article, fundamental, technical
"""
 
ORCHESTRATOR_USER_PROMPT = """Hôm nay là {today}.
 
Yêu cầu: {user_input}
 
Khẩu vị rủi ro:
{risk_appetite}"""
 
 
# ─── Node ────────────────────────────────────────────────────────────────────
 
def orchestrator_agent(state: AgentState) -> dict:
    """Node chính: gọi LLM với Structured Output để tạo plan."""
    print(f"[Orchestrator] Nhận mode: {state['mode']}")
    print(f"[Orchestrator] Nhận input: {state['user_input']}")
    print(f"[Orchestrator] Nhận risk_appetite: {state['risk_appetite']}")

    if (state['mode'] == "manual" and state["plan"] != None):
        print(f"[Orchestrator] Chế độ thủ công")
        print(f"[Orchestrator] Sử dụng plan của user: {state['plan']}")
        return {}
 
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