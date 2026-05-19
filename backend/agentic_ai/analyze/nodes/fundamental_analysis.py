from agentic_ai.analyze.state import AgentState
from app.services.fundamental_analysis_service import FundamentalAnalysisService


def _fmt(value, spec: str) -> str:
    if value is None:
        return ""
    try:
        return format(float(value), spec)
    except (TypeError, ValueError):
        return ""


def _safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        f = float(value)
        if f != f:  # NaN check
            return None
        return f
    except (TypeError, ValueError):
        return None


# ─────────────────────────────────────────────────────────────
# Pre-computed fundamental scoring — đếm điểm trong code
# ─────────────────────────────────────────────────────────────

def _compute_fundamental_score(latest_ind: dict, latest_cf: dict) -> dict:
    """
    Đếm điểm theo 5 tiêu chí trong aggregator prompt:
      + PE < 18 → tốt
      + ROE > 15% → tốt
      + Doanh thu tăng YoY → tốt
      + Lợi nhuận tăng YoY → tốt
      + CFO > 0 → tốt

    ≥ 3/5 → TỐT, 2/5 → TRUNG BÌNH, < 2/5 → YẾU.

    Lưu ý ngành ngân hàng: gross_margin = None → là dấu hiệu nhận biết.
    Với ngân hàng KHÔNG tính điểm "current_ratio" và "D/E" — đã loại khỏi tiêu chí.
    """
    signals: list[str] = []
    weaknesses: list[str] = []
    score = 0
    max_score = 5

    pe = _safe_float(latest_ind.get("pe_ratio"))
    roe = _safe_float(latest_ind.get("roe"))
    revenue_yoy = _safe_float(latest_ind.get("revenue_yoy"))
    profit_yoy = _safe_float(latest_ind.get("profit_yoy"))
    cfo = _safe_float(latest_cf.get("cfo"))

    if pe is not None:
        if pe < 18 and pe > 0:
            score += 1
            signals.append(f"PE={pe:.2f} (rẻ/hợp lý)")
        else:
            weaknesses.append(f"PE={pe:.2f} (đắt hoặc âm)")

    if roe is not None:
        if roe > 0.15:
            score += 1
            signals.append(f"ROE={roe*100:.2f}% > 15% (sinh lời tốt)")
        else:
            weaknesses.append(f"ROE={roe*100:.2f}% < 15%")

    if revenue_yoy is not None:
        if revenue_yoy > 0:
            score += 1
            signals.append(f"Doanh thu YoY +{revenue_yoy*100:.2f}%")
        else:
            weaknesses.append(f"Doanh thu YoY {revenue_yoy*100:.2f}%")

    if profit_yoy is not None:
        if profit_yoy > 0:
            score += 1
            signals.append(f"Lợi nhuận YoY +{profit_yoy*100:.2f}%")
        else:
            weaknesses.append(f"Lợi nhuận YoY {profit_yoy*100:.2f}%")

    if cfo is not None:
        if cfo > 0:
            score += 1
            signals.append(f"CFO dương ({cfo/1e9:,.1f} tỷ)")
        else:
            weaknesses.append(f"CFO âm ({cfo/1e9:,.1f} tỷ)")

    # Classification — chỉ áp dụng nếu có ≥ 3 chỉ số đánh giá được
    evaluated = len(signals) + len(weaknesses)
    if evaluated < 3:
        classification = "DỮ LIỆU THIẾU"
    elif score >= 3:
        classification = "TỐT"
    elif score == 2:
        classification = "TRUNG BÌNH"
    else:
        classification = "YẾU"

    is_bank = latest_ind.get("gross_margin") in (None, 0)

    return {
        "score": score,
        "max_score": max_score,
        "classification": classification,
        "signals": signals,
        "weaknesses": weaknesses,
        "is_bank_or_finance": is_bank,
    }


def _format_fundamental_output(summary, indicators, income_statements, cash_flows) -> dict:
    latest_ind = next((i for i in indicators if i["year"] == max(i["year"] for i in indicators)), {})
    latest_inc = next((i for i in income_statements if i["year"] == max(i["year"] for i in income_statements)), {})
    latest_cf  = next((i for i in cash_flows if i["year"] == max(i["year"] for i in cash_flows)), {})

    year = latest_ind.get("year", "N/A")

    score_info = _compute_fundamental_score(latest_ind, latest_cf)

    if score_info["is_bank_or_finance"]:
        sector_note = "\n> ⚠️ Một số chỉ số không áp dụng cho ngành ngân hàng (gross margin, current ratio, D/E)."
    else:
        sector_note = ""

    signals_lines = "\n".join(f"  ✓ {s}" for s in score_info["signals"]) or "  (không có)"
    weakness_lines = "\n".join(f"  ✗ {w}" for w in score_info["weaknesses"]) or "  (không có)"

    display = f"""
## Phân tích cơ bản ({year}){sector_note}

### Đánh giá tổng hợp (pre-computed)
- Phân loại: **{score_info["classification"]}** ({score_info["score"]}/{score_info["max_score"]} điểm)
- Điểm mạnh:
{signals_lines}
- Điểm yếu:
{weakness_lines}

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

    return {
        "display": display,
        "signal": score_info["classification"],
        "score": score_info["score"],
        "max_score": score_info["max_score"],
        "signals": score_info["signals"],
        "weaknesses": score_info["weaknesses"],
        "is_bank_or_finance": score_info["is_bank_or_finance"],
        "year": year,
    }


def fundamental_analysis_agent(state: AgentState) -> AgentState:
    symbol = state.get("symbol", "")

    income_statements = FundamentalAnalysisService.get_income_statements(symbol)
    cash_flows = FundamentalAnalysisService.get_cash_flows(symbol)
    indicators = FundamentalAnalysisService.get_indicators(symbol)
    summary = FundamentalAnalysisService.get_summary(symbol)

    if not indicators or not income_statements or not cash_flows:
        return {
            "agent_results": {
                "fundamental_analysis_agent": {
                    "display": "Không có đủ dữ liệu cơ bản.",
                    "signal": "NO_DATA",
                    "score": 0,
                    "max_score": 5,
                    "signals": [],
                    "weaknesses": [],
                    "is_bank_or_finance": False,
                    "year": None,
                },
            },
        }

    output = _format_fundamental_output(summary, indicators, income_statements, cash_flows)

    print("[Fundamental Analysis Agent] Output:", output["display"])
    print(f"[Fundamental Analysis Agent] Signal: {output['signal']} ({output['score']}/{output['max_score']})")

    return {
        "agent_results": {
            "fundamental_analysis_agent": output,
        },
    }
