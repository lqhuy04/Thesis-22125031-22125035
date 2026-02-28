from agents.service import gemini
from state import AgentState
import time

def news_analysis_agent(state: AgentState) -> AgentState:
    """Agent phân tích tin tức"""
    
    time.sleep(4)

    prompt = f"""Tóm tắt tình hình tin tức cho cổ phiếu {state['symbol']} của {state['company_name']} dựa trên dữ liệu tin tức gần đây:
    {state['news_data']}
    
    Nhận định trong 3-5 câu về tác động của các tin tức này đến cổ phiếu."""
    
    # result = gemini.generate_content(prompt)
    
    return {
        "news_analysis": "Vinamilk (VNM) đã công bố kết quả kinh doanh ấn tượng cho năm 2025 với doanh thu hợp nhất đạt mức cao nhất lịch sử 63.724 tỷ đồng, tăng 3,1%, và lợi nhuận sau thuế quý IV tăng mạnh 31,7%. Sự tăng trưởng này được thúc đẩy bởi hoạt động kinh doanh quốc tế và xuất khẩu, vốn duy trì đà tăng trưởng dương 10 quý liên tiếp, cùng với sự phục hồi của thị trường nội địa. Biên lợi nhuận gộp hợp nhất quý IV cũng cải thiện, đạt 40,4% nhờ quy mô doanh thu mở rộng và giá nguyên liệu ổn định. Những thông tin tích cực này cho thấy triển vọng kinh doanh khả quan của công ty, đã tác động tích cực đến giá cổ phiếu VNM, khiến mã này tăng hơn 2% trong phiên giao dịch gần nhất.",
        "completed_agents": ["news_analysis_agent"]
    }