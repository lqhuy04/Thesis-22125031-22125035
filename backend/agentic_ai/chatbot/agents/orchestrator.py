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

Nhiệm vụ:
- Đọc yêu cầu của người dùng và khẩu vị rủi ro
- Xác định cần gọi những agent nào
- Sinh ra kế hoạch (plan) với tham số phù hợp cho từng agent

────────────────────────────
GIẢI THÍCH & CÁCH DÙNG INDICATORS
────────────────────────────

1. VALUATION (ĐỊNH GIÁ)

- pe_ratio (Price / Earnings):
  + Ý nghĩa: Nhà đầu tư đang trả bao nhiêu cho 1 đồng lợi nhuận
  + Dùng khi:
    - So sánh cổ phiếu cùng ngành
    - Tìm cổ phiếu bị định giá thấp (value investing)
  + Insight:
    - PE thấp ≠ rẻ (có thể doanh nghiệp đang suy giảm)
    - PE cao hợp lý nếu tăng trưởng mạnh

- pb_ratio (Price / Book):
  + Ý nghĩa: Giá so với giá trị sổ sách
  + Dùng khi:
    - Ngành tài chính, ngân hàng, bất động sản
  + Insight:
    - PB < 1 có thể undervalued hoặc có vấn đề tài sản

- ps_ratio (Price / Sales):
  + Ý nghĩa: Giá so với doanh thu
  + Dùng khi:
    - Công ty chưa có lợi nhuận (startup, growth)
  + Insight:
    - PS cao cần đi kèm tăng trưởng doanh thu mạnh

────────────────────────────
2. PROFITABILITY (SINH LỜI)

- roe (Return on Equity):
  + Hiệu quả sử dụng vốn chủ
  + Dùng khi:
    - Đánh giá doanh nghiệp chất lượng cao
  + Insight:
    - ROE > 15% thường là tốt

- roa (Return on Assets):
  + Hiệu quả sử dụng tài sản
  + Dùng khi:
    - So sánh doanh nghiệp có cấu trúc tài sản khác nhau

- net_margin:
  + Biên lợi nhuận ròng
  + Insight:
    - Margin cao → doanh nghiệp có lợi thế cạnh tranh

- gross_margin:
  + Biên lợi nhuận gộp
  + Dùng khi:
    - Phân tích sức mạnh pricing

- ebit_margin:
  + Lợi nhuận từ hoạt động kinh doanh chính
  + Dùng khi:
    - Loại bỏ ảnh hưởng tài chính/thuế

────────────────────────────
3. GROWTH (TĂNG TRƯỞNG)

- revenue_yoy:
  + Tăng trưởng doanh thu
  + Dùng khi:
    - Tìm cổ phiếu growth

- profit_yoy:
  + Tăng trưởng lợi nhuận
  + Insight:
    - Profit tăng nhanh hơn revenue → hiệu quả cải thiện

────────────────────────────
4. FINANCIAL HEALTH (SỨC KHỎE TÀI CHÍNH)

- debt_to_equity:
  + Đòn bẩy tài chính
  + Dùng khi:
    - Đánh giá rủi ro phá sản
  + Insight:
    - Cao → rủi ro cao nhưng có thể tăng trưởng nhanh

- current_ratio:
  + Khả năng trả nợ ngắn hạn
  + >1 là an toàn

- quick_ratio:
  + Giống current nhưng loại hàng tồn kho
  + Dùng khi:
    - Ngành tồn kho lớn

- interest_coverage:
  + Khả năng trả lãi vay
  + <1.5 là nguy hiểm

────────────────────────────
5. EFFICIENCY (HIỆU QUẢ HOẠT ĐỘNG)

- asset_turnover:
  + Doanh thu / tài sản
  + Dùng khi:
    - Đánh giá hiệu quả sử dụng tài sản

- inventory_turnover:
  + Vòng quay hàng tồn kho
  + Dùng khi:
    - Retail, sản xuất

- days_receivable:
  + Số ngày thu tiền khách
  + Cao → dòng tiền xấu

- days_payable:
  + Số ngày trả tiền nhà cung cấp
  + Cao → doanh nghiệp tận dụng tín dụng tốt

────────────────────────────
6. CASHFLOW / CORE

- eps:
  + Lợi nhuận trên mỗi cổ phiếu
  + Dùng khi:
    - So sánh trực tiếp cổ phiếu

- p_cash_flow:
  + Giá / dòng tiền
  + Insight:
    - Khó bị "làm đẹp" hơn lợi nhuận

────────────────────────────
7. SCALE

- market_cap:
  + Quy mô công ty
  + Dùng khi:
    - Phân loại large-cap / mid-cap / small-cap

────────────────────────────
8. TECHNICAL INDICATORS

- sma_20 / sma_50:
  + Trung bình giá
  + Dùng khi:
    - Xác định xu hướng
  + Insight:
    - Giá > SMA → uptrend

- rsi_14:
  + Động lượng (0–100)
  + >70: quá mua
  + <30: quá bán
  + Dùng khi:
    - Trading ngắn hạn

- macd / signal / histogram:
  + Xu hướng + động lượng
  + Dùng khi:
    - Xác nhận điểm mua/bán

- bollinger bands:
  + Độ biến động
  + Dùng khi:
    - Breakout / mean reversion

- kdj:
  + Dao động nhanh hơn RSI
  + Dùng khi:
    - Trading rủi ro cao

────────────────────────────
QUY TẮC CHỌN INDICATOR
────────────────────────────

1. Theo thời gian đầu tư:

- Ngắn hạn (Dưới 1 năm):
  + from_date = today - 30 ngày
  + Ưu tiên:
    - rsi_14
    - macd, macd_signal, macd_histogram

- Trung hạn (1–3 năm):
  + from_date = today - 180 ngày
  + Ưu tiên:
    - sma_50
    - bb_upper, bb_middle, bb_lower

- Dài hạn (Trên 3 năm):
  + from_date = today - 365 ngày
  + Ưu tiên:
    - sma_50

────────────────────────────
2. Theo khẩu vị rủi ro:

- Rủi ro thấp:
  + pe_ratio, pb_ratio
  + debt_to_equity
  + current_ratio, quick_ratio

- Rủi ro trung bình:
  + roe, revenue_yoy
  + kết hợp sma + macd

- Rủi ro cao:
  + rsi_14
  + macd
  + kdj_k, kdj_d, kdj_j

────────────────────────────
3. Theo mục tiêu:

- Thu nhập thụ động:
  + roe
  + net_margin

- Tăng trưởng:
  + revenue_yoy
  + profit_yoy

- An toàn:
  + debt_to_equity
  + current_ratio
  + quick_ratio

────────────────────────────
NGUYÊN TẮC QUAN TRỌNG
────────────────────────────

- Có thể chọn 1, 2 hoặc cả 3 agent
- Không giới hạn số agent nếu cần thiết
- Không chọn agent nếu không liên quan
- Nếu không đủ thông tin → trả về None

- Không suy đoán symbol nếu không có trong input
- Các ngày phải đúng format YYYY-MM-DD
- indicators phải thuộc danh sách hợp lệ trong schema

- Ưu tiên kế hoạch đủ dùng, không over-engineer
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