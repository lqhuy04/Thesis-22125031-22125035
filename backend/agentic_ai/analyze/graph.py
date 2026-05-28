from langgraph.graph import StateGraph, END
from agentic_ai.analyze.state import AgentState
from agentic_ai.analyze.agents.orchestrator import orchestrator_agent
from agentic_ai.analyze.agents.aggregator import aggregator_agent
from agentic_ai.analyze.nodes.article import article_agent
from agentic_ai.analyze.nodes.fundamental_analysis import fundamental_analysis_agent
from agentic_ai.analyze.nodes.technical_analysis import technical_analysis_agent

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("orchestrator", orchestrator_agent)
    # graph.add_node("article_agent", article_agent)
    # graph.add_node("fundamental_analysis_agent", fundamental_analysis_agent)
    graph.add_node("technical_analysis_agent", technical_analysis_agent)
    graph.add_node("aggregator", aggregator_agent)

    graph.add_edge("__start__","orchestrator")

    # graph.add_edge("orchestrator", "article_agent"),
    # graph.add_edge("orchestrator", "fundamental_analysis_agent"),
    graph.add_edge("orchestrator", "technical_analysis_agent"),

    # graph.add_edge("article_agent", "aggregator")
    # graph.add_edge("fundamental_analysis_agent", "aggregator")
    graph.add_edge("technical_analysis_agent", "aggregator")

    graph.add_edge("aggregator", END)

    return graph.compile()