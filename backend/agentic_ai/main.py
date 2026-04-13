"""
main.py — Entry point
"""

from graph import build_graph


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
        "user_input": (
            f"Tóm tắt tình hình và gợi ý thời điểm đầu tư của mã cổ phiếu {symbol} "
            f"dựa vào khẩu vị rủi ro của nhà đầu tư."
        ),
        "risk_appetite": user_risk_appetite,   # Truyền riêng để orchestrator dễ parse
        "symbol": symbol,                      # Truyền riêng để các agent dễ xử lý
        "plan": {},
        "agent_results": {},
        "final_output": "",
        "error": None,
    }
    # ─────────────────────────────────────────────────────────────────────────

    print("=== Multi-Agent System ===\n")
    result = graph.invoke(initial_state)

    print("\n=== Kết quả cuối ===")
    print(result.get("final_output", "(Không có kết quả)"))


if __name__ == "__main__":
    main()