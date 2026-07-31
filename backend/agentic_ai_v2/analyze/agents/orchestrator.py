"""Deterministic plan builder for the v2 analysis graph."""

from datetime import date, datetime, timedelta, timezone
from typing import Literal

from agentic_ai_v2.analyze.state import AgentState


InvestmentPeriod = Literal["short_term", "mid_term", "long_term"]

_VIETNAM_TIMEZONE = timezone(timedelta(hours=7))

_PERIOD_RULES = {
    "short_term": {
        "technical_interval": "1h",
        "technical_lookback_days": 90,
        "article_lookback_days": 30,
    },
    "mid_term": {
        "technical_interval": "1d",
        "technical_lookback_days": 365,
        "article_lookback_days": 90,
    },
    "long_term": {
        "technical_interval": "1w",
        "technical_lookback_days": 1825,
        "article_lookback_days": 365,
    },
}


def _today_in_vietnam() -> date:
    return datetime.now(_VIETNAM_TIMEZONE).date()


def build_analysis_plan(
    period: InvestmentPeriod,
    as_of_date: date | None = None,
) -> dict:
    """Build source date ranges for an investment horizon and analysis date."""
    rule = _PERIOD_RULES[period]
    to_date = as_of_date or _today_in_vietnam()

    technical_from_date = to_date - timedelta(
        days=rule["technical_lookback_days"]
    )
    article_from_date = to_date - timedelta(
        days=rule["article_lookback_days"]
    )

    return {
        "technical": {
            "from_date": technical_from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "interval": rule["technical_interval"],
        },
        "article": {
            "from_date": article_from_date.isoformat(),
            "to_date": to_date.isoformat(),
        },
    }


def orchestrator_agent(state: AgentState) -> dict:
    """Create the analysis plan from risk_appetite.period."""
    period = state["risk_appetite"]["period"]

    return {"plan": build_analysis_plan(period)}
