import math

from agentic_ai.analyze.state import AgentState
from agentic_ai.analyze.selection import get_selection
from app.services.fundamental_analysis_service import FundamentalAnalysisService
from app.services.company_service import CompanyService


def _is_missing(value) -> bool:
    """None hoặc NaN (giá trị thiếu sau khi qua DataFrame — cột thưa dữ liệu như
    các chỉ số ngân hàng chỉ có ở vài năm sẽ bị pandas đổi None thành NaN)."""
    if value is None:
        return True
    try:
        return math.isnan(value)
    except TypeError:
        return False

# Tên ngành theo chữ số đầu mã ICB (cấp Industry). Dùng để gắn nhãn bảng so sánh ngành.
_ICB_INDUSTRY_NAMES = {
    "0": "Dầu khí",
    "1": "Vật liệu cơ bản",
    "2": "Công nghiệp",
    "3": "Hàng tiêu dùng",
    "4": "Y tế",
    "5": "Dịch vụ tiêu dùng",
    "6": "Viễn thông",
    "7": "Tiện ích",
    "8": "Tài chính",
    "9": "Công nghệ",
}

# Chỉ tiêu đưa vào bảng so sánh với ngành (chọn lọc theo góc nhìn chuyên viên tài
# chính — không dùng hết bộ chỉ số). Mỗi mục: (nhãn, key, format, scale, hậu tố).
_COMPARE_METRICS_FINANCIAL = [
    ("ROE", "roe", ".2f", 100, "%"),
    ("ROA", "roa", ".2f", 100, "%"),
    ("Biên LN ròng", "net_margin", ".2f", 100, "%"),
    ("Đòn bẩy TC (TS/VCSH)", "financial_leverage", ".2f", 1, ""),
    ("Dư nợ/VCSH", "loans_to_equity", ".2f", 1, ""),
    ("Thanh toán tiền mặt", "cash_ratio", ".2f", 1, ""),
    ("P/B", "pb_ratio", ".2f", 1, ""),
    ("CAR", "car", ".2f", 100, "%"),
    ("NIM", "nim", ".2f", 100, "%"),
    ("LDR", "ldr", ".2f", 100, "%"),
    ("Tỷ lệ nợ xấu (NPL)", "npl_ratio", ".2f", 100, "%"),
]
_COMPARE_METRICS_NONFINANCIAL = [
    ("ROE", "roe", ".2f", 100, "%"),
    ("ROA", "roa", ".2f", 100, "%"),
    ("Biên LN gộp", "gross_margin", ".2f", 100, "%"),
    ("Biên LN ròng", "net_margin", ".2f", 100, "%"),
    ("Vòng quay tài sản", "asset_turnover", ".2f", 1, "x"),
    ("Nợ/VCSH", "debt_to_equity", ".2f", 1, ""),
    ("P/E", "pe_ratio", ".2f", 1, ""),
    ("P/B", "pb_ratio", ".2f", 1, ""),
]


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
        if _is_missing(value):
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
        if year is None or _is_missing(value):
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


def _fmt_val(value, spec: str, scale: float = 1.0, suffix: str = "") -> str:
    """Định dạng 1 giá trị đơn (dùng cho ô bảng); None/không parse được → '—'."""
    if value is None:
        return "—"
    try:
        return f"{format(float(value) * scale, spec)}{suffix}"
    except (TypeError, ValueError):
        return "—"


