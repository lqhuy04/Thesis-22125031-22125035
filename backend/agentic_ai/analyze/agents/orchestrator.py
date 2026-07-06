"""
orchestrator.py — Orchestrator Agent với Structured Output (Pydantic)
"""
 
import json
from datetime import datetime

from pydantic import BaseModel, Field
from agentic_ai.service.openai_service import _get_openai_client
from agentic_ai.analyze.state import AgentState
from agentic_ai.analyze.horizon import interval_for


# ─── Schema định nghĩa output của LLM ────────────────────────────────────────
class ArticleAgentParams(BaseModel):
    from_date: str = Field(description="Ngày bắt đầu lấy tin tức, định dạng YYYY-MM-DD")
    to_date: str = Field(description="Ngày kết thúc lấy tin tức, định dạng YYYY-MM-DD")
class TechnicalAgentParams(BaseModel):
    # `interval` KHÔNG có ở đây: hệ thống luôn tự tính bằng interval_for(period)
    # trong orchestrator_agent (short→1d, mid→1w, long→1M), giá trị LLM chọn sẽ
    # luôn bị ghi đè nên không đáng để LLM tốn suy luận/token cho field này.
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
- Sinh ra kế hoạch (plan) với tham số phù hợp cho từng agent

────────────────────────────
QUY TẮC CHỌN KHOẢNG THỜI GIAN (from_date, to_date)
────────────────────────────

Dựa vào trường `period` trong khẩu vị rủi ro để xác định khoảng thời gian nhìn lại:
- Ngắn hạn (vài ngày - vài tuần): khoảng thời gian nhìn lại là 60 ngày gần nhất.
- Trung hạn (vài tháng): khoảng thời gian nhìn lại từ 6 tháng đến 1 năm gần nhất (tương đương 180 đến 365 ngày).
- Dài hạn (> 1 năm): khoảng thời gian nhìn lại từ 2 năm trở đi gần nhất (tối thiểu 730 ngày).

Quy tắc:
- `to_date` luôn = ngày hôm nay.
- `from_date` tính lùi từ `to_date` dựa vào số ngày nhìn lại tương ứng ở trên.
- Nếu không xác định được kỳ hạn hoặc không có thông tin → mặc định sử dụng kỳ hạn Trung hạn (khoảng thời gian nhìn lại từ 180 đến 365 ngày).

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
 
    # Khung nến là hàm xác định của kỳ hạn (short→1d, mid→1w, long→1M), luôn tính
    # bằng Python (không do LLM chọn). DB chỉ có 1d; MarketService tự aggregate
    # sang 1w/1M. Thiếu period → interval_for mặc định về 'mid' (1w).
    period = (risk_appetite or {}).get("period")
    plan_dict.setdefault("technical_analysis_agent", {})["interval"] = interval_for(period)

    print(f"[Orchestrator] Kế hoạch:\n{json.dumps(plan_dict, ensure_ascii=False, indent=2)}")
    return {"plan": plan_dict}