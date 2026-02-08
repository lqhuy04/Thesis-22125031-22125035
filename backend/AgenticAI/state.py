from typing import TypedDict, Annotated, Sequence
import operator

class AgentState(TypedDict):
    # ===== INPUT INFORMATION =====
    symbol: str
    company_name: str
    startTime: str
    endTime: str
    userProfile: dict
    
    # ===== FUNDAMENTAL ANALYSIS OUTPUT =====
    fundamental_analysis: dict

    # ===== TECHNICAL ANALYSIS OUTPUT =====
    technical_analysis: dict

    # ===== NEWS SENTIMENT OUTPUT =====
    news_sentiment: dict

    # ===== RISK APPETITE OUTPUT =====
    risk_appetite: dict

    # ===== FINAL RECOMMENDATION OUTPUT =====
    recommendation: dict

    # ===== AGENT COORDINATION =====
    current_agent: str
    completed_agents: Annotated[Sequence[str], operator.add]
    messages: Annotated[Sequence[str], operator.add]
    
    # ===== METADATA =====
    timestamp: str
    analysis_duration: float  # seconds
    data_sources: list  # Các nguồn dữ liệu đã sử dụng
    
    # ===== ERROR HANDLING =====
    errors: Annotated[Sequence[dict], operator.add]
    warnings: Annotated[Sequence[str], operator.add]