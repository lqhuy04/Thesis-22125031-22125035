from state import AgentState
import time

def fundamental_analysis_agent(state: AgentState) -> AgentState:
    """Agent phân tích cơ bản"""
    
    print("Agent phân tích cơ bản - START")

    # Fetch DB lấy ra ptcb của mã
    print("Agent phân tích cơ bản - RUNNING")
    time.sleep(3)

    print("Agent phân tích cơ bản - END")
    
    return {
        "fundamental_analysis": {
            "content": "VNM (Vinamilk) là doanh nghiệp đầu ngành sữa..."
        },
        "completed_agents": ["fundamental_analysis_agent"]
    }
