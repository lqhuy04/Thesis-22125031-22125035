"""Fundamental-data preparation node for the v2 analysis graph."""

import logging
import math
from datetime import date
from dataclasses import dataclass

from agentic_ai_v2.analyze.state import AgentState
from app.services.company_service import CompanyService
from app.services.fundamental_analysis_service import FundamentalAnalysisService

logger = logging.getLogger(__name__)

_YEARS_TO_ANALYZE = 5


@dataclass(frozen=True)
class Metric:
    label: str
    key: str
    format_spec: str = ".2f"
    scale: float = 1
    suffix: str = ""
    include_cagr: bool = True


@dataclass(frozen=True)
class Section:
    title: str
    metrics: tuple[Metric, ...]


_STANDARD_SECTIONS = (
    Section(
        "Khả năng thanh toán",
        (
            Metric("Thanh toán hiện hành", "current_ratio"),
            Metric("Thanh toán nhanh", "quick_ratio"),
            Metric("Thanh toán tiền mặt", "cash_ratio"),
        ),
    ),
    Section(
        "Đòn bẩy tài chính",
        (
            Metric("Nợ/Vốn chủ sở hữu", "debt_to_equity"),
            Metric("Đòn bẩy tài chính", "financial_leverage"),
            Metric("Khả năng trả lãi", "interest_coverage", suffix="x"),
        ),
    ),
    Section(
        "Hiệu quả hoạt động",
        (
            Metric("Vòng quay tài sản", "asset_turnover", suffix="x"),
            Metric("Vòng quay tài sản cố định", "fixed_asset_turnover", suffix="x"),
            Metric("Số ngày tồn kho", "days_inventory", ",.0f", suffix=" ngày"),
            Metric("Số ngày phải thu", "days_receivable", ",.0f", suffix=" ngày"),
        ),
    ),
    Section(
        "Khả năng sinh lời",
        (
            Metric("ROE", "roe", scale=100, suffix="%"),
            Metric("ROA", "roa", scale=100, suffix="%"),
            Metric("Biên lợi nhuận gộp", "gross_margin", scale=100, suffix="%"),
            Metric("Biên lợi nhuận ròng", "net_margin", scale=100, suffix="%"),
        ),
    ),
    Section(
        "Định giá",
        (
            Metric("P/E", "pe_ratio", include_cagr=False),
            Metric("P/B", "pb_ratio", include_cagr=False),
            Metric("EV/EBITDA", "ev_ebitda", include_cagr=False),
            Metric("EPS", "eps", ",.0f", suffix=" đồng", include_cagr=False),
        ),
    ),
)

_FINANCIAL_SECTIONS = (
    Section(
        "C — An toàn vốn",
        (
            Metric("CAR", "car", scale=100, suffix="%"),
            Metric("Đòn bẩy tài chính", "financial_leverage"),
            Metric("Nợ/Vốn chủ sở hữu", "debt_to_equity"),
            Metric("VCSH/Tổng tài sản", "equity_to_assets", scale=100, suffix="%"),
        ),
    ),
    Section(
        "A/M — Chất lượng tài sản và năng lực quản trị",
        (
            Metric("Tỷ lệ nợ xấu", "npl_ratio", scale=100, suffix="%"),
            Metric("Bao phủ nợ xấu", "npl_coverage_ratio", scale=100, suffix="%"),
            Metric("CIR", "cir", scale=100, suffix="%"),
            Metric("ROIC", "roic", scale=100, suffix="%"),
        ),
    ),
    Section(
        "E — Khả năng sinh lời",
        (
            Metric("NIM", "nim", scale=100, suffix="%"),
            Metric("ROE", "roe", scale=100, suffix="%"),
            Metric("ROA", "roa", scale=100, suffix="%"),
            Metric("Biên lợi nhuận ròng", "net_margin", scale=100, suffix="%"),
            Metric("EPS", "eps", ",.0f", suffix=" đồng"),
        ),
    ),
    Section(
        "L — Thanh khoản",
        (
            Metric("LDR", "ldr", scale=100, suffix="%"),
            Metric("Thanh toán tiền mặt", "cash_ratio"),
            Metric("Thanh toán nhanh", "quick_ratio"),
        ),
    ),
    Section(
        "Định giá",
        (
            Metric("P/B", "pb_ratio", include_cagr=False),
            Metric("EPS", "eps", ",.0f", suffix=" đồng", include_cagr=False),
        ),
    ),
)

_STANDARD_COMPARISON_METRICS = (
    Metric("ROE", "roe", scale=100, suffix="%"),
    Metric("ROA", "roa", scale=100, suffix="%"),
    Metric("Biên lợi nhuận gộp", "gross_margin", scale=100, suffix="%"),
    Metric("Biên lợi nhuận ròng", "net_margin", scale=100, suffix="%"),
    Metric("Vòng quay tài sản", "asset_turnover", suffix="x"),
    Metric("Nợ/Vốn chủ sở hữu", "debt_to_equity"),
    Metric("P/E", "pe_ratio", include_cagr=False),
    Metric("P/B", "pb_ratio", include_cagr=False),
)

