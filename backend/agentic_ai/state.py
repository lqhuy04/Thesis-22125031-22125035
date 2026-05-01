"""
state.py — Shared State cho toàn bộ LangGraph graph.
"""

from typing import Any, Annotated, Literal
import operator
from typing_extensions import TypedDict


class AgentState(TypedDict):
    user_input: str               # Câu hỏi / yêu cầu gốc từ người dùng
    risk_appetite: dict           # Khẩu vị rủi ro
    symbol: str                   # Mã cổ phiếu (extract bởi intent_classifier hoặc truyền thủ công)
    mode: Literal["chatbot", "api"]  # "chatbot" → plain text, "api" → structured output
    intent: dict                  # Kết quả từ intent_classifier {intent_type, symbol, instant_reply}
    plan: dict                    # Kế hoạch do Orchestrator tạo ra {agent_name: params}
    final_output: Any             # Structured dict (api) hoặc plain text (chatbot)
    error: str | None             # Lỗi nếu có

    # Nhiều sub-agent song song ghi → dùng operator.or_ để merge dict
    agent_results: Annotated[dict[str, Any], operator.or_]