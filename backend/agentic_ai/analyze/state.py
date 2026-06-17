"""
shared/state/analyze_state.py — State dùng cho Analyze pipeline (API mode).
"""

from typing import Any, Annotated, Literal
import operator
from typing_extensions import TypedDict


class AgentState(TypedDict):
    mode: Literal["auto", "manual","chat"]

    user_input: str                    # Câu hỏi gốc từ người dùng
    risk_appetite: dict                # Khẩu vị rủi ro

    symbol: str

    # Người dùng chọn nguồn/chỉ số dữ liệu cho AI phân tích (xem selection.py).
    # Thiếu → mặc định bật tất cả.
    data_selection: dict

    # Pipeline fields
    plan: dict                         # Kế hoạch do Orchestrator tạo
    agent_results: Annotated[dict[str, Any], operator.or_]  # Kết quả sub-agents

    # Output cuối
    final_output: Any
    error: str | None