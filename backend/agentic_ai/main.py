"""
Multi-Agent System - Entry Point
Chạy: python main.py
"""

from graph import build_graph


def main():
    graph = build_graph()

    print("=== Multi-Agent System ===")

    initial_state = {
        "user_input": "hihihihihihihihihihihi",  # Input gốc từ người dùng
        "plan": [],
        "agent_results": {},
        "final_output": "",
        "error": None,
    }

    print(graph.get_graph().draw_ascii())
    
    print("\n[System] Đang xử lý...\n")
    result = graph.invoke(initial_state)
    

    print("=== Kết quả ===")
    # print(result.get("final_output", "(Không có kết quả)"))


if __name__ == "__main__":
    main()