"""
state.py — Shared State cho toàn bộ LangGraph graph.
"""

from typing import Any, Annotated
import operator
from typing_extensions import TypedDict


class AgentState(TypedDict):
    user_input: str               # Câu hỏi / yêu cầu gốc từ người dùng
    risk_appetite: dict           # Khẩu vị rủi ro (truyền riêng để orchestrator dễ xử lý)
    symbol: str                   # Mã cổ phiếu (truyền riêng để các agent dễ xử lý)
    plan: dict                    # Kế hoạch do Orchestrator tạo ra {agent_name: params}
    final_output: str             # Output tổng hợp cuối cùng
    error: str | None             # Lỗi nếu có

    # Nhiều sub-agent song song ghi → dùng operator.or_ để merge dict
    agent_results: Annotated[dict[str, Any], operator.or_]