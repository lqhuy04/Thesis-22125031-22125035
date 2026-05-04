"""
state.py — Shared State cho toàn bộ LangGraph graph.
"""

from typing import Any, Annotated, Literal
import operator
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


# ─── State của từng intent job chạy song song ─────────────────────────────────

class IntentJob(TypedDict):
    """
    Một intent đơn lẻ được dispatch song song.
    Mỗi job có state riêng biệt, không chia sẻ với job khác.
    """
    # Input từ intent_classifier
    intent_type: str          # stock_analysis / market_index_analysis / ...
    sub_query: str            # câu hỏi con tương ứng với intent này
    symbol: str | None               # chỉ có giá trị với stock_analysis
    market_index: str | None  # chỉ có giá trị với market_index_analysis
    category: str | None      # chỉ có giá trị với category_analysis
    order: int                # thứ tự intent trong list → dùng để sắp xếp khi gộp

    # Thừa kế từ state cha (cần để các agent trong pipeline dùng)
    user_input: str
    risk_appetite: dict
    mode: Literal["chatbot", "api"]
    session_id: str
    messages: list

    # Output của job này sau khi xử lý xong
    plan: dict
    agent_results: Annotated[dict[str, Any], operator.or_]


# ─── State chính của toàn bộ graph ────────────────────────────────────────────

class AgentState(TypedDict):
    user_input: str                    # Câu hỏi gốc từ người dùng
    risk_appetite: dict                # Khẩu vị rủi ro
    symbol: str                        # Mã cổ phiếu (fallback nếu intent_classifier không extract được)
    mode: Literal["chatbot", "api"]    # "chatbot" → plain text, "api" → structured output
    session_id: str                    # ID phiên chat — dùng làm thread_id cho checkpointer

    # Kết quả phân loại từ intent_classifier
    intents: list[dict]                # list các SingleIntent đã được phân loại

    # API mode pipeline fields
    plan: dict                         # Kế hoạch do Orchestrator tạo (API mode)
    agent_results: Annotated[dict[str, Any], operator.or_]  # Kết quả sub-agents (API mode)

    # Kết quả từ các job song song — reset đầu mỗi turn, append trong turn
    sub_results: Annotated[list[dict], reset_each_turn]

    # Output cuối sau khi Reply Merger gộp lại
    final_output: Any

    error: str | None

    # Lịch sử hội thoại — add_messages tự động append
    messages: Annotated[list[BaseMessage], add_messages]