from agentic_ai.analyze.state import AgentState
from agentic_ai.analyze.selection import get_selection
from app.services.fundamental_analysis_service import FundamentalAnalysisService
from app.services.company_service import CompanyService


def _is_financial_sector(icb_code) -> bool:
    """True nếu mã ngành ICB thuộc nhóm Tài chính (ICB Industry 8000: ngân hàng,
    bảo hiểm, dịch vụ tài chính, BĐS đầu tư...). Mọi phân ngành tài chính đều bắt
    đầu bằng chữ số '8'. Với nhóm này, P/E (và EV/EBITDA) không phản ánh đúng định
    giá → chỉ dùng P/B."""
    return str(icb_code or "").strip().startswith("8")


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


def _cagr(rows: list[dict], key: str) -> float | None:
    """Tốc độ tăng trưởng kép trung bình năm (CAGR) của 1 chỉ số qua các năm.

        CAGR = (giá_trị_cuối / giá_trị_đầu) ^ (1 / số_năm) − 1

    Lấy điểm đầu và điểm cuối theo năm (bỏ qua năm thiếu dữ liệu). Trả về None khi
    không đủ 2 điểm, khoảng cách năm ≤ 0, hoặc có giá trị ≤ 0 (CAGR không xác định
    khi đổi dấu / có số âm — tránh ra kết quả vô nghĩa cho biên lợi nhuận âm...).
    """
    pts: list[tuple[int, float]] = []
    for r in rows:
        year, value = r.get("year"), r.get(key)
        if year is None or value is None:
            continue
        try:
            pts.append((int(year), float(value)))
        except (TypeError, ValueError):
            continue
    if len(pts) < 2:
        return None
    pts.sort(key=lambda p: p[0])
    (y0, v0), (yn, vn) = pts[0], pts[-1]
    n = yn - y0
    if n <= 0 or v0 <= 0 or vn <= 0:
        return None
    return (vn / v0) ** (1.0 / n) - 1.0


def _line(label: str, rows: list[dict], key: str, spec: str,
          scale: float = 1.0, suffix: str = "", cagr: bool = False) -> str:
    """Dòng 1 chỉ số: chuỗi giá trị theo năm, kèm CAGR (tốc độ tăng trưởng TB) nếu cagr=True."""
    body = _series(rows, key, spec, scale=scale, suffix=suffix)
    if not cagr:
        return f"- {label}: {body}"
    c = _cagr(rows, key)
    cagr_txt = f"{c * 100:.2f}%/năm" if c is not None else "—"
    return f"- {label}: {body}  ·  Tốc độ tăng trưởng TB (CAGR): {cagr_txt}"


def _format_fundamental_output(summary, indicators, income_statements, cash_flows,
                               selection: dict, is_financial: bool = False) -> str:
    # Cả 5 nhóm chỉ số cơ bản đều lấy từ FA_Indicator, nên chỉ cần chuỗi năm của
    # indicators (income_statements / cash_flows chỉ dùng cho cờ "có dữ liệu" ở agent).
    inds = _last_n_years(indicators)

    latest_ind = inds[-1] if inds else {}

    # Khoảng năm hiển thị trên tiêu đề (ví dụ "2020–2024").
    years_all = [r["year"] for r in inds if r.get("year") is not None]
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

    # 4 nhóm dưới đây kèm CAGR (tốc độ tăng trưởng kép trung bình năm) bên cạnh
    # chuỗi giá trị theo năm; riêng nhóm định giá không tính CAGR (chỉ số định
    # giá dao động theo giá thị trường nên tăng trưởng kép không mang nhiều ý nghĩa).
    if selection.get("liquidity", True):
        parts += [
            "",
            "### Khả năng thanh toán (theo năm)",
            _line("Thanh toán hiện hành", inds, "current_ratio", ".2f", cagr=True),
            _line("Thanh toán nhanh", inds, "quick_ratio", ".2f", cagr=True),
            _line("Thanh toán tiền mặt", inds, "cash_ratio", ".2f", cagr=True),
        ]

    if selection.get("leverage", True):
        parts += [
            "",
            "### Đòn bẩy tài chính (theo năm)",
            _line("Nợ/Vốn chủ sở hữu", inds, "debt_to_equity", ".2f", cagr=True),
            _line("Đòn bẩy tài chính (Tổng TS/VCSH)", inds, "financial_leverage", ".2f", cagr=True),
            _line("Khả năng trả lãi", inds, "interest_coverage", ".2f", suffix="x", cagr=True),
        ]

    if selection.get("efficiency", True):
        parts += [
            "",
            "### Hiệu quả hoạt động (theo năm)",
            _line("Vòng quay tài sản", inds, "asset_turnover", ".2f", suffix="x", cagr=True),
            _line("Vòng quay tài sản cố định", inds, "fixed_asset_turnover", ".2f", suffix="x", cagr=True),
            _line("Số ngày tồn kho", inds, "days_inventory", ",.0f", suffix=" ngày", cagr=True),
            _line("Số ngày phải thu", inds, "days_receivable", ",.0f", suffix=" ngày", cagr=True),
        ]

    if selection.get("profitability", True):
        parts += [
            "",
            "### Khả năng sinh lời (theo năm)",
            _line("ROE", inds, "roe", ".2f", scale=100, suffix="%", cagr=True),
            _line("ROA", inds, "roa", ".2f", scale=100, suffix="%", cagr=True),
            _line("Biên lợi nhuận gộp", inds, "gross_margin", ".2f", scale=100, suffix="%", cagr=True),
            _line("Biên lợi nhuận ròng", inds, "net_margin", ".2f", scale=100, suffix="%", cagr=True),
        ]

    if selection.get("valuation", True):
        if is_financial:
            # Ngành tài chính (ICB 8xxx): P/E và EV/EBITDA dựa trên lợi nhuận không
            # phản ánh đúng định giá ngân hàng/bảo hiểm → chỉ dùng P/B.
            parts += [
                "",
                "### Nhóm định giá (theo năm)",
                "> ℹ️ Ngành tài chính (ICB 8xxx): định giá bằng P/B; KHÔNG dùng P/E / EV/EBITDA.",
                _line("P/B", inds, "pb_ratio", ".2f"),
                _line("EPS (đồng)", inds, "eps", ",.0f"),
            ]
        else:
            parts += [
                "",
                "### Nhóm định giá (theo năm)",
                _line("P/E", inds, "pe_ratio", ".2f"),
                _line("P/B", inds, "pb_ratio", ".2f"),
                _line("EV/EBITDA", inds, "ev_ebitda", ".2f"),
                _line("EPS (đồng)", inds, "eps", ",.0f"),
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

        # Nhận diện ngành tài chính (ICB 8xxx) để bỏ P/E khỏi định giá. Lỗi/thiếu
        # profile KHÔNG được chặn phân tích cơ bản → mặc định coi như không phải tài chính.
        try:
            profile = CompanyService.get_profile(symbol)
            is_financial = _is_financial_sector((profile or {}).get("icb_code"))
        except Exception as e:
            print(f"[Fundamental Analysis Agent] Không lấy được mã ngành ICB cho {symbol}: {e}")
            is_financial = False

        if not indicators and not income_statements and not cash_flows and not summary:
            output = "Không có dữ liệu phân tích cơ bản."
        else:
            output = _format_fundamental_output(
                summary, indicators, income_statements, cash_flows, selection, is_financial
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