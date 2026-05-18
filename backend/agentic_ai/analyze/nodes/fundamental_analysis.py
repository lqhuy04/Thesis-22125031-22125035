from agentic_ai.analyze.state import AgentState
from app.services.fundamental_analysis_service import FundamentalAnalysisService


def _fmt(value, spec: str) -> str:
    if value is None:
        return ""
    try:
        return format(float(value), spec)
    except (TypeError, ValueError):
        return ""


def _format_fundamental_output(summary, indicators, income_statements, cash_flows) -> str:
    latest_ind = next((i for i in indicators if i["year"] == max(i["year"] for i in indicators)), {})
    latest_inc = next((i for i in income_statements if i["year"] == max(i["year"] for i in income_statements)), {})
    latest_cf  = next((i for i in cash_flows if i["year"] == max(i["year"] for i in cash_flows)), {})

    year = latest_ind.get("year", "N/A")

    # Thêm vào đây
    if not latest_ind.get("gross_margin"):
        sector_note = "\n> ⚠️ Một số chỉ số không áp dụng cho ngành ngân hàng (gross margin, current ratio, D/E)."
    else:
        sector_note = ""

    return f"""
## Phân tích cơ bản ({year}){sector_note}

### Tóm tắt tổng quan
{summary.get("summary", "Không có dữ liệu")}

### Chỉ số định giá
- P/E: {_fmt(latest_ind.get("pe_ratio"), ".2f")}
- P/B: {_fmt(latest_ind.get("pb_ratio"), ".2f")}
- EV/EBITDA: {_fmt(latest_ind.get("ev_ebitda"), ".2f")}
- EPS: {_fmt(latest_ind.get("eps"), ",.0f")} đồng

### Khả năng sinh lời
- ROE: {_fmt(latest_ind.get("roe", 0) and latest_ind.get("roe") * 100, ".2f")}%
- ROA: {_fmt(latest_ind.get("roa", 0) and latest_ind.get("roa") * 100, ".2f")}%
- Biên lợi nhuận gộp: {_fmt(latest_ind.get("gross_margin", 0) and latest_ind.get("gross_margin") * 100, ".2f")}%
- Biên lợi nhuận ròng: {_fmt(latest_ind.get("net_margin", 0) and latest_ind.get("net_margin") * 100, ".2f")}%

### Tăng trưởng
- Tăng trưởng doanh thu YoY: {_fmt(latest_ind.get("revenue_yoy", 0) and latest_ind.get("revenue_yoy") * 100, ".2f")}%
- Tăng trưởng lợi nhuận YoY: {_fmt(latest_ind.get("profit_yoy", 0) and latest_ind.get("profit_yoy") * 100, ".2f")}%
- Doanh thu thuần: {_fmt(latest_inc.get("net_revenue", 0) and latest_inc.get("net_revenue") / 1e9, ",.1f")} tỷ đồng
- Lợi nhuận ròng: {_fmt(latest_inc.get("net_profit_after_tax", 0) and latest_inc.get("net_profit_after_tax") / 1e9, ",.1f")} tỷ đồng

### Sức khỏe tài chính
- Tỷ lệ thanh khoản hiện tại: {_fmt(latest_ind.get("current_ratio"), ".2f")}
- Nợ/Vốn chủ sở hữu: {_fmt(latest_ind.get("debt_to_equity"), ".2f")}
- Khả năng trả lãi: {_fmt(latest_ind.get("interest_coverage"), ".2f")}x

### Dòng tiền
- CFO: {_fmt(latest_cf.get("cfo", 0) and latest_cf.get("cfo") / 1e9, ",.1f")} tỷ đồng
- CAPEX: {_fmt(latest_cf.get("capex", 0) and latest_cf.get("capex") / 1e9, ",.1f")} tỷ đồng
- Cổ tức đã trả: {_fmt(latest_cf.get("dividends_paid", 0) and latest_cf.get("dividends_paid") / 1e9, ",.1f")} tỷ đồng
""".strip()


def fundamental_analysis_agent(state: AgentState) -> AgentState:
    symbol = state.get("symbol", "")

    balance_sheets = FundamentalAnalysisService.get_balance_sheets(symbol)
    income_statements = FundamentalAnalysisService.get_income_statements(symbol)
    cash_flows = FundamentalAnalysisService.get_cash_flows(symbol)
    indicators = FundamentalAnalysisService.get_indicators(symbol)
    summary = FundamentalAnalysisService.get_summary(symbol)

    output = _format_fundamental_output(summary, indicators, income_statements, cash_flows)

    print("[Fundamental Analysis Agent] Output:", output)

    return {
        "agent_results": {
            "fundamental_analysis_agent": output,
        },
    }