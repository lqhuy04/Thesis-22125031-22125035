"""
shared/state/chatbot_state.py — State dùng cho Chatbot pipeline (chat mode).
"""

import operator
from typing import Annotated, Any
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


def reset_each_turn(old: list, new: list) -> list:
    """
    Nếu new là list rỗng → reset (turn mới bắt đầu).
    Nếu new có phần tử → append vào old (các job song song đang ghi).
    """
    if not new:
        return []
    return old + new


class IntentJob(TypedDict):
    order: int
    
    intent: str
    user_input: str

    symbol: str | None
    market_index: str | None
    category: str | None
    
    # Pipeline fields
    plan: dict                         # Kế hoạch do Orchestrator tạo
    agent_results: Annotated[dict[str, Any], operator.or_]  # Kết quả sub-agents

    # Output cuối
    final_output: Any
    error: str | None


class ChatbotSystemState(TypedDict):
    user_input: str                    # Câu hỏi gốc từ người dùng
    risk_appetite: dict                # Khẩu vị rủi ro

    sub_results: Annotated[list[dict], reset_each_turn]

    intents: list[IntentJob]
    messages: Annotated[list[BaseMessage], add_messages]

    # Output cuối
    final_output: Any
    error: str | None