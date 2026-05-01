"""
main.py — Entry point
"""

from agentic_ai.graph import build_graph


def main():
    graph = build_graph()

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
        "user_input": f"Tóm tắt tình hình và gợi ý thời điểm đầu tư của mã cổ phiếu {symbol} dựa vào khẩu vị rủi ro của nhà đầu tư.",
        "risk_appetite": user_risk_appetite,
        "mode": "chatbot",
        "symbol": symbol,
        "intent": {},
        "plan": {},
        "agent_results": {},
        "final_output": "",
        "error": None,
    }
    # ─────────────────────────────────────────────────────────────────────────

    print("=== Multi-Agent System ===\n")
    result = graph.invoke(initial_state)

    print("\n=== Kết quả cuối ===")

    intent = result.get("intent", {})
    intent_type = intent.get("intent_type")

    # Nếu pipeline dừng sớm (general_question / clarification / out_of_scope)
    # → trả instant_reply thẳng cho user
    if intent_type != "stock_analysis":
        print(intent.get("instant_reply", "(Không có phản hồi)"))
    else:
        print(result.get("final_output", "(Không có kết quả)"))


if __name__ == "__main__":
    main()