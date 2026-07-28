"""Shared state contract for the v2 analysis graph."""

import operator
from typing import Annotated, Any, Literal

from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """State passed between nodes in the analysis pipeline."""

    mode: Literal["auto", "manual", "chat"]
    user_input: str
    risk_appetite: dict[str, Any]
    symbol: str
    data_selection: dict[str, Any]

    plan: dict[str, Any]
    agent_results: Annotated[dict[str, Any], operator.or_]

    final_output: Any
    error: str | None
