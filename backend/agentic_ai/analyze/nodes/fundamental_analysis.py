from agentic_ai.analyze.state import AgentState
from app.services.fundamental_analysis_service import FundamentalAnalysisService


def _format_fundamental_output(
    summary: dict,
    indicators: list,
    income_statements: list,
    cash_flows: list,
) -> str:
    latest_ind = next((i for i in indicators if i["year"] == max(i["year"] for i in indicators)), {})
    latest_inc = next((i for i in income_statements if i["year"] == max(i["year"] for i in income_statements)), {})
    latest_cf = next((i for i in cash_flows if i["year"] == max(i["year"] for i in cash_flows)), {})

    year = latest_ind.get("year", "N/A")

    return f"""
## Phân tích cơ bản ({year})

### Tóm tắt tổng quan
{summary.get("summary", "Không có dữ liệu")}

### Chỉ số định giá
- P/E: {latest_ind.get("pe_ratio", "N/A"):.2f}
- P/B: {latest_ind.get("pb_ratio", "N/A"):.2f}
- EV/EBITDA: {latest_ind.get("ev_ebitda", "N/A"):.2f}
- EPS: {latest_ind.get("eps", "N/A"):,.0f} đồng

### Khả năng sinh lời
- ROE: {latest_ind.get("roe", 0) * 100:.2f}%
- ROA: {latest_ind.get("roa", 0) * 100:.2f}%
- Biên lợi nhuận gộp: {latest_ind.get("gross_margin", 0) * 100:.2f}%
- Biên lợi nhuận ròng: {latest_ind.get("net_margin", 0) * 100:.2f}%

### Tăng trưởng
- Tăng trưởng doanh thu YoY: {latest_ind.get("revenue_yoy", 0) * 100:.2f}%
- Tăng trưởng lợi nhuận YoY: {latest_ind.get("profit_yoy", 0) * 100:.2f}%
- Doanh thu thuần: {latest_inc.get("net_revenue", 0) / 1e9:,.1f} tỷ đồng
- Lợi nhuận ròng: {latest_inc.get("net_profit_after_tax", 0) / 1e9:,.1f} tỷ đồng

### Sức khỏe tài chính
- Tỷ lệ thanh khoản hiện tại: {latest_ind.get("current_ratio", "N/A"):.2f}
- Nợ/Vốn chủ sở hữu: {latest_ind.get("debt_to_equity", "N/A"):.2f}
- Khả năng trả lãi: {latest_ind.get("interest_coverage", "N/A"):.2f}x

### Dòng tiền
- CFO: {latest_cf.get("cfo", 0) / 1e9:,.1f} tỷ đồng
- CAPEX: {latest_cf.get("capex", 0) / 1e9:,.1f} tỷ đồng
- Cổ tức đã trả: {latest_cf.get("dividends_paid", 0) / 1e9:,.1f} tỷ đồng
""".strip()


def fundamental_analysis_agent(state: AgentState) -> AgentState:
    symbol = state.get("symbol", "")

    balance_sheets = FundamentalAnalysisService.get_balance_sheets(symbol)
    income_statements = FundamentalAnalysisService.get_income_statements(symbol)
    cash_flows = FundamentalAnalysisService.get_cash_flows(symbol)
    indicators = FundamentalAnalysisService.get_indicators(symbol)
    summary = FundamentalAnalysisService.get_summary(symbol)

    output = _format_fundamental_output(summary, indicators, income_statements, cash_flows)

    return {
        "agent_results": {
            "fundamental_analysis_agent": output,
        },
    }