def _dupont_analysis(rows: list[dict]) -> str:
    """Phân tích DuPont: ROE = Biên LN ròng × Vòng quay TS × Đòn bẩy TC

    Công thức: ROE = (Net Income / Revenue) × (Revenue / Total Assets) × (Total Assets / Equity)
                   = Net Margin × Asset Turnover × Financial Leverage

    Trả về markdown text với phân tích từng thành phần, chiến lược tài chính, và xu hướng.
    """
    if not rows:
        return ""

    inds = _last_n_years(rows, FUND_YEARS)
    if not inds:
        return ""

    latest = inds[-1] if inds else {}

    lines = ["", "### Phân tích DuPont (Tác động từng thành phần lên ROE)"]
    lines.append(
        "> ROE = Biên LN ròng (%) × Vòng quay TS (lần) × Đòn bẩy TC (lần)\n"
        "> Công thức này giúp hiểu doanh nghiệp tạo lợi nhuận từ: (1) khả năng tính lãi trên doanh thu; "
        "(2) hiệu quả khai thác tài sản; (3) mức sử dụng nợ."
    )

    # Thành phần 1: Biên lợi nhuận ròng (Net Margin)
    net_margin = _latest(inds, "net_margin")
    if net_margin is not None:
        net_margin_pct = net_margin * 100
        lines.append("")
        lines.append(f"**1. Biên lợi nhuận ròng**: {net_margin_pct:.2f}%")
        lines.append(
            f"   Năm gần nhất: {_series(inds, 'net_margin', '.2f', scale=100, suffix='%')}"
        )
        cagr_nm = _cagr(inds, "net_margin")
        cagr_nm_txt = f"{cagr_nm * 100:.2f}%/năm" if cagr_nm is not None else "—"
        lines.append(
            f"   • CAGR: {cagr_nm_txt}  →  Lợi nhuận ròng trên doanh thu đang "
            f"{'cải thiện' if cagr_nm and cagr_nm > 0 else 'suy giảm' if cagr_nm else 'không tính được'}."
        )

    # Thành phần 2: Vòng quay tài sản (Asset Turnover)
    asset_turnover = _latest(inds, "asset_turnover")
    if asset_turnover is not None:
        lines.append("")
        lines.append(f"**2. Vòng quay tài sản (lần)**: {asset_turnover:.2f}x")
        lines.append(
            f"   Năm gần nhất: {_series(inds, 'asset_turnover', '.2f', suffix='x')}"
        )
        cagr_at = _cagr(inds, "asset_turnover")
        cagr_at_txt = f"{cagr_at * 100:.2f}%/năm" if cagr_at is not None else "—"
        lines.append(
            f"   • CAGR: {cagr_at_txt}  →  Khả năng khai thác tài sản đang "
            f"{'tốt lên' if cagr_at and cagr_at > 0 else 'yếu đi' if cagr_at else 'không tính được'}."
        )

    # Thành phần 3: Đòn bẩy tài chính (Financial Leverage)
    fin_leverage = _latest(inds, "financial_leverage")
    debt_to_equity = _latest(inds, "debt_to_equity")
    if fin_leverage is not None:
        lines.append("")
        lines.append(f"**3. Đòn bẩy tài chính (TS/VCSH)**: {fin_leverage:.2f}x")
        lines.append(
            f"   Năm gần nhất: {_series(inds, 'financial_leverage', '.2f', suffix='x')}"
        )
        if debt_to_equity is not None:
            lines.append(
                f"   Nợ/VCSH: {_series(inds, 'debt_to_equity', '.2f')}"
            )
        cagr_fl = _cagr(inds, "financial_leverage")
        cagr_fl_txt = f"{cagr_fl * 100:.2f}%/năm" if cagr_fl is not None else "—"

        # Phân tích chiến lược tài chính
        leverage_interpretation = ""
        if fin_leverage is not None:
            if fin_leverage < 1.5:
                leverage_interpretation = "→ **An toàn, ít dùng nợ** (vốn chủ sở hữu nhiều hơn nợ)"
            elif fin_leverage < 2.5:
                leverage_interpretation = "→ **Cân bằng**, sử dụng nợ vừa phải"
            else:
                leverage_interpretation = "→ **Rủi ro cao**, phụ thuộc nhiều vào nợ"

        lines.append(
            f"   • CAGR: {cagr_fl_txt}  →  Mức nợ đang {'tăng' if cagr_fl and cagr_fl > 0 else 'giảm' if cagr_fl else 'không xác định'}. "
            f"{leverage_interpretation}"
        )

    # Tổng hợp ROE từ 3 thành phần
    roe_latest = _latest(inds, "roe")
    if roe_latest is not None and net_margin is not None and asset_turnover is not None and fin_leverage is not None:
        lines.append("")
        lines.append("**Tổng hợp DuPont:**")
        calculated_roe = (net_margin / 100) * asset_turnover * fin_leverage * 100
        roe_pct = roe_latest * 100
        lines.append(
            f"   ROE năm gần nhất: {roe_pct:.2f}% "
            f"(từ công thức: {net_margin_pct:.2f}% × {asset_turnover:.2f}x × {fin_leverage:.2f}x ≈ {calculated_roe:.2f}%)"
        )

        cagr_roe = _cagr(inds, "roe")
        cagr_roe_txt = f"{cagr_roe * 100:.2f}%/năm" if cagr_roe is not None else "—"

        lines.append(
            f"   • Xu hướng ROE: {cagr_roe_txt}  →  Khả năng sinh lợi đang "
            f"{'tăng trưởng' if cagr_roe and cagr_roe > 0 else 'suy giảm' if cagr_roe else 'không tính được'}."
        )

        # Kết luận chiến lược
        lines.append("")
        lines.append("**Nhận xét chiến lược tài chính:**")

        if asset_turnover > 1.5 and fin_leverage >= 2:
            strategy = "Công ty phụ thuộc nợ để khai thác tài sản. ROE cao chủ yếu do đòn bẩy, rủi ro nếu tài chính suy thoái."
        elif asset_turnover > 1.5 and fin_leverage < 1.5:
            strategy = "Công ty khai thác tài sản tốt với vốn chủ yếu từ VCSH. Chiến lược bảo thủ, an toàn."
        elif asset_turnover <= 1.5 and fin_leverage >= 2:
            strategy = "Công ty dùng nợ để bù lại hiệu quả khai thác tài sản thấp. Rủi ro cao nếu doanh thu giảm."
        elif net_margin > 0.1:
            strategy = "Công ty lợi nhuận từ biên cao (margin tốt). Ít phụ thuộc vào đòn bẩy."
        else:
            strategy = "Công ty có ROE thấp. Cần cải thiện lợi nhuận hoặc hiệu quả khai thác tài sản."

        lines.append(f"   {strategy}")

    return "\n".join(lines).strip()


