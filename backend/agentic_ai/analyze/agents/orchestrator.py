"""
orchestrator.py — Orchestrator Agent với Structured Output (Pydantic)
"""
 
import json
from datetime import datetime
from typing import Literal
 
from pydantic import BaseModel, Field
from agentic_ai.service.openai_service import _get_openai_client
from agentic_ai.analyze.state import AgentState
from agentic_ai.analyze.horizon import interval_for
 
 
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
- Xác định interval phù hợp cho technical analysis (luôn luôn là nến ngày '1d')
- Sinh ra kế hoạch (plan) với tham số phù hợp cho từng agent

────────────────────────────
QUY TẮC CHỌN INTERVAL & KHOẢNG THỜI GIAN
────────────────────────────

Hệ thống chỉ sử dụng khung nến ngày (interval luôn luôn là '1d').
Dựa vào trường `period` trong khẩu vị rủi ro để xác định khoảng thời gian nhìn lại (from_date đến to_date):
- Ngắn hạn (vài ngày - vài tuần): interval = '1d', khoảng thời gian nhìn lại là 60 ngày gần nhất.
- Trung hạn (vài tháng): interval = '1d', khoảng thời gian nhìn lại từ 6 tháng đến 1 năm gần nhất (tương đương 180 đến 365 ngày).
- Dài hạn (> 1 năm): interval = '1d', khoảng thời gian nhìn lại từ 2 năm trở đi gần nhất (tối thiểu 730 ngày).

Quy tắc:
- `interval` luôn luôn truyền là '1d' vào technical_analysis_agent.
- `to_date` luôn = ngày hôm nay.
- `from_date` tính lùi từ `to_date` dựa vào số ngày nhìn lại tương ứng ở trên.
- Nếu không xác định được kỳ hạn hoặc không có thông tin → mặc định sử dụng kỳ hạn Trung hạn (interval = '1d', khoảng thời gian nhìn lại từ 180 đến 365 ngày).

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
 
    # Khung nến là hàm xác định của kỳ hạn (short→1d, mid→1w, long→1M). Ép cứng
    # bằng Python thay vì tin vào LLM, để mỗi kỳ hạn thực sự phân tích trên khung
    # nến khác nhau. DB chỉ có 1d; MarketService tự aggregate sang 1w/1M.
    period = (risk_appetite or {}).get("period")
    if period:
        plan_dict.setdefault("technical_analysis_agent", {})["interval"] = interval_for(period)

    print(f"[Orchestrator] Kế hoạch:\n{json.dumps(plan_dict, ensure_ascii=False, indent=2)}")
    return {"plan": plan_dict}