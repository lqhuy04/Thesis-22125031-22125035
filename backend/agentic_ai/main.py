"""
main.py — Entry point
"""

import uuid
from agentic_ai.graph import build_graph


def main():
    graph = build_graph()

    # ── Session ──────────────────────────────────────────────────────────────
    # Production: lấy session_id từ user auth / cookie / request context
    # Demo: tạo mới mỗi lần chạy (mỗi lần = một cuộc trò chuyện mới)
    # Giữ nguyên session_id giữa các lần invoke để LangGraph load lại history
    session_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}

    # ── Input ────────────────────────────────────────────────────────────────
    symbol = "VNM"

    user_risk_appetite = {
        "capital_ratio": "Dưới 10%",
        "comfort_zone": "Lợi nhuận +15% | Rủi ro lỗ tối đa -10%",
        "expectation": "Kiếm thêm thu nhập thụ động",
        "experience": "Đã có kinh nghiệm",
        "period": "Ngắn hạn (Dưới 1 năm)",
    }

    initial_state = {
        "user_input": "Xin chào",
        "risk_appetite": user_risk_appetite,
        "symbol": symbol,
        "mode": "chatbot",   # ← đổi thành "api" nếu muốn structured output
        "session_id": session_id,
        "intent": {},
        "plan": {},
        "agent_results": {},
        "messages": [],
        "final_output": "",
        "error": None,
    }
    # ─────────────────────────────────────────────────────────────────────────

    print("=== Multi-Agent System ===\n")

    # Truyền config để LangGraph biết thread_id → tự load/save checkpoint
    result = graph.invoke(initial_state, config=config)

    print("\n=== Kết quả cuối ===")

    intent = result.get("intent", {})
    intent_type = intent.get("intent_type")

    if intent_type != "stock_analysis":
        print(intent.get("instant_reply", "(Không có phản hồi)"))
    else:
        print(result.get("final_output", "(Không có kết quả)"))


if __name__ == "__main__":
    main()