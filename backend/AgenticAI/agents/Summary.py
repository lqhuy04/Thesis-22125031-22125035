from agents.service import gemini
import stat
from state import AgentState

def summary_agent(state: AgentState) -> AgentState:
    """Agent tổng hợp, gợi ý"""
    
    prompt = f"""Dựa trên các phân tích sau đây cho cổ phiếu {state['symbol']} {state['company_name']}, hãy tổng hợp và đưa ra khuyến nghị đầu tư:

    PHÂN TÍCH CƠ BẢN:
    {state['fundamental_analysis']}
    
    PHÂN TÍCH KỸ THUẬT:
    {state['technical_analysis']}

    PHÂN TÍCH TIN TỨC:
    {state['news_analysis']}

    KHẨU VỊ RỦI RO: 
    {state['risk_appetite']}
    
    Đưa ra khuyến nghị (Mua/Giữ/Bán), mức giá mục tiêu và lý do trong 3-5 câu."""

    # result = gemini.generate_content(prompt)
    
    return {
        "recommendation": {
            "recommendation": "Khuyến nghị \"Giữ\" đối với cổ phiếu VNM do đây là doanh nghiệp đầu ngành có nền tảng tài chính vững chắc, dòng tiền ổn định và chính sách cổ tức đều đặn. Kết quả kinh doanh năm 2025 rất tích cực với doanh thu và lợi nhuận tăng trưởng ấn tượng, củng cố triển vọng dài hạn của công ty. Mặc dù giá cổ phiếu đang điều chỉnh trong ngắn hạn, đây có thể là cơ hội tốt để tích lũy thêm ở các vùng hỗ trợ mạnh đối với nhà đầu tư dài hạn như bạn. Với khẩu vị rủi ro vừa phải và tầm nhìn dài hạn, VNM là lựa chọn ổn định trong danh mục. Mức giá mục tiêu trong trung và dài hạn có thể đạt quanh 78.000 - 80.000 VND, giúp phục hồi vị thế hiện tại và đạt được tăng trưởng vốn ổn định."
        },
        "completed_agents": ["summary_agent"]
    }