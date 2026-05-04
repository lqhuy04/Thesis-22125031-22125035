"""
state.py — Shared State cho toàn bộ LangGraph graph.
"""

from typing import Any, Annotated, Literal
import operator
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# ─── State chính của toàn bộ graph ────────────────────────────────────────────

class AgentState(TypedDict):
    mode: Literal["chat", "auto"]
    
    intent = str                       # Loại intent chính (dựa vào intent classifier)
    order: int                          # Thứ tự của sub-query trong một turn (dựa vào intent classifier)
    
    user_input: str                    # Câu hỏi gốc từ người dùng
    risk_appetite: dict                # Khẩu vị rủi ro

    symbol: str | None               
    market_index: str | None  
    category: str | None      

    # API mode pipeline fields
    plan: dict                         # Kế hoạch do Orchestrator tạo (API mode)
    agent_results: Annotated[dict[str, Any], operator.or_]  # Kết quả sub-agents (API mode)

    # Output cuối 
    final_output: Any

    error: str | None

def reset_each_turn(old: list, new: list) -> list:
    """
    Nếu new là list rỗng → reset (turn mới bắt đầu).
    Nếu new có phần tử → append vào old (các job song song đang ghi).
    """
    if not new:
        return []
    return old + new


class ChatbotSystemState(TypedDict):
    mode: Literal["chat", "api"]       # Chat mode hoặc API mode
    
    user_input: str                    # Câu hỏi gốc từ người dùng
    risk_appetite: dict                # Khẩu vị rủi ro
    
    sub_results: Annotated[list[dict], reset_each_turn]
    
    intents: list[dict]
    messages: Annotated[list[BaseMessage], add_messages]