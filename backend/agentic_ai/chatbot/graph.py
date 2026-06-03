"""
agentic_ai/chatbot/graph.py — LangGraph StateGraph cho chatbot.

Luồng đơn giản: __start__ → chat → END
Lịch sử hội thoại được lưu BỀN VỮNG vào Postgres (Supabase) qua PostgresSaver,
khóa theo thread_id (= session_id). Restart server vẫn còn lịch sử.
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver

from agentic_ai.chatbot.db import get_pool
from agentic_ai.chatbot.state import ChatbotState
from agentic_ai.chatbot.agents.chat import chat_agent


def build_chatbot_graph() -> StateGraph:
    graph = StateGraph(ChatbotState)

    graph.add_node("chat", chat_agent)
    graph.add_edge("__start__", "chat")
    graph.add_edge("chat", END)

    checkpointer = PostgresSaver(get_pool())
    # Tạo các bảng checkpoint nếu chưa có (chạy 1 lần, idempotent).
    checkpointer.setup()

    return graph.compile(checkpointer=checkpointer)
