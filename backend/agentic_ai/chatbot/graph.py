"""
agentic_ai/chatbot/graph.py — LangGraph StateGraph cho chatbot.

Luồng đơn giản: __start__ → chat → END
Lịch sử hội thoại được lưu/đọc tự động qua SqliteSaver theo thread_id (session_id).
"""

import sqlite3
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from agentic_ai.chatbot.state import ChatbotState
from agentic_ai.chatbot.agents.chat import chat_agent


def build_chatbot_graph() -> StateGraph:
    graph = StateGraph(ChatbotState)

    graph.add_node("chat", chat_agent)
    
    graph.add_edge("__start__", "chat")
    graph.add_edge("chat", END)

    # Checkpointer giữ lịch sử hội thoại giữa các turn (theo thread_id)
    conn = sqlite3.connect("chat_memory.db", check_same_thread=False)
    return graph.compile(checkpointer=SqliteSaver(conn))
