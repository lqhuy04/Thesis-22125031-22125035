"""
state.py — Shared State cho toàn bộ LangGraph graph.
"""
 
from typing import Any, Annotated, Literal
import operator
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
 
 
class AgentState(TypedDict):
    user_input: str               # Câu hỏi / yêu cầu gốc từ người dùng
    risk_appetite: dict           # Khẩu vị rủi ro
    symbol: str                   # Mã cổ phiếu (extract bởi intent_classifier hoặc truyền thủ công)
    mode: Literal["chatbot", "api"]  # "chatbot" → plain text, "api" → structured output
    session_id: str               # ID phiên chat — dùng làm thread_id cho checkpointer
    intent: dict                  # Kết quả từ intent_classifier {intent_type, symbol, instant_reply}
    plan: dict                    # Kế hoạch do Orchestrator tạo ra {agent_name: params}
    final_output: Any             # Structured dict (api) hoặc plain text (chatbot)
    error: str | None             # Lỗi nếu có
 
    # add_messages tự động append thay vì override — an toàn khi nhiều node ghi đồng thời
    messages: Annotated[list[BaseMessage], add_messages]
 
    # Nhiều sub-agent song song ghi → dùng operator.or_ để merge dict
    agent_results: Annotated[dict[str, Any], operator.or_]