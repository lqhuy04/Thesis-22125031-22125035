"""
graph.py — Xây dựng LangGraph StateGraph
Định nghĩa các node, edge, và routing logic.
"""

from langgraph.graph import StateGraph, END

from agentic_ai.state import AgentState
from agentic_ai.agents.intent_classifier import intent_classifier_agent
from agentic_ai.agents.orchestrator import orchestrator_agent
from agentic_ai.agents.aggregator import aggregator_agent
from agentic_ai.agents.article import article_agent
from agentic_ai.agents.fundamental_analysis import fundamental_analysis_agent
from agentic_ai.agents.technical_analysis import technical_analysis_agent


# ─── Routing: entry point ────────────────────────────────────────────────────

def route_entry(state: AgentState) -> str:
    """
    mode = "api"     → skip intent_classifier, vào thẳng orchestrator
    mode = "chatbot" → qua intent_classifier trước
    """
    mode = state.get("mode", "api")
    print(f"[Router/Entry] mode = {mode}")
    return "orchestrator" if mode == "api" else "intent_classifier"


# ─── Routing: sau Intent Classifier ──────────────────────────────────────────

def route_after_intent(state: AgentState) -> str:
    """
    Nếu intent_type = 'stock_analysis' → vào pipeline chính (orchestrator).
    Còn lại (general_question / clarification / out_of_scope) → kết thúc luôn,
    instant_reply đã có sẵn trong state["intent"].
    """
    intent_type = state.get("intent", {}).get("intent_type", "out_of_scope")
    print(f"[Router/Intent] intent_type = {intent_type}")

    if intent_type == "stock_analysis":
        return "orchestrator"
    return "end"


# ─── Routing: sau Orchestrator → các sub-agent ───────────────────────────────

def route_to_agents(state: AgentState) -> list[str]:
    """
    Conditional edge: Orchestrator quyết định agent nào sẽ chạy
    dựa trên plan đã tạo.
    """
    plan = state.get("plan", {})
    print(f"[Router/Agents] Routing theo plan: {plan}")

    task_to_node = {
        "article_agent": "article_agent",
        "fundamental_analysis_agent": "fundamental_analysis_agent",
        "technical_analysis_agent": "technical_analysis_agent",
    }

    nodes_to_run = [task_to_node[task] for task in plan if task in task_to_node]
    print(f"[Router/Agents] Các node được chọn: {nodes_to_run}")

    if not nodes_to_run:
        print("[Router/Agents] Không tìm thấy agent phù hợp, chuyển thẳng đến aggregator.")
        return ["aggregator"]

    return nodes_to_run


# ─── Build graph ──────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # ── Nodes ────────────────────────────────────────────────
    graph.add_node("intent_classifier", intent_classifier_agent)
    graph.add_node("orchestrator", orchestrator_agent)
    graph.add_node("article_agent", article_agent)
    graph.add_node("fundamental_analysis_agent", fundamental_analysis_agent)
    graph.add_node("technical_analysis_agent", technical_analysis_agent)
    graph.add_node("aggregator", aggregator_agent)

    # ── Entry point: mode routing ─────────────────────────────
    # mode = "api"     → thẳng orchestrator, bỏ qua intent_classifier
    # mode = "chatbot" → qua intent_classifier trước
    graph.add_conditional_edges(
        "__start__",
        route_entry,
        {
            "intent_classifier": "intent_classifier",
            "orchestrator": "orchestrator",
        },
    )

    # ── Intent classifier → routing ───────────────────────────
    graph.add_conditional_edges(
        "intent_classifier",
        route_after_intent,
        {
            "orchestrator": "orchestrator",
            "end": END,             # instant_reply trả thẳng, không cần pipeline
        },
    )

    # ── Orchestrator → sub-agents (song song) ─────────────────
    graph.add_conditional_edges(
        "orchestrator",
        route_to_agents,
        {
            "article_agent": "article_agent",
            "fundamental_analysis_agent": "fundamental_analysis_agent",
            "technical_analysis_agent": "technical_analysis_agent",
        },
    )

    # ── Sub-agents → aggregator ───────────────────────────────
    graph.add_edge("article_agent", "aggregator")
    graph.add_edge("fundamental_analysis_agent", "aggregator")
    graph.add_edge("technical_analysis_agent", "aggregator")

    # ── Kết thúc ─────────────────────────────────────────────
    graph.add_edge("aggregator", END)

    return graph.compile()