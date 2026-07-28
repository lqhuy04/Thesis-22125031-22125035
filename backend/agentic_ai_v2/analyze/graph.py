"""Base LangGraph topology for the v2 analysis pipeline."""

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


def build_graph() -> CompiledStateGraph:
    """Build the analysis graph with the same topology as agentic_ai."""
    graph = StateGraph(AgentState)

    graph.add_node("orchestrator", orchestrator_agent)
    graph.add_node("article_agent", article_agent)
    graph.add_node("fundamental_analysis_agent", fundamental_analysis_agent)
    graph.add_node("technical_analysis_agent", technical_analysis_agent)
    graph.add_node("aggregator", aggregator_agent)

    graph.add_edge(START, "orchestrator")

    graph.add_edge("orchestrator", "article_agent")
    graph.add_edge("orchestrator", "fundamental_analysis_agent")
    graph.add_edge("orchestrator", "technical_analysis_agent")

    graph.add_edge("article_agent", "aggregator")
    graph.add_edge("fundamental_analysis_agent", "aggregator")
    graph.add_edge("technical_analysis_agent", "aggregator")

    graph.add_edge("aggregator", END)

    return graph.compile()
