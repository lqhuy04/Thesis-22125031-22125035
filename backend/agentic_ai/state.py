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


class ChatbotSystemState(TypedDict):
    user_input: str                    # Câu hỏi gốc từ người dùng
    risk_appetite: dict                # Khẩu vị rủi ro
    
    intents: list[dict]
    messages: Annotated[list[BaseMessage], add_messages]