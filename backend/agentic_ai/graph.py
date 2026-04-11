"""
graph.py — Xây dựng LangGraph StateGraph
Định nghĩa các node, edge, và routing logic.
"""

from langgraph.graph import StateGraph, END

from state import AgentState
from agents.orchestrator import orchestrator_agent
from agents.aggregator import aggregator_agent
from agents.article import article_agent
from agents.fundamental_analysis import fundamental_analysis_agent
from agents.technical_analysis import technical_analysis_agent


# ─── Routing function ────────────────────────────────────────────────────────

def route_to_agents(state: AgentState) -> list[str]:
    """
    Conditional edge: Orchestrator quyết định agent nào sẽ chạy
    dựa trên plan đã tạo.

    Trả về danh sách tên node sẽ được gọi song song (Send API)
    hoặc tuần tự tuỳ thiết kế.
    """
    plan = state.get("plan", [])
    print(f"[Router] Routing theo plan: {plan}")

    # Map task name → node name trong graph
    task_to_node = {
        "task_a": "article_agent",
        "task_b": "fundamental_analysis_agent",
        "task_c": "technical_analysis_agent",
    }

    nodes_to_run = [task_to_node[task] for task in plan if task in task_to_node]

    if not nodes_to_run:
        print("[Router] Không tìm thấy agent phù hợp, chuyển thẳng đến aggregator.")
        return ["aggregator"]

    return nodes_to_run


# ─── Build graph ──────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """
    Khởi tạo và compile LangGraph StateGraph.
    """
    graph = StateGraph(AgentState)

    # Thêm các node
    graph.add_node("orchestrator", orchestrator_agent)
    graph.add_node("fundamental_analysis_agent", fundamental_analysis_agent)
    graph.add_node("technical_analysis_agent", technical_analysis_agent)
    graph.add_node("article_agent", article_agent)
    graph.add_node("aggregator", aggregator_agent)

    # Entry point
    graph.set_entry_point("orchestrator")

    # Conditional edge: sau orchestrator → routing
    graph.add_conditional_edges(
        "orchestrator",
        route_to_agents,
        {
            "fundamental_analysis_agent": "fundamental_analysis_agent",
            "technical_analysis_agent": "technical_analysis_agent",
            "article_agent": "article_agent",
            "aggregator": "aggregator",
        },
    )

    # Các sub-agent xong → tổng hợp
    graph.add_edge("fundamental_analysis_agent", "aggregator")
    graph.add_edge("technical_analysis_agent", "aggregator")
    graph.add_edge("article_agent", "aggregator")

    # Kết thúc
    graph.add_edge("aggregator", END)

    return graph.compile()