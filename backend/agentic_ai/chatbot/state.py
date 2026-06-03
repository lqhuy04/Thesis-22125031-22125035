"""
agentic_ai/chatbot/state.py — State cho Chatbot (chat mode).

Đối đáp thông thường, không truy vấn DB, không chia intent.
Lịch sử hội thoại được LangGraph tự lưu/đọc qua SqliteSaver theo thread_id.
"""

from typing import Annotated, Any
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ChatbotState(TypedDict):
    user_input: str                                      # Tin nhắn mới từ user
    messages: Annotated[list[BaseMessage], add_messages]  # Lịch sử hội thoại (auto-merge)

    final_output: Any                                     # Reply trả về cho user
    error: str | None
