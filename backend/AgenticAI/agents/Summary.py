from agents.service import gemini
import stat
from state import AgentState

def summary_agent(state: AgentState) -> AgentState:
    """Agent tổng hợp, gợi ý"""
    
    prompt = f"""Dựa trên các phân tích sau đây cho cổ phiếu {state['symbol']} {state['company_name']}, hãy tổng hợp thành một báo cáo đầu tư hoàn chỉnh:

    PHÂN TÍCH CƠ BẢN:
    {state['fundamental_analysis']}
    
    PHÂN TÍCH KỸ THUẬT:
    {state['technical_analysis']}

    PHÂN TÍCH TIN TỨC:
    {state['news_analysis']}

    KHẨU VỊ RỦI RO: 
    {state['risk_appetite']}
    
    Hãy:
    1. Đánh giá rủi ro và cơ hội
    2. Đưa ra khuyến nghị đầu tư (Mua/Giữ/Bán) với lý do rõ ràng
    3. Đề xuất mức giá mục tiêu (nếu có thể)
    4. Các lưu ý quan trọng cho nhà đầu tư
    
    Định dạng trong một đoạn 4-5 câu."""

    result = gemini.generate_content(prompt);
    
    return {
        "recommendation": result,
        "completed_agents": ["summary_agent"]
    }