def _latest(rows: list[dict], key: str) -> float | None:
    """Giá trị của năm gần nhất có dữ liệu cho `key`."""
    best: tuple[int, float] | None = None
    for r in rows:
        year, value = r.get("year"), r.get(key)
        if year is None or _is_missing(value):
            continue
        try:
            y, v = int(year), float(value)
        except (TypeError, ValueError):
            continue
        if best is None or y > best[0]:
            best = (y, v)
    return best[1] if best else None


def _format_industry_comparison(inds: list[dict], industry_rows: list[dict],
                                is_financial: bool) -> list[str]:
    """Bảng so sánh mã CP với TRUNG VỊ ngành (cùng Industry ICB): giá trị năm gần
    nhất + CAGR của cả hai phía.

    `industry_rows` là chuỗi trung vị ngành theo năm đã precompute (bảng
    FA_Industry_Aggregate) — mỗi bản ghi có `year`, `peer_count` và các chỉ số.
    Trả về [] nếu ngành < 3 mã (trung vị không đủ tin cậy để so sánh)."""
    peer_count = max(
        (r.get("peer_count") or 0 for r in industry_rows),
        default=0,
    )
    if peer_count < 3:
        return []

    metrics = _COMPARE_METRICS_FINANCIAL if is_financial else _COMPARE_METRICS_NONFINANCIAL

    lines = [
        "",
        f"### So sánh với ngành (trung vị ~{peer_count} mã cùng ngành ICB)",
        "| Chỉ tiêu | Mã (gần nhất) | Ngành (trung vị) | CAGR mã | CAGR ngành |",
        "|---|---|---|---|---|",
    ]
    for label, key, spec, scale, suffix in metrics:
        stock_val = _fmt_val(_latest(inds, key), spec, scale, suffix)
        ind_val = _fmt_val(_latest(industry_rows, key), spec, scale, suffix)

        sc = _cagr(inds, key)
        ic = _cagr(industry_rows, key)
        stock_cagr = f"{sc * 100:.2f}%/năm" if sc is not None else "—"
        ind_cagr = f"{ic * 100:.2f}%/năm" if ic is not None else "—"

        lines.append(f"| {label} | {stock_val} | {ind_val} | {stock_cagr} | {ind_cagr} |")
    return lines


