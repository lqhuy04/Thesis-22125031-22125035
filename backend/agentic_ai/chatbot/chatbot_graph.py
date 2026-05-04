"""
graph.py — LangGraph StateGraph

API mode:     __start__ → orchestrator → agents → aggregator → END
Chatbot mode: __start__ → intent_classifier → dispatch song song
                          → [run_pipeline | run_qa] → reply_merger → END
"""

import sqlite3
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Send

from agentic_ai.state import AgentState, ChatbotSystemState
from agentic_ai.agents.intent_classifier import intent_classifier_agent
from agentic_ai.agents.qa_agent import qa_agent
from agentic_ai.agents.orchestrator import orchestrator_agent
from agentic_ai.agents.aggregator import aggregator_agent
from agentic_ai.agents.article import article_agent
from agentic_ai.agents.fundamental_analysis import fundamental_analysis_agent
from agentic_ai.agents.technical_analysis import technical_analysis_agent
from agentic_ai.agents.reply_merger import reply_merger_agent


# ─── Routing: Chatbot mode — dispatch intent jobs song song ───────────────────

def dispatch_intents(state: ChatbotSystemState) -> list[Send]:
    intents = state.get("intents", [])
    sends = []

    for intent in intents:
        job: AgentState = {
            "mode": "chat",
            
            "intent": intent["intent"],
            "order": intent["order"],
            
            "user_input": intent["user_input"],
            "risk_appetite": state.get("risk_appetite", {}),
            
            "symbol": intent.get("symbol") or state.get("symbol", ""),
            "market_index": intent.get("market_index"),
            "category": intent.get("category"),
            
            "plan": {},
            "agent_results": {},
            
            "final_output": "",
            "error": None,
        }

        if intent["intent"] == "analysis":
            sends.append(Send("run_pipeline", job))
        else:
            sends.append(Send("run_qa", job))

    print(f"[Router/Dispatch] Dispatch {len(sends)} job(s) song song")
    return sends


# ─── Job nodes (chatbot only) ─────────────────────────────────────────────────

def run_pipeline(job: AgentState) -> dict:
    """Full pipeline cho một pipeline intent."""
    # Orchestrator
    plan_result = orchestrator_agent(job)
    job = {**job, **plan_result}

    # Sub-agents
    agent_results = {}
    plan = job.get("plan", {})

    if "article_agent" in plan:
        agent_results.update(article_agent(job).get("agent_results", {}))
    if "fundamental_analysis_agent" in plan:
        agent_results.update(fundamental_analysis_agent(job).get("agent_results", {}))
    if "technical_analysis_agent" in plan:
        agent_results.update(technical_analysis_agent(job).get("agent_results", {}))

    job = {**job, "agent_results": agent_results}

    # Aggregator
    agg_result = aggregator_agent(job)
    final_output = agg_result.get("final_output", "")
    reply = final_output if isinstance(final_output, str) else str(final_output)

    return {
        "sub_results": [{
            "order": job["order"],
            "intent": job["intent"],
            "user_input": job["user_input"],
            "reply": reply,
        }]
    }


def run_qa(job: AgentState) -> dict:
    """QA agent cho general_question / clarification / out_of_scope."""
    return qa_agent(job)


# ─── Build graph ──────────────────────────────────────────────────────────────

def build_chatbot_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # ── Chatbot mode nodes ─────────────────────────────────────
    graph.add_node("intent_classifier", intent_classifier_agent)
    graph.add_node("run_pipeline", run_pipeline)
    graph.add_node("run_qa", run_qa)
    graph.add_node("reply_merger", reply_merger_agent)

    # ── Entry: phân nhánh theo mode ───────────────────────────
    graph.add_edge(
        "__start__",
        "intent_classifier"
    )

    # ── Chatbot mode pipeline ──────────────────────────────────
    graph.add_conditional_edges(
        "intent_classifier",
        dispatch_intents,
        ["run_pipeline", "run_qa"],
    )
    graph.add_edge("run_pipeline", "reply_merger")
    graph.add_edge("run_qa", "reply_merger")
    graph.add_edge("reply_merger", END)

    # graph.add_edge("intent_classifier", END)

    # ── Checkpointer ──────────────────────────────────────────
    conn = sqlite3.connect("chat_memory.db", check_same_thread=False)
    return graph.compile(checkpointer=SqliteSaver(conn))