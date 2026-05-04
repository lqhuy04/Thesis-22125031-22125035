from langgraph.graph import StateGraph, END
from agentic_ai.state import AgentState
from agentic_ai.agents.orchestrator import orchestrator_agent
from agentic_ai.agents.aggregator import aggregator_agent
from agentic_ai.agents.article import article_agent
from agentic_ai.agents.fundamental_analysis import fundamental_analysis_agent
from agentic_ai.agents.technical_analysis import technical_analysis_agent

def route_to_agents(state: AgentState) -> list[str]:
    plan = state.get("plan", {})
    task_to_node = {
        "article_agent": "article_agent",
        "fundamental_analysis_agent": "fundamental_analysis_agent",
        "technical_analysis_agent": "technical_analysis_agent",
    }
    nodes = [task_to_node[t] for t in plan if t in task_to_node]
    print(f"[Router/Agents] Nodes: {nodes}")
    return nodes or ["aggregator"]

def build_analyze_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("orchestrator", orchestrator_agent)
    graph.add_node("article_agent", article_agent)
    graph.add_node("fundamental_analysis_agent", fundamental_analysis_agent)
    graph.add_node("technical_analysis_agent", technical_analysis_agent)
    graph.add_node("aggregator", aggregator_agent)

    graph.add_edge("__start__","orchestrator")

    graph.add_conditional_edges(
        "orchestrator",
        route_to_agents,
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