_FINANCIAL_COMPARISON_METRICS = (
    Metric("ROE", "roe", scale=100, suffix="%"),
    Metric("ROA", "roa", scale=100, suffix="%"),
    Metric("NIM", "nim", scale=100, suffix="%"),
    Metric("Tỷ lệ nợ xấu", "npl_ratio", scale=100, suffix="%"),
    Metric("CAR", "car", scale=100, suffix="%"),
    Metric("LDR", "ldr", scale=100, suffix="%"),
    Metric("P/B", "pb_ratio", include_cagr=False),
)

_DUPONT_PERCENT = Metric("", "", scale=100, suffix="%")
_DUPONT_MULTIPLE = Metric("", "", suffix="x")


def _to_float(value) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _is_missing(value) -> bool:
    return _to_float(value) is None


def _latest_years(rows: list[dict]) -> list[dict]:
    valid_rows = []
    for row in rows:
        try:
            year = int(row["year"])
        except (KeyError, TypeError, ValueError):
            continue
        valid_rows.append((year, row))

    valid_rows.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in reversed(valid_rows[:_YEARS_TO_ANALYZE])]


def _cagr(rows: list[dict], key: str) -> float | None:
    values: list[tuple[int, float]] = []
    for row in rows:
        value = _to_float(row.get(key))
        if value is None:
            continue
        try:
            values.append((int(row["year"]), value))
        except (KeyError, TypeError, ValueError):
            continue

    if len(values) < 2:
        return None

    values.sort()
    first_year, first_value = values[0]
    last_year, last_value = values[-1]
    year_count = last_year - first_year

    if year_count <= 0 or first_value <= 0 or last_value <= 0:
        return None
    return (last_value / first_value) ** (1 / year_count) - 1


def _format_metric(rows: list[dict], metric: Metric) -> str:
    values = []
    for row in rows:
        value = _to_float(row.get(metric.key))
        if value is None:
            formatted = "—"
        else:
            formatted = (
                f"{format(value * metric.scale, metric.format_spec)}"
                f"{metric.suffix}"
            )
        values.append(f"{row['year']}: {formatted}")

    line = f"- {metric.label}: {' | '.join(values)}"
    if metric.include_cagr:
        growth = _cagr(rows, metric.key)
        growth_text = f"{growth * 100:.2f}%/năm" if growth is not None else "—"
        line += f" · CAGR: {growth_text}"
    return line


def _latest_value(rows: list[dict], key: str) -> float | None:
    for row in reversed(rows):
        value = _to_float(row.get(key))
        if value is not None:
            return value
    return None


def _format_value(value: float | None, metric: Metric) -> str:
    if value is None:
        return "—"
    return (
        f"{format(value * metric.scale, metric.format_spec)}"
        f"{metric.suffix}"
    )


def _format_dupont(rows: list[dict]) -> str:
    table_rows = []
    for row in rows:
        net_margin = _to_float(row.get("net_margin"))
        asset_turnover = _to_float(row.get("asset_turnover"))
        financial_leverage = _to_float(row.get("financial_leverage"))
        reported_roe = _to_float(row.get("roe"))

        components = (
            net_margin,
            asset_turnover,
            financial_leverage,
        )
        if any(value is None for value in components):
            calculated_roe = None
        else:
            calculated_roe = net_margin * asset_turnover * financial_leverage

        table_rows.append(
            "| {year} | {margin} | {turnover} | {leverage} | {calculated} | {reported} |".format(
                year=row["year"],
                margin=_format_value(net_margin, _DUPONT_PERCENT),
                turnover=_format_value(asset_turnover, _DUPONT_MULTIPLE),
                leverage=_format_value(financial_leverage, _DUPONT_MULTIPLE),
                calculated=_format_value(calculated_roe, _DUPONT_PERCENT),
                reported=_format_value(reported_roe, _DUPONT_PERCENT),
            )
        )

    has_complete_row = any(
        all(
            _to_float(row.get(key)) is not None
            for key in ("net_margin", "asset_turnover", "financial_leverage")
        )
        for row in rows
    )
    if not has_complete_row:
        return ""

    return "\n".join(
        [
            "### Phân tích DuPont",
            "> ROE = Biên lợi nhuận ròng × Vòng quay tài sản × Đòn bẩy tài chính.",
            "| Năm | Biên LN ròng | Vòng quay TS | Đòn bẩy TC | ROE DuPont | ROE báo cáo |",
            "|---|---:|---:|---:|---:|---:|",
            *table_rows,
        ]
    )


