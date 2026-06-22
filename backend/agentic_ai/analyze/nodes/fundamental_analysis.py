from agentic_ai.analyze.state import AgentState
from agentic_ai.analyze.selection import get_selection
from app.services.fundamental_analysis_service import FundamentalAnalysisService


def _fmt(value, spec: str) -> str:
    if value is None:
        return ""
    try:
        return format(float(value), spec)
    except (TypeError, ValueError):
        return ""


def _format_fundamental_output(summary, indicators, income_statements, cash_flows, selection: dict) -> str:
    latest_ind = next((i for i in indicators if i["year"] == max(i["year"] for i in indicators)), {})
    latest_inc = next((i for i in income_statements if i["year"] == max(i["year"] for i in income_statements)), {})
    latest_cf  = next((i for i in cash_flows if i["year"] == max(i["year"] for i in cash_flows)), {})

    year = latest_ind.get("year", "N/A")

    # Thêm vào đây
    if not latest_ind.get("gross_margin"):
        sector_note = "\n> ⚠️ Một số chỉ số không áp dụng cho ngành ngân hàng (gross margin, current ratio, D/E)."
    else:
        sector_note = ""

    parts = [f"## Phân tích cơ bản ({year}){sector_note}", ""]
    parts.append("### Tóm tắt tổng quan")
    parts.append((summary or {}).get("summary", "Không có dữ liệu"))

    if selection.get("valuation", True):
        parts += [
            "",
            "### Chỉ số định giá",
            f'- P/E: {_fmt(latest_ind.get("pe_ratio"), ".2f")}',
            f'- P/B: {_fmt(latest_ind.get("pb_ratio"), ".2f")}',
            f'- EV/EBITDA: {_fmt(latest_ind.get("ev_ebitda"), ".2f")}',
            f'- EPS: {_fmt(latest_ind.get("eps"), ",.0f")} đồng',
        ]

    if selection.get("profitability", True):
        parts += [
            "",
            "### Khả năng sinh lời",
            f'- ROE: {_fmt(latest_ind.get("roe", 0) and latest_ind.get("roe") * 100, ".2f")}%',
            f'- ROA: {_fmt(latest_ind.get("roa", 0) and latest_ind.get("roa") * 100, ".2f")}%',
            f'- Biên lợi nhuận gộp: {_fmt(latest_ind.get("gross_margin", 0) and latest_ind.get("gross_margin") * 100, ".2f")}%',
            f'- Biên lợi nhuận ròng: {_fmt(latest_ind.get("net_margin", 0) and latest_ind.get("net_margin") * 100, ".2f")}%',
        ]

    if selection.get("growth", True):
        parts += [
            "",
            "### Tăng trưởng",
            f'- Tăng trưởng doanh thu YoY: {_fmt(latest_ind.get("revenue_yoy", 0) and latest_ind.get("revenue_yoy") * 100, ".2f")}%',
            f'- Tăng trưởng lợi nhuận YoY: {_fmt(latest_ind.get("profit_yoy", 0) and latest_ind.get("profit_yoy") * 100, ".2f")}%',
            f'- Doanh thu thuần: {_fmt(latest_inc.get("net_revenue", 0) and latest_inc.get("net_revenue") / 1e9, ",.1f")} tỷ đồng',
            f'- Lợi nhuận ròng: {_fmt(latest_inc.get("net_profit_after_tax", 0) and latest_inc.get("net_profit_after_tax") / 1e9, ",.1f")} tỷ đồng',
        ]

    if selection.get("financial_health", True):
        parts += [
            "",
            "### Sức khỏe tài chính",
            f'- Tỷ lệ thanh khoản hiện tại: {_fmt(latest_ind.get("current_ratio"), ".2f")}',
            f'- Nợ/Vốn chủ sở hữu: {_fmt(latest_ind.get("debt_to_equity"), ".2f")}',
            f'- Khả năng trả lãi: {_fmt(latest_ind.get("interest_coverage"), ".2f")}x',
        ]

    if selection.get("cash_flow", True):
        parts += [
            "",
            "### Dòng tiền",
            f'- CFO: {_fmt(latest_cf.get("cfo", 0) and latest_cf.get("cfo") / 1e9, ",.1f")} tỷ đồng',
            f'- CAPEX: {_fmt(latest_cf.get("capex", 0) and latest_cf.get("capex") / 1e9, ",.1f")} tỷ đồng',
            f'- Cổ tức đã trả: {_fmt(latest_cf.get("dividends_paid", 0) and latest_cf.get("dividends_paid") / 1e9, ",.1f")} tỷ đồng',
        ]

    return "\n".join(parts).strip()


def fundamental_analysis_agent(state: AgentState) -> AgentState:
    symbol = state.get("symbol", "")
    selection = get_selection(state)["fundamental"]

    # Người dùng tắt toàn bộ nhóm chỉ số cơ bản → bỏ qua
    if not any(selection.values()):
        return {
            "agent_results": {
                "fundamental_analysis_agent": "Người dùng đã tắt phân tích cơ bản.",
            },
        }

    # Dữ liệu cơ bản có thể thiếu (mã mới niêm yết, chưa có báo cáo...). Một lỗi
    # tầng dữ liệu của 1 mã KHÔNG được làm hỏng cả pipeline (đặc biệt khi chạy rổ
    # VN30/VN100). Thiếu/lỗi dữ liệu → coi như không có dữ liệu cơ bản; aggregator
    # nhận diện qua marker "Không có dữ liệu" và loại nguồn này khỏi confidence.
    try:
        income_statements = FundamentalAnalysisService.get_income_statements(symbol)
        cash_flows = FundamentalAnalysisService.get_cash_flows(symbol)
        indicators = FundamentalAnalysisService.get_indicators(symbol)
        summary = FundamentalAnalysisService.get_summary(symbol)

        if not indicators and not income_statements and not cash_flows and not summary:
            output = "Không có dữ liệu phân tích cơ bản."
        else:
            output = _format_fundamental_output(
                summary, indicators, income_statements, cash_flows, selection
            )
    except Exception as e:
        print(f"[Fundamental Analysis Agent] Lỗi lấy dữ liệu cơ bản cho {symbol}: {e}")
        output = "Không có dữ liệu phân tích cơ bản."

    print("[Fundamental Analysis Agent] Output:", output)

    return {
        "agent_results": {
            "fundamental_analysis_agent": output,
        },
    }