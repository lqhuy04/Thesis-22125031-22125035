"""
state.py — Định nghĩa Shared State dùng chung cho toàn bộ graph
"""

from typing import Any, Annotated
import operator
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """
    Trạng thái chia sẻ giữa tất cả các node trong LangGraph.
    Mỗi agent đọc và ghi vào đây.
    """
    user_input: str                    # Input gốc từ người dùng
    plan: dict[str, Any]               # Danh sách sub-task do Orchestrator lên kế hoạch
    agent_results: Annotated[dict[str, Any], operator.or_]      # Kết quả trả về từ từng sub-agent {agent_name: result}
    final_output: str                  # Output tổng hợp cuối cùng
    error: str | None                  # Ghi nhận lỗi nếu có