def _format_industry_comparison(
    stock_rows: list[dict],
    industry_rows: list[dict],
    is_financial: bool,
) -> str:
    industry_rows = _latest_years(industry_rows)
    peer_counts = []
    for row in industry_rows:
        try:
            peer_counts.append(int(row.get("peer_count") or 0))
        except (TypeError, ValueError):
            continue
    peer_count = max(peer_counts, default=0)
    if peer_count < 3:
        return ""

    metrics = (
        _FINANCIAL_COMPARISON_METRICS
        if is_financial
        else _STANDARD_COMPARISON_METRICS
    )
    table_rows = []

    for metric in metrics:
        stock_value = _format_value(
            _latest_value(stock_rows, metric.key),
            metric,
        )
        industry_value = _format_value(
            _latest_value(industry_rows, metric.key),
            metric,
        )
        stock_cagr = _cagr(stock_rows, metric.key)
        industry_cagr = _cagr(industry_rows, metric.key)

        table_rows.append(
            "| {label} | {stock} | {industry} | {stock_cagr} | {industry_cagr} |".format(
                label=metric.label,
                stock=stock_value,
                industry=industry_value,
                stock_cagr=(
                    f"{stock_cagr * 100:.2f}%/năm"
                    if stock_cagr is not None
                    else "—"
                ),
                industry_cagr=(
                    f"{industry_cagr * 100:.2f}%/năm"
                    if industry_cagr is not None
                    else "—"
                ),
            )
        )

    if not table_rows:
        return ""

    return "\n".join(
        [
            f"### So sánh với ngành (trung vị {peer_count} mã cùng ngành ICB)",
            "| Chỉ tiêu | Mã (gần nhất) | Ngành (trung vị) | CAGR mã | CAGR ngành |",
            "|---|---:|---:|---:|---:|",
            *table_rows,
        ]
    )


def _get_company_context(symbol: str) -> tuple[bool, str | None]:
    try:
        profile = CompanyService.get_profile(symbol)
    except Exception:
        logger.exception("Unable to load company profile for %s", symbol)
        return False, None

    icb_code = (profile or {}).get("icb_code")
    normalized_icb_code = str(icb_code).strip() if icb_code else None
    return bool(normalized_icb_code and normalized_icb_code.startswith("8")), normalized_icb_code


def _get_industry_rows(icb_code: str | None) -> list[dict]:
    if not icb_code:
        return []
    try:
        return FundamentalAnalysisService.get_industry_aggregate(icb_code)
    except Exception:
        logger.exception(
            "Unable to load industry aggregate for ICB %s",
            icb_code,
        )
        return []


def _rows_available_before(
    rows: list[dict],
    as_of_date: date | None,
) -> list[dict]:
    """Exclude same-year/future annual data from historical backtests.

    FA_Indicator and FA_Industry_Aggregate only expose an annual ``year`` field,
    not a publication timestamp. The conservative boundary below ensures a
    backtest never reads financial data for the year being simulated.
    """
    if as_of_date is None:
        return rows

    available_rows = []
    for row in rows:
        try:
            year = int(row.get("year"))
        except (TypeError, ValueError):
            continue
        if year < as_of_date.year:
            available_rows.append(row)
    return available_rows


def _fundamental_as_of_date(state: AgentState) -> date | None:
    value = ((state.get("plan") or {}).get("fundamental") or {}).get(
        "as_of_date"
    )
    if not value:
        return None
    return date.fromisoformat(value)


def _format_output(
    indicators: list[dict],
    is_financial: bool,
    industry_rows: list[dict] | None = None,
) -> str:
    rows = _latest_years(indicators)
    if not rows:
        return "Không có dữ liệu phân tích cơ bản."

    first_year, last_year = rows[0]["year"], rows[-1]["year"]
    year_label = (
        str(first_year)
        if first_year == last_year
        else f"{first_year}–{last_year}"
    )
    sections = _FINANCIAL_SECTIONS if is_financial else _STANDARD_SECTIONS
    output = [f"## Phân tích cơ bản ({year_label})"]

    if is_financial:
        output += [
            "",
            "> Ngành tài chính — sử dụng các chỉ số CAMEL và định giá bằng P/B.",
        ]

    for section in sections:
        output += [
            "",
            f"### {section.title}",
            *(_format_metric(rows, metric) for metric in section.metrics),
        ]

    dupont_output = _format_dupont(rows)
    if dupont_output:
        output += ["", dupont_output]

    industry_output = _format_industry_comparison(
        stock_rows=rows,
        industry_rows=industry_rows or [],
        is_financial=is_financial,
    )
    if industry_output:
        output += ["", industry_output]

    return "\n".join(output)


def fundamental_agent(state: AgentState) -> dict:
    """Load and format fundamental indicators for the selected stock."""
    symbol = state.get("symbol", "").strip().upper()

    try:
        as_of_date = _fundamental_as_of_date(state)
        indicators = _rows_available_before(
            FundamentalAnalysisService.get_indicators(symbol),
            as_of_date,
        )
        is_financial, icb_code = _get_company_context(symbol)
        output = _format_output(
            indicators=indicators,
            is_financial=is_financial,
            industry_rows=_rows_available_before(
                _get_industry_rows(icb_code),
                as_of_date,
            ),
        )
    except Exception:
        logger.exception("Fundamental data preparation failed for %s", symbol)
        output = "Không có dữ liệu phân tích cơ bản."

    print(f"Fundamental output for {symbol}:\n{output}")

    return {
        "agent_results": {
            "fundamental_agent": output,
        },
    }
