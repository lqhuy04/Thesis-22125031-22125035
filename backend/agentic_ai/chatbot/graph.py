"""
agentic_ai/chatbot/graph.py — LangGraph StateGraph cho chatbot.

Luồng:
  __start__ → intent_classifier → (routing) → chat | qa | market | END
                                               chat   → END
                                               qa     → END
                                               market → END

intent_classifier phân loại và route:
  - OUT_OF_SCOPE  → END  (final_output đã được set sẵn trong classifier)
  - GREETING      → chat_agent
  - KNOWLEDGE_QA  → qa_agent
  - MARKET_QUERY  → market_agent (text-to-SQL trên Supabase Postgres)

Lịch sử được lưu bền vững vào Postgres (Supabase) qua PostgresSaver.
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver

from agentic_ai.chatbot.db import get_pool
from agentic_ai.chatbot.state import ChatbotState
from agentic_ai.chatbot.agents.chat import chat_agent
from agentic_ai.chatbot.agents.qa_agent import qa_agent
from agentic_ai.chatbot.agents.market_agent import market_agent
from agentic_ai.chatbot.agents.intent_classifier import intent_classifier_agent


def _route_by_intent(state: ChatbotState) -> str:
    intent = state.get("intent", "KNOWLEDGE_QA")
    print(f"[Graph Router] >>> Routing intent '{intent}' →", end=" ")

    if intent == "OUT_OF_SCOPE":
        print("END")
        return END
    elif intent == "GREETING":
        print("chat")
        return "chat"
    elif intent == "MARKET_QUERY":
        print("market")
        return "market"
    else:
        # KNOWLEDGE_QA → qa_agent
        print("qa")
        return "qa"


def build_chatbot_graph() -> StateGraph:
    graph = StateGraph(ChatbotState)

    graph.add_node("intent_classifier", intent_classifier_agent)
    graph.add_node("chat", chat_agent)
    graph.add_node("qa", qa_agent)
    graph.add_node("market", market_agent)

    graph.add_edge("__start__", "intent_classifier")
    graph.add_conditional_edges("intent_classifier", _route_by_intent)
    graph.add_edge("chat", END)
    graph.add_edge("qa", END)
    graph.add_edge("market", END)

    checkpointer = PostgresSaver(get_pool())
    checkpointer.setup()

    return graph.compile(checkpointer=checkpointer)
