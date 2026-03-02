from typing import TypedDict, Annotated, Sequence
import operator

class AgentState(TypedDict):
    # ===== INPUT INFORMATION =====
    symbol: str
    company_name: str
    price_data: list
    news_data: list
    userProfile: dict
    
    # ===== FUNDAMENTAL ANALYSIS OUTPUT =====
    fundamental_analysis: dict

    # ===== TECHNICAL ANALYSIS OUTPUT =====
    technical_analysis: dict

    # ===== NEWS SENTIMENT OUTPUT =====
    news_analysis: dict

    # ===== RISK APPETITE OUTPUT =====
    risk_appetite: dict

    # ===== FINAL RECOMMENDATION OUTPUT =====
    recommendation: dict
    confidence: float

    # ===== AGENT COORDINATION =====
    current_agent: str
    completed_agents: Annotated[Sequence[str], operator.add]
    messages: Annotated[Sequence[str], operator.add]
    
    # ===== ERROR HANDLING =====
    errors: Annotated[Sequence[dict], operator.add]
    warnings: Annotated[Sequence[str], operator.add]