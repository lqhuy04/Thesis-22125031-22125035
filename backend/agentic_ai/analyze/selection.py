"""
selection.py — Chuẩn hóa cấu hình "người dùng chọn dữ liệu nào để AI phân tích".

Cấu hình đến từ body của /api/agentic/analyze (trường `data_selection`) và được
lưu trong AgentState. Các agent đọc qua `get_selection(state)` để biết nguồn/chỉ số
nào được bật.

Mặc định: tất cả đều BẬT. Nhờ vậy các luồng không truyền `data_selection`
(ví dụ backtest pipeline) giữ nguyên hành vi cũ (đủ 5 chỉ số kỹ thuật → max_score = 5).
"""

# Các chỉ số kỹ thuật có thể bật/tắt
TECH_KEYS = ["ma", "boll", "rsi", "macd", "kdj"]

# Các nhóm chỉ số cơ bản có thể bật/tắt
FUND_KEYS = ["liquidity", "leverage", "efficiency", "profitability", "valuation"]


def get_selection(state: dict) -> dict:
    """
    Trả về cấu hình chuẩn hóa, mọi key đều có mặt với giá trị bool.

    {
        "news": bool,
        "technical":   {"ma","boll","rsi","macd","kdj"} -> bool,
        "fundamental": {"liquidity","leverage","efficiency",
                        "profitability","valuation"} -> bool,
    }

    Key thiếu → mặc định True (bật).
    """
    sel = state.get("data_selection") or {}
    tech = sel.get("technical") or {}
    fund = sel.get("fundamental") or {}

    return {
        "news": bool(sel.get("news", True)),
        "technical":   {k: bool(tech.get(k, True)) for k in TECH_KEYS},
        "fundamental": {k: bool(fund.get(k, True)) for k in FUND_KEYS},
    }
