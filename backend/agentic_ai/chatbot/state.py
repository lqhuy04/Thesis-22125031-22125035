"""
agentic_ai/chatbot/state.py — State cho Chatbot (chat mode).

Luồng: intent_classifier → (chat | qa | market | END)
Lịch sử hội thoại được LangGraph tự lưu/đọc qua PostgresSaver theo thread_id.
"""

from typing import Annotated, Any
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ChatbotState(TypedDict):
    user_input: str                                       # Tin nhắn mới từ user
    messages: Annotated[list[BaseMessage], add_messages]  # Lịch sử hội thoại (auto-merge)

    # Intent được phân loại bởi intent_classifier_agent
    # Giá trị: OUT_OF_SCOPE | GREETING | KNOWLEDGE_QA | MARKET_QUERY
    intent: str | None

    # Trace cho luồng MARKET_QUERY (market_agent) — phục vụ debug, không bắt buộc
    generated_sql: str | None                             # Câu SQL do LLM sinh ra
    query_result: Any                                     # Rows trả về từ DB (đã cắt bớt)

    final_output: Any                                     # Reply trả về cho user
    error: str | None
