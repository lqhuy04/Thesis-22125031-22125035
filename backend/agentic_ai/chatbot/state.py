"""
shared/state/chatbot_state.py — State dùng cho Chatbot pipeline (chat mode).
"""

from typing import Annotated, Any
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from agentic_ai.analyze.state import AgentState


def reset_each_turn(old: list, new: list) -> list:
    """
    Nếu new là list rỗng → reset (turn mới bắt đầu).
    Nếu new có phần tử → append vào old (các job song song đang ghi).
    """
    if not new:
        return []
    return old + new

class IntentJob(TypedDict):
    intent: str
    order: int
    state: AgentState


class ChatbotSystemState(TypedDict):
    user_input: str                    # Câu hỏi gốc từ người dùng
    risk_appetite: dict                # Khẩu vị rủi ro

    sub_results: Annotated[list[dict], reset_each_turn]

    intents: list[IntentJob]
    messages: Annotated[list[BaseMessage], add_messages]

    # Output cuối
    final_output: Any
    error: str | None