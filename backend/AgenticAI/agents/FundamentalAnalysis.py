from state import AgentState
import time

def fundamental_analysis_agent(state: AgentState) -> AgentState:
    """Agent phân tích cơ bản"""
    
    # Fetch DB lấy ra ptcb của mã
    time.sleep(2)
    
    return {
        "fundamental_analysis": "VNM (Vinamilk) là doanh nghiệp đầu ngành sữa tại Việt Nam với thị phần lớn, thương hiệu mạnh và hệ thống phân phối rộng khắp. Về cơ bản, công ty có nền tảng tài chính lành mạnh, nợ thấp, dòng tiền ổn định và chính sách cổ tức tiền mặt đều đặn, phù hợp với nhà đầu tư dài hạn. Tuy nhiên, tốc độ tăng trưởng không còn cao do thị trường nội địa dần bão hòa và biên lợi nhuận có thể chịu áp lực từ biến động giá nguyên liệu. Nhìn chung, VNM mang tính phòng thủ, ổn định, ưu tiên bảo toàn vốn và thu nhập hơn là tăng trưởng đột biến.",
        "completed_agents": ["fundamental_analysis_agent"]
    }
