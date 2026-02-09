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
    3. Đề xuất mức giá mục tiêu 
    4. Các lưu ý quan trọng cho nhà đầu tư
    
    Định dạng trong một đoạn 4-5 câu."""

    # result = gemini.generate_content(prompt);
    
    return {
        "recommendation": {
            "recommendation": 'Dựa trên các phân tích và khẩu vị rủi ro của bạn, dưới đây là báo cáo đầu tư chi tiết cho cổ phiếu VNM:\n\n**BÁO CÁO ĐẦU TƯ CỔ PHIẾU VNM**\n\nVinamilk (VNM) là một cổ phiếu phòng thủ vững chắc, dẫn đầu ngành sữa Việt Nam với nền tảng cơ bản mạnh mẽ, tài chính lành mạnh và dòng tiền ổn định. Các phân tích gần đây cho thấy công ty đang có đà tăng trưởng tích cực từ mảng kinh doanh quốc tế và sự phục hồi của thị trường nội địa, với doanh thu kỷ lục năm 2025 và lợi nhuận quý IV tăng trưởng ấn tượng, cho thấy khả năng thích ứng và chiến lược kinh doanh hiệu quả. Tuy nhiên, VNM có thể không mang lại tăng trưởng đột biến do thị trường nội địa dần bão hòa và áp lực biên lợi nhuận từ giá nguyên liệu, phù hợp hơn với nhà đầu tư tìm kiếm sự ổn định, bảo toàn vốn và thu nhập đều đặn.\n\nVề mặt kỹ thuật, VNM vừa trải qua một đợt tăng giá mạnh mẽ từ 60,300 lên 73,400, sau đó điều chỉnh về vùng 67,000-68,000. Cổ phiếu hiện đang tìm điểm cân bằng tại vùng hỗ trợ này, với khối lượng giao dịch đã giảm dần trong giai đoạn điều chỉnh, cho thấy áp lực bán đã chững lại. Đối với nhà đầu tư có kinh nghiệm trung cấp, khẩu vị rủi ro trung bình và mục tiêu tăng trưởng vốn dài hạn như bạn, việc VNM duy trì được vùng hỗ trợ 67,000 là yếu tố then chốt. Việc bạn đã nắm giữ VNM ở mức giá 85,000 đồng cũng cần được xem xét để tối ưu hóa vị thế.\n\n**Khuyến nghị đầu tư: GIỮ (Hold) và MUA THÊM (Accumulate) khi điều chỉnh.**\nVới vị thế hiện tại của bạn, khuyến nghị là tiếp tục **Giữ** cổ phiếu VNM. Đồng thời, bạn có thể cân nhắc **Mua thêm** (Accumulate) VNM nếu giá điều chỉnh về vùng hỗ trợ 67,000 - 67,200 hoặc sâu hơn là 62,000 - 63,000 với tín hiệu phục hồi rõ ràng. Lý do là VNM đang có kết quả kinh doanh tốt hơn kỳ vọng (đặc biệt là Q4 và mảng quốc tế), đồng thời xu hướng điều chỉnh kỹ thuật sau đợt tăng mạnh tạo cơ hội để bạn bình quân giá xuống và tăng lợi suất tiềm năng trong dài hạn, phù hợp với mục tiêu tăng trưởng vốn và khả năng "mua thêm khi thị trường giảm" của bạn.\n\n**Mức giá mục tiêu:**\nTrong trung hạn (6-12 tháng), chúng tôi đề xuất mức giá mục tiêu cho VNM là **78,000 - 82,000 VND**, dựa trên đà tăng trưởng doanh thu và lợi nhuận được củng cố, vị thế dẫn đầu thị trường và khả năng kiểm soát chi phí của công ty. Mức này cũng giúp bạn giảm thiểu khoản lỗ hiện tại và tiến gần hơn đến giá vốn trung bình ban đầu.\n\n**Các lưu ý quan trọng:**\nNhà đầu tư cần theo dõi sát sao biến động giá nguyên liệu đầu vào và tình hình cạnh tranh trên thị trường nội địa, cũng như tốc độ tăng trưởng của mảng xuất khẩu. Mặc dù VNM mang tính phòng thủ, không nên kỳ vọng tăng trưởng "nóng" hay đột biến. Việc phân bổ vốn không quá 15% cho một cổ phiếu như VNM (theo sở thích danh mục của bạn) là hợp lý để đảm bảo đa dạng hóa. Luôn duy trì quỹ dự phòng khẩn cấp và không sử dụng margin quá mức để tránh rủi ro khi thị trường biến động.'
        },
        "completed_agents": ["summary_agent"]
    }