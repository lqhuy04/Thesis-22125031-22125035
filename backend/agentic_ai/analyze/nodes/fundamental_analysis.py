from agentic_ai.analyze.state import AgentState
from agentic_ai.analyze.selection import get_selection
from app.services.fundamental_analysis_service import FundamentalAnalysisService


# Luôn phân tích 5 năm gần nhất, KHÔNG phụ thuộc kỳ hạn đầu tư (ngắn/trung/dài
# hạn). Nhờ đó tóm tắt cơ bản thể hiện được cả xu hướng dài hạn, không chỉ ảnh
# chụp 1 năm gần nhất (ngắn hạn).
FUND_YEARS = 5


def _last_n_years(rows: list[dict], n: int = FUND_YEARS) -> list[dict]:
    """Lấy tối đa n năm gần nhất, sắp xếp cũ → mới để đọc theo dòng thời gian."""
    valid = [r for r in (rows or []) if r.get("year") is not None]
    valid.sort(key=lambda r: r["year"], reverse=True)
    return list(reversed(valid[:n]))


def _series(rows: list[dict], key: str, spec: str, scale: float = 1.0, suffix: str = "") -> str:
    """Chuỗi giá trị 1 chỉ số qua các năm: '2020: 12.30 | 2021: 15.00 | ...'.

    Giá trị thiếu (None/không parse được) → '—' để không gãy dòng thời gian.
    """
    cells = []
    for r in rows:
        year = r.get("year", "?")
        value = r.get(key)
        if value is None:
            cells.append(f"{year}: —")
            continue
        try:
            cells.append(f"{year}: {format(float(value) * scale, spec)}{suffix}")
        except (TypeError, ValueError):
            cells.append(f"{year}: —")
    return " | ".join(cells) if cells else "Không có dữ liệu"


def _format_fundamental_output(summary, indicators, income_statements, cash_flows, selection: dict) -> str:
    inds = _last_n_years(indicators)
    incs = _last_n_years(income_statements)
    cfs  = _last_n_years(cash_flows)

    latest_ind = inds[-1] if inds else {}

    # Khoảng năm hiển thị trên tiêu đề (ví dụ "2020–2024").
    years_all = [r["year"] for r in (inds + incs + cfs) if r.get("year") is not None]
    if years_all:
        y_min, y_max = min(years_all), max(years_all)
        year_label = f"{y_min}–{y_max}" if y_min != y_max else f"{y_max}"
    else:
        year_label = "N/A"

    if not latest_ind.get("gross_margin"):
        sector_note = "\n> ⚠️ Một số chỉ số không áp dụng cho ngành ngân hàng (gross margin, current ratio, D/E)."
    else:
        sector_note = ""

    parts = [f"## Phân tích cơ bản ({year_label}){sector_note}", ""]
    parts.append("### Tóm tắt tổng quan")
    parts.append((summary or {}).get("summary", "Không có dữ liệu"))

    if selection.get("valuation", True):
        parts += [
            "",
            "### Chỉ số định giá (theo năm)",
            f"- P/E: {_series(inds, 'pe_ratio', '.2f')}",
            f"- P/B: {_series(inds, 'pb_ratio', '.2f')}",
            f"- EV/EBITDA: {_series(inds, 'ev_ebitda', '.2f')}",
            f"- EPS (đồng): {_series(inds, 'eps', ',.0f')}",
        ]

    if selection.get("profitability", True):
        parts += [
            "",
            "### Khả năng sinh lời (theo năm)",
            f"- ROE: {_series(inds, 'roe', '.2f', scale=100, suffix='%')}",
            f"- ROA: {_series(inds, 'roa', '.2f', scale=100, suffix='%')}",
            f"- Biên lợi nhuận gộp: {_series(inds, 'gross_margin', '.2f', scale=100, suffix='%')}",
            f"- Biên lợi nhuận ròng: {_series(inds, 'net_margin', '.2f', scale=100, suffix='%')}",
        ]

    if selection.get("growth", True):
        parts += [
            "",
            "### Tăng trưởng (theo năm)",
            f"- Tăng trưởng doanh thu YoY: {_series(inds, 'revenue_yoy', '.2f', scale=100, suffix='%')}",
            f"- Tăng trưởng lợi nhuận YoY: {_series(inds, 'profit_yoy', '.2f', scale=100, suffix='%')}",
            f"- Doanh thu thuần (tỷ đồng): {_series(incs, 'net_revenue', ',.1f', scale=1 / 1e9)}",
            f"- Lợi nhuận ròng (tỷ đồng): {_series(incs, 'net_profit_after_tax', ',.1f', scale=1 / 1e9)}",
        ]

    if selection.get("financial_health", True):
        parts += [
            "",
            "### Sức khỏe tài chính (theo năm)",
            f"- Tỷ lệ thanh khoản hiện tại: {_series(inds, 'current_ratio', '.2f')}",
            f"- Nợ/Vốn chủ sở hữu: {_series(inds, 'debt_to_equity', '.2f')}",
            f"- Khả năng trả lãi: {_series(inds, 'interest_coverage', '.2f', suffix='x')}",
        ]

    if selection.get("cash_flow", True):
        parts += [
            "",
            "### Dòng tiền (theo năm)",
            f"- CFO (tỷ đồng): {_series(cfs, 'cfo', ',.1f', scale=1 / 1e9)}",
            f"- CAPEX (tỷ đồng): {_series(cfs, 'capex', ',.1f', scale=1 / 1e9)}",
            f"- Cổ tức đã trả (tỷ đồng): {_series(cfs, 'dividends_paid', ',.1f', scale=1 / 1e9)}",
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