from agents.service import gemini
from state import AgentState
import time

def news_analysis_agent(state: AgentState) -> AgentState:
    """Agent phân tích tin tức"""
    
    time.sleep(4)

    prompt = f"""Tóm tắt tình hình tin tức cho cổ phiếu {state['symbol']} của {state['company_name']} dựa trên dữ liệu tin tức gần đây:
    {state['news_data']}
    
    Đưa ra nhận định ngắn từ 3-5 câu từ dữ liệu tin tức trên"""
    
    # result = gemini.generate_content(prompt); 
    
    return {
        "news_analysis": {
            "analysis": '**Tóm tắt tình hình tin tức cho cổ phiếu VNM:**\n\nVinamilk (VNM) đã công bố kết quả kinh doanh năm 2025 với doanh thu hợp nhất đạt mức cao nhất lịch sử là 63.724 tỷ đồng, tăng 3,1% so với cùng kỳ, nhờ vào kết quả tích cực của quý IV (tăng 10,1%). Động lực chính đến từ mảng kinh doanh quốc tế, đặc biệt là xuất khẩu, với doanh thu tăng mạnh 25,4% trong năm và ghi nhận 10 quý tăng trưởng liên tiếp. Kinh doanh nội địa cũng cho thấy sự phục hồi, tăng 7,8% trong quý IV. Lợi nhuận trước thuế và sau thuế quý IV tăng trưởng ấn tượng lần lượt 31,5% và 31,7%, nhờ biên lợi nhuận gộp cải thiện và chi phí bán hàng giảm. Tuy nhiên, lợi nhuận sau thuế hợp nhất cả năm 2025 giảm nhẹ so với năm 2024 do ảnh hưởng từ quý I, dù mức giảm đã được thu hẹp đáng kể. EPS năm 2025 đạt 4.028 đồng. Cổ phiếu VNM đã tăng hơn 2% trong phiên giao dịch ngày 2/2.\n\n**Nhận định:**\n\nVinamilk (VNM) đang thể hiện đà tăng trưởng mạnh mẽ với doanh thu kỷ lục năm 2025, được thúc đẩy chủ yếu bởi sự mở rộng hiệu quả ở thị trường quốc tế và xuất khẩu. Sự phục hồi của thị trường nội địa cùng với việc kiểm soát chi phí và cải thiện biên lợi nhuận đã giúp lợi nhuận quý IV tăng trưởng ấn tượng. Mặc dù lợi nhuận sau thuế cả năm có giảm nhẹ do ảnh hưởng từ quý đầu, nhưng kết quả tích cực từ các quý sau cho thấy công ty đang trên đà phát triển bền vững. Tình hình này phản ánh chiến lược kinh doanh hiệu quả và khả năng thích ứng tốt của VNM.',
        },
        "completed_agents": ["news_analysis_agent"]
    }