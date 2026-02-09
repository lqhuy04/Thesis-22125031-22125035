from agents.service import gemini
from state import AgentState
import time
            

def technical_analysis_agent(state: AgentState) -> AgentState:
    """Agent phân tích kĩ thuật"""
    
    time.sleep(4)

    prompt = f"""Phân tích kỹ thuật cho cổ phiếu {state['symbol']} dựa trên dữ liệu giá gần đây:
    {state['price_data']}
    
    Hãy phân tích:
    - Xu hướng giá (trend) trong giai đoạn này
    - Mức hỗ trợ và kháng cự
    - Khối lượng giao dịch và thanh khoản
    - Biên độ dao động giá
    - Các tín hiệu mua/bán tiềm năng
    
    Đưa ra nhận định ngắn từ 3-5 câu về xu hướng trong khoảng thời gian dữ liệu giá trên"""

    # result = gemini.generate_content(prompt);
    
    return {
        "technical_analysis": {
            "analysis" : 'VNM (Vinamilk) là doanh nghiệp đầu ngành sữa tại Việt Nam với thị phần lớn, thương hiệu mạnh và hệ thống phân phối rộng khắp. Về cơ bản, công ty có nền tảng tài chính lành mạnh, nợ thấp, dòng tiền ổn định và chính sách cổ tức tiền mặt đều đặn, phù hợp với nhà đầu tư dài hạn. Tuy nhiên, tốc độ tăng trưởng không còn cao do thị trường nội địa dần bão hòa và biên lợi nhuận có thể chịu áp lực từ biến động giá nguyên liệu. Nhìn chung, VNM mang tính phòng thủ, ổn định, ưu tiên bảo toàn vốn và thu nhập hơn là tăng trưởng đột biến.'}, 'technical_analysis': {'data': 'Dưới đây là phân tích kỹ thuật cho cổ phiếu VNM dựa trên dữ liệu giá gần đây:\n\n**1. Xu hướng giá (trend) trong giai đoạn này:**\n\n*   **Giai đoạn đầu (29/12/2025 - 05/01/2026):** VNM có xu hướng giảm nhẹ hoặc đi ngang, từ mức 62,100 xuống 60,300.\n*   **Giai đoạn tăng mạnh (06/01/2026 - 20/01/2026):** Cổ phiếu bắt đầu một xu hướng tăng giá rất mạnh mẽ và rõ rệt. Giá tăng từ 60,300 lên đỉnh 73,400, tạo ra các đỉnh cao hơn và đáy cao hơn. Đây là một đợt tăng trưởng ấn tượng với mức tăng khoảng 21.7% trong vòng chưa đầy 3 tuần.\n*   **Giai đoạn điều chỉnh (21/01/2026 - 28/01/2026):** Sau khi đạt đỉnh, VNM bước vào giai đoạn điều chỉnh. Giá giảm từ 73,400 xuống 67,200, sau đó dao động quanh mức 67,000 - 69,000. Xu hướng trong những ngày cuối cùng của dữ liệu là đi ngang hoặc giảm nhẹ, cho thấy áp lực bán vẫn còn nhưng đã chững lại.\n\n**2. Mức hỗ trợ và kháng cự:**\n\n*   **Mức hỗ trợ:**\n    *   **Hỗ trợ mạnh 1:** Vùng 60,000 - 60,300 (đáy của đợt giảm đầu tháng 1).\n    *   **Hỗ trợ hiện tại:** Vùng 67,000 - 67,200 (mức đáy mới nhất sau đợt điều chỉnh, cổ phiếu đang cố gắng giữ vững).\n    *   **Hỗ trợ tiềm năng:** Vùng 62,000 - 63,000 (mức kháng cự cũ đã bị phá vỡ, có thể trở thành hỗ trợ nếu giá giảm sâu hơn).\n*   **Mức kháng cự:**\n    *   **Kháng cự gần nhất:** Vùng 70,000 - 71,000 (mức giá VNM đã không thể vượt qua sau đợt điều chỉnh).\n    *   **Kháng cự mạnh:** Vùng 73,000 - 73,400 (đỉnh cao nhất của giai đoạn tăng giá).\n    *   **Kháng cự tâm lý:** Mức 75,000.\n\n**3. Khối lượng giao dịch và thanh khoản:**\n\n*   **Giai đoạn đầu (tháng 12/2025 - đầu tháng 1/2026):** Khối lượng giao dịch ở mức trung bình thấp (khoảng 1.5 triệu - 3 triệu cổ phiếu/ngày).\n*   **Giai đoạn tăng mạnh (giữa tháng 1/2026):** Khối lượng giao dịch tăng đột biến và duy trì ở mức rất cao, đặc biệt là vào các ngày:\n    *   14/01/2026: 24.8 triệu cổ phiếu (tăng giá mạnh)\n    *   15/01/2026: 19.2 triệu cổ phiếu (tăng giá)\n    *   20/01/2026: 21.5 triệu cổ phiếu (đạt đỉnh giá)\n    Điều này cho thấy dòng tiền lớn đã tham gia mạnh mẽ vào VNM trong đợt tăng giá.\n*   **Giai đoạn điều chỉnh (cuối tháng 1/2026):** Khối lượng giao dịch giảm dần so với đỉnh nhưng vẫn duy trì ở mức cao hơn so với giai đoạn đầu (khoảng 6 triệu - 16 triệu cổ phiếu/ngày). Điều này cho thấy áp lực bán ra chốt lời, nhưng khối lượng giảm trong khi giá giảm có thể là dấu hiệu tích cực hơn là sự tháo chạy hoảng loạn.\n*   **Thanh khoản:** VNM thể hiện thanh khoản rất cao trong giai đoạn này, đặc biệt là trong những ngày giá biến động mạnh, cho phép nhà đầu tư dễ dàng mua bán một lượng lớn cổ phiếu.\n\n**4. Biên độ dao động giá:**\n\n*   **Giai đoạn đầu:** Biên độ dao động giá hàng ngày tương đối hẹp (vài trăm đồng).\n*   **Giai đoạn tăng mạnh:** Biên độ dao động giá mở rộng đáng kể, với nhiều phiên có khoảng cách giữa giá cao nhất và thấp nhất lên tới hàng nghìn đồng (ví dụ: ngày 14/01 biên độ 4,300 đồng, ngày 20/01 biên độ 4,400 đồng). Điều này phản ánh sự hưng phấn và biến động mạnh của thị trường.\n*   **Giai đoạn điều chỉnh:** Biên độ vẫn duy trì ở mức tương đối rộng nhưng có xu hướng thu hẹp lại trong những ngày cuối dữ liệu, cho thấy sự ổn định hơn sau biến động mạnh.\n\n**5. Các tín hiệu mua/bán tiềm năng:**\n\n*   **Tín hiệu mua:**\n    *   Nếu VNM giữ vững được vùng hỗ trợ 67,000 - 67,200 và xuất hiện các nến đảo chiều tăng giá (ví dụ: Hammer, Engulfing Bullish) với khối lượng giao dịch tăng trở lại, có thể là tín hiệu mua.\n    *   Vượt qua vùng kháng cự 70,000 - 71,000 một cách thuyết phục với khối lượng lớn sẽ xác nhận xu hướng tăng trở lại.\n*   **Tín hiệu bán:**\n    *   Việc không thể vượt qua vùng 73,000 - 73,400 và xuất hiện các nến đảo chiều giảm giá (ví dụ: Shooting Star, Engulfing Bearish) với khối lượng lớn đã là tín hiệu bán/chốt lời.\n    *   Nếu VNM phá vỡ vùng hỗ trợ 67,000 - 67,200 với khối lượng lớn, đây sẽ là tín hiệu bán mạnh, có thể dẫn đến việc kiểm tra lại các mức hỗ trợ thấp hơn như 62,000 - 63,000.\n\n**Nhận định ngắn hạn (3-5 câu):**\n\nVNM vừa trải qua một đợt tăng giá mạnh mẽ, đạt đỉnh 73,400 vào ngày 20/01, sau đó điều chỉnh về vùng 67,000-68,000. Cổ phiếu đang tìm kiếm điểm cân bằng tại vùng hỗ trợ này, với khối lượng giao dịch đã giảm dần trong giai đoạn điều chỉnh. Trong ngắn hạn, VNM có thể tiếp tục dao động quanh vùng 67,000-70,000. Xu hướng tiếp theo sẽ phụ thuộc vào việc cổ phiếu có giữ vững được mốc hỗ trợ 67,000 hay không; nếu giữ được và có tín hiệu phục hồi, VNM có thể kiểm tra lại vùng 70,000-71,000.'
        },
        "completed_agents": ["technical_analysis_agent"]
    }
