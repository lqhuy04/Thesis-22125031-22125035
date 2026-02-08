from state import AgentState
import time

def risk_appetite_agent(state: AgentState) -> AgentState:
    """Agent phân tích khẩu vị rủi ro"""
    
    print("Agent phân tích khẩu vị rủi ro - START")
    time.sleep(2)
    print("Agent phân tích khẩu vị rủi ro - RUNNING")
    print("Agent phân tích khẩu vị rủi ro - END")
    
    return {
        "completed_agents": ["risk_appetite_agent"]
    }