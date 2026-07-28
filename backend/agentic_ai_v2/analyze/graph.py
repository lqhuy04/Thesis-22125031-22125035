"""Base LangGraph topology for the v2 analysis pipeline."""

from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agentic_ai_v2.analyze.agents.aggregator import aggregator_agent
from agentic_ai_v2.analyze.agents.orchestrator import orchestrator_agent
from agentic_ai_v2.analyze.agents.article import article_agent
from agentic_ai_v2.analyze.agents.fundamental_analysis import (
    fundamental_analysis_agent,
)
from agentic_ai_v2.analyze.agents.technical_analysis import (
    technical_analysis_agent,
)
from agentic_ai_v2.analyze.state import AgentState


AnalysisRoute = Literal[
    "article_agent",
    "fundamental_analysis_agent",
    "technical_analysis_agent",
    "aggregator",
]


def _route_selected_agents(state: AgentState) -> list[AnalysisRoute]:
    """Select analysis branches from mode and the data_selection payload."""
    if state.get("mode") == "auto":
        return [
            "article_agent",
            "technical_analysis_agent",
            "fundamental_analysis_agent",
        ]

    selection = state.get("data_selection") or {}
    technical = selection.get("technical") or {}

    routes: list[AnalysisRoute] = []

    if selection.get("news") is True:
        routes.append("article_agent")

    if any(value is True for value in technical.values()):
        routes.append("technical_analysis_agent")

    if selection.get("fundamental") is True:
        routes.append("fundamental_analysis_agent")

    # The aggregator still finishes the graph when every data source is off.
    return routes or ["aggregator"]


def build_graph() -> CompiledStateGraph:
    """Build the analysis graph with conditional parallel analysis branches."""
    graph = StateGraph(AgentState)

    graph.add_node("orchestrator", orchestrator_agent)
    graph.add_node("article_agent", article_agent)
    graph.add_node("fundamental_analysis_agent", fundamental_analysis_agent)
    graph.add_node("technical_analysis_agent", technical_analysis_agent)
    graph.add_node("aggregator", aggregator_agent)

    graph.add_edge(START, "orchestrator")

    graph.add_conditional_edges(
        "orchestrator",
        _route_selected_agents,
        {
            "article_agent": "article_agent",
            "fundamental_analysis_agent": "fundamental_analysis_agent",
            "technical_analysis_agent": "technical_analysis_agent",
            "aggregator": "aggregator",
        },
    )

    graph.add_edge("article_agent", "aggregator")
    graph.add_edge("fundamental_analysis_agent", "aggregator")
    graph.add_edge("technical_analysis_agent", "aggregator")

    graph.add_edge("aggregator", END)

    return graph.compile()