def _format_fundamental_output(summary, indicators, income_statements, cash_flows,
                               selection: dict, is_financial: bool = False,
                               industry_rows: list[dict] | None = None) -> str:
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

    if is_financial:
        sector_note = (
            "\n> 🏦 Ngành tài chính — phân tích theo khung CAMELS (C-A-M-E-L-S). "
            "Với mã ngân hàng có đủ dữ liệu, các cấu phần dùng chỉ số chuyên ngành "
            "(CAR, NPL, NIM, LDR, CIR); mã bảo hiểm/chứng khoán/BĐS dùng chỉ số "
            "tổng quát làm proxy do SSI chưa cung cấp chỉ số chuyên ngành cho nhóm này."
        )
    elif not latest_ind.get("gross_margin"):
        sector_note = "\n> ⚠️ Một số chỉ số không áp dụng cho ngành ngân hàng (gross margin, current ratio, D/E)."
    else:
        sector_note = ""

    parts = [f"## Phân tích cơ bản ({year_label}){sector_note}", ""]
    # Bỏ phần summary từ FA_Summary (database) vì nó không tuân thủ quy tắc ngành tài chính
    # (không biết trước là tài chính hay không tài chính). Aggregator sẽ tự tổng hợp phần
    # tóm tắt dựa trên các chỉ số cụ thể dưới đây.
    # parts.append("### Tóm tắt tổng quan")
    # parts.append((summary or {}).get("summary", "Không có dữ liệu"))

    # Các nhóm dưới đây kèm CAGR (tốc độ tăng trưởng kép trung bình năm) bên cạnh
    # chuỗi giá trị theo năm; riêng nhóm định giá không tính CAGR (chỉ số định
    # giá dao động theo giá thị trường nên tăng trưởng kép không mang nhiều ý nghĩa).
    if is_financial:
        # Ngành tài chính → khung CAMELS. Các toggle nhóm doanh nghiệp được ánh xạ
        # sang cấu phần CAMELS gần nhất: leverage→C, efficiency→A+M, profitability→E,
        # liquidity→L. S (độ nhạy) chỉ là caveat định tính (không có dữ liệu định lượng).
        # Ngân hàng có CAR/NPL/NIM/LDR/CIR thực tế từ SSI; bảo hiểm/chứng khoán/BĐS
        # (cùng nhóm ICB tài chính nhưng không phải TCTD) không có các chỉ số này
        # → _line trả về "—" khi thiếu dữ liệu, không cần nhánh riêng.
        has_bank_metrics = _latest(inds, "car") is not None or _latest(inds, "nim") is not None

        if selection.get("leverage", True):
            parts.append("")
            parts.append("### C — An toàn vốn (Capital adequacy)")
            if not has_bank_metrics:
                parts.append("> ℹ️ Chưa có CAR (mã không phải TCTD); dùng đòn bẩy & Nợ/VCSH & BVPS làm proxy.")
            parts.append(_line("CAR (hệ số an toàn vốn)", inds, "car", ".2f", scale=100, suffix="%", cagr=True))
            parts.append(_line("Đòn bẩy tài chính (Tổng TS/VCSH)", inds, "financial_leverage", ".2f", cagr=True))
            parts.append(_line("Nợ/Vốn chủ sở hữu", inds, "debt_to_equity", ".2f", cagr=True))
            parts.append(_line("VCSH/Tổng tài sản", inds, "equity_to_assets", ".2f", scale=100, suffix="%", cagr=True))
            parts.append(_line("VCSH/Tổng nợ", inds, "equity_to_liabilities", ".2f", scale=100, suffix="%", cagr=True))
            parts.append(_line("VCSH/Tổng cho vay", inds, "equity_to_loans", ".2f", scale=100, suffix="%", cagr=True))
            parts.append(_line("Giá trị sổ sách/CP (BVPS, đồng)", inds, "bvps", ",.0f", cagr=True))

        if selection.get("efficiency", True):
            parts.append("")
            parts.append("### A — Chất lượng tài sản (Asset quality)")
            if not has_bank_metrics:
                parts.append("> ℹ️ Chưa có tỷ lệ nợ xấu (NPL) / bao phủ nợ xấu (mã không phải TCTD); đánh giá qua proxy.")
            parts.append(_line("Tỷ lệ nợ xấu (NPL)", inds, "npl_ratio", ".2f", scale=100, suffix="%", cagr=True))
            parts.append(_line("Bao phủ nợ xấu (dự phòng/NPL)", inds, "npl_coverage_ratio", ".2f", scale=100, suffix="%", cagr=True))
            parts.append(_line("Dư nợ/Vốn chủ sở hữu", inds, "loans_to_equity", ".2f", cagr=True))
            parts.append(_line("ROA", inds, "roa", ".2f", scale=100, suffix="%", cagr=True))
            parts.append(_line("Dự phòng rủi ro tín dụng/Cho vay", inds, "loan_loss_reserve_ratio", ".2f", scale=100, suffix="%", cagr=True))
            parts.append(_line("Trích lập dự phòng/Cho vay", inds, "provision_expense_to_loans", ".2f", scale=100, suffix="%", cagr=True))
            parts.append(_line("Tăng trưởng tín dụng", inds, "credit_growth", ".2f", scale=100, suffix="%"))

            parts.append("")
            parts.append("### M — Năng lực quản trị (Management)")
            if not has_bank_metrics:
                parts.append("> ℹ️ Chưa có CIR (mã không phải TCTD); dùng hiệu suất khai thác tài sản làm proxy.")
            parts.append(_line("CIR (chi phí/thu nhập)", inds, "cir", ".2f", scale=100, suffix="%", cagr=True))
            parts.append(_line("Vòng quay tài sản", inds, "asset_turnover", ".2f", suffix="x", cagr=True))
            parts.append(_line("ROIC", inds, "roic", ".2f", scale=100, suffix="%", cagr=True))
            parts.append(_line("Thu nhập ngoài lãi/Thu nhập từ lãi", inds, "non_interest_to_interest_income", ".2f", scale=100, suffix="%", cagr=True))

        if selection.get("profitability", True):
            parts.append("")
            parts.append("### E — Khả năng sinh lời (Earnings)")
            if not has_bank_metrics:
                parts.append("> ℹ️ Chưa có NIM (mã không phải TCTD).")
            parts.append(_line("NIM (biên lãi thuần)", inds, "nim", ".2f", scale=100, suffix="%", cagr=True))
            parts.append(_line("ROE", inds, "roe", ".2f", scale=100, suffix="%", cagr=True))
            parts.append(_line("ROA", inds, "roa", ".2f", scale=100, suffix="%", cagr=True))
            parts.append(_line("Biên lợi nhuận ròng", inds, "net_margin", ".2f", scale=100, suffix="%", cagr=True))
            parts.append(_line("EPS (đồng)", inds, "eps", ",.0f", cagr=True))
            parts.append(_line("Thu nhập lãi thuần (đồng)", inds, "net_interest_income", ",.0f", cagr=True))
            parts.append(_line("Tăng trưởng thu nhập lãi thuần", inds, "nii_growth", ".2f", scale=100, suffix="%"))
            parts.append(_line("Tỉ suất sinh lời TS có sinh lãi (YOEA)", inds, "yield_on_earning_assets", ".2f", scale=100, suffix="%", cagr=True))
            parts.append(_line("Chi phí vốn bình quân (COF)", inds, "cost_of_funds", ".2f", scale=100, suffix="%", cagr=True))
            parts.append(_line("Tỉ lệ CASA (tiền gửi không kỳ hạn)", inds, "casa_ratio", ".2f", scale=100, suffix="%", cagr=True))
            # Thêm phân tích DuPont cho ngành tài chính
            dupont_text = _dupont_analysis(inds)
            if dupont_text:
                parts.append(dupont_text)

        if selection.get("liquidity", True):
            parts.append("")
            parts.append("### L — Thanh khoản (Liquidity)")
            if not has_bank_metrics:
                parts.append("> ℹ️ Chưa có LDR (mã không phải TCTD).")
            parts.append(_line("LDR (dư nợ/huy động)", inds, "ldr", ".2f", scale=100, suffix="%", cagr=True))
            parts.append(_line("Thanh toán tiền mặt", inds, "cash_ratio", ".2f", cagr=True))
            parts.append(_line("Thanh toán nhanh", inds, "quick_ratio", ".2f", cagr=True))
            parts.append(_line("Thanh toán hiện hành", inds, "current_ratio", ".2f", cagr=True))
            parts.append(_line("Tăng trưởng huy động tiền gửi", inds, "deposit_growth", ".2f", scale=100, suffix="%"))

        # S — Sensitivity: không có dữ liệu định lượng → chỉ nêu caveat, hiển thị khi
        # có ít nhất 1 cấu phần CAMELS khác được bật.
        if any(selection.get(k, True) for k in ("leverage", "efficiency", "profitability", "liquidity")):
            parts += [
                "",
                "### S — Độ nhạy rủi ro thị trường (Sensitivity)",
                "> ℹ️ Chưa có dữ liệu định lượng về độ nhạy lãi suất/tỷ giá; cần đánh giá "
                "định tính từ cơ cấu tài sản–nguồn vốn và tỷ trọng thu nhập lãi.",
            ]
    else:
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
            # Thêm phân tích DuPont
            dupont_text = _dupont_analysis(inds)
            if dupont_text:
                parts.append(dupont_text)

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
            # Thêm phân tích DuPont nếu chưa có trong leverage section
            if not selection.get("leverage", True):
                dupont_text = _dupont_analysis(inds)
                if dupont_text:
                    parts.append(dupont_text)

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

    # Bảng so sánh với trung vị ngành (cùng Industry ICB) — bổ trợ cho các nhóm trên.
    if industry_rows:
        parts += _format_industry_comparison(inds, industry_rows, is_financial)

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

        # Nhận diện ngành ICB để (1) bỏ P/E khỏi định giá nếu là tài chính và (2)
        # so sánh với trung vị ngành. Lỗi/thiếu profile KHÔNG được chặn phân tích
        # cơ bản → mặc định coi như không phải tài chính, không có so sánh ngành.
        icb_code = None
        try:
            profile = CompanyService.get_profile(symbol)
            if profile:
                icb_code = profile.get("icb_code")
                if icb_code:
                    print(f"[Fundamental Analysis Agent] {symbol}: ICB code = {icb_code}")
                else:
                    print(f"[Fundamental Analysis Agent] {symbol}: profile không có icb_code")
            else:
                print(f"[Fundamental Analysis Agent] {symbol}: không lấy được profile")
        except Exception as e:
            print(f"[Fundamental Analysis Agent] Lỗi lấy profile cho {symbol}: {e}")
        is_financial = _is_financial_sector(icb_code)
        print(f"[Fundamental Analysis Agent] {symbol}: is_financial = {is_financial} (icb_code={icb_code})")

        # Trung vị ngành đã precompute (bảng FA_Industry_Aggregate) để so sánh. Lỗi/
        # thiếu/chưa precompute → coi như không có so sánh ngành, không làm hỏng phân tích.
        industry_rows: list[dict] = []
        if icb_code:
            try:
                industry_rows = FundamentalAnalysisService.get_industry_aggregate(icb_code)
                if industry_rows:
                    print(f"[Fundamental Analysis Agent] {symbol}: Lấy được {len(industry_rows)} hàng so sánh ngành")
                else:
                    print(f"[Fundamental Analysis Agent] {symbol}: Không có dữ liệu so sánh ngành cho ICB {icb_code}")
            except Exception as e:
                print(f"[Fundamental Analysis Agent] {symbol}: Lỗi lấy trung vị ngành (ICB {icb_code}): {e}")
        else:
            print(f"[Fundamental Analysis Agent] {symbol}: Không có icb_code → bỏ qua so sánh ngành")

        if not indicators and not income_statements and not cash_flows and not summary:
            output = "Không có dữ liệu phân tích cơ bản."
        else:
            output = _format_fundamental_output(
                summary, indicators, income_statements, cash_flows, selection,
                is_financial, industry_rows,
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