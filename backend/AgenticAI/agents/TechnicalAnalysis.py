from agents.service import gemini
from state import AgentState
import time
            

def technical_analysis_agent(state: AgentState) -> AgentState:
    """Agent phân tích kĩ thuật"""
    
    time.sleep(4)

    prompt = f"""Phân tích kỹ thuật cho cổ phiếu {state['symbol']} dựa trên dữ liệu giá gần đây:
    {state['price_data']}
    
    Tóm tắt xu hướng giá, mức hỗ trợ/kháng cự và tín hiệu mua/bán tiềm năng trong 3-5 câu."""

    # result = gemini.generate_content(prompt)

    # print(result)
    return {
        "technical_analysis": {
           "analysis": "Cổ phiếu VNM đã có một đợt tăng giá mạnh mẽ từ đầu tháng 1/2026, đạt đỉnh 73.400 vào ngày 20/01/2026. Tuy nhiên, sau đó giá đã điều chỉnh xuống mức 68.000, cho thấy xu hướng giảm trong ngắn hạn. Mức kháng cự mạnh hiện tại nằm quanh vùng 73.000-75.000, trong khi mức hỗ trợ gần nhất là 67.200 và hỗ trợ mạnh hơn ở vùng 60.000-61.000. Với việc giá đang điều chỉnh sau đỉnh cùng khối lượng giao dịch vẫn còn cao, đây có thể là tín hiệu bán đối với nhà đầu tư ngắn hạn hoặc tín hiệu chờ mua khi giá tiếp cận các vùng hỗ trợ mạnh hơn.",
           "completed_agents": ["technical_analysis_agent"]
        }
    }
