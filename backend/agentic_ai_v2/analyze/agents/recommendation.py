"""Deterministic recommendation scoring plus an LLM-generated trading plan."""

import json
import logging
import math
from typing import Any

from pydantic import BaseModel, Field

from agentic_ai_v2.analyze.language import localized_text
from agentic_ai_v2.analyze.state import AgentState
from agentic_ai_v2.service.deepseek_service import create_structured_completion

logger = logging.getLogger(__name__)

_MAX_OUTPUT_TOKENS = 1_000

SCORE_THRESHOLD = 0.60
TECHNICAL_SCORE_THRESHOLD_BY_PERIOD = {
    "short_term": 0.60,
    "mid_term": 0.50,
    "long_term": 0.40,
}
MANUAL_TECHNICAL_GATE_MIN_WEIGHT = 0.15
WEIGHTS_BY_PERIOD = {
    "short_term": {
        "fundamental": 0.10,
        "technical": 0.60,
        "article": 0.30,
    },
    "mid_term": {
        "fundamental": 0.40,
        "technical": 0.40,
        "article": 0.20,
    },
    "long_term": {
        "fundamental": 0.70,
        "technical": 0.15,
        "article": 0.15,
    },
}
INTERVAL_BY_PERIOD = {
    "short_term": "1h",
    "mid_term": "1d",
    "long_term": "1w",
}

MIN_REWARD_TO_RISK_RATIO = 1.5
PLAN_RULES_BY_PERIOD = {
    "short_term": {
        "take_profit_pct": (0.08, 0.15),
        "stop_loss_pct": (0.04, 0.07),
        "max_hold_candles": (5, 15),
    },
    "mid_term": {
        "take_profit_pct": (0.15, 0.30),
        "stop_loss_pct": (0.07, 0.12),
        "max_hold_candles": (15, 60),
    },
    "long_term": {
        "take_profit_pct": (0.40, 0.80),
        "stop_loss_pct": (0.15, 0.20),
        "max_hold_candles": (26, 104),
    },
}

_FALLBACK_PLAN_BY_PERIOD = {
    "short_term": {
        "take_profit_pct": 0.10,
        "stop_loss_pct": 0.05,
        "max_hold_candles": 15,
    },
    "mid_term": {
        "take_profit_pct": 0.20,
        "stop_loss_pct": 0.10,
        "max_hold_candles": 30,
    },
    "long_term": {
        "take_profit_pct": 0.50,
        "stop_loss_pct": 0.18,
        "max_hold_candles": 26,
    },
}

_SYSTEM_PROMPT = """Bạn là chuyên gia lập kế hoạch giao dịch cổ phiếu Việt Nam.

Quyết định Mua đã được hệ thống xác định bằng công thức điểm cố định. Bạn KHÔNG
được thay đổi quyết định hoặc tính lại điểm. Dựa duy nhất trên dữ liệu article,
fundamental và technical được cung cấp, hãy trả về:
- take_profit: mức giá chốt lời lớn hơn current_price.
- stop_loss: mức giá cắt lỗ dương và nhỏ hơn current_price.
- max_hold_candles: số cây nến tối đa nên giữ theo đúng interval được cung cấp.

Bạn BẮT BUỘC tuân thủ trading_plan_constraints trong dữ liệu đầu vào, gồm khoảng
phần trăm chốt lời/cắt lỗ, khoảng số nến giữ và reward_to_risk_ratio tối thiểu.
Phần trăm chốt lời và cắt lỗ đều được tính từ current_price.

Ưu tiên vùng hỗ trợ/kháng cự, Bollinger Bands, MA và mức độ rủi ro thể hiện trong
tin tức/cơ bản. Không bịa dữ liệu; nếu dữ liệu không đủ thì chọn kế hoạch thận
trọng dựa quanh current_price. Đơn vị giá phải giống current_price.
"""


class TradingPlanOutput(BaseModel):
    take_profit: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    max_hold_candles: int = Field(gt=0)


def _finite_score(value: Any) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(parsed):
        return 0.0
    return min(max(parsed, 0.0), 1.0)


def _normalize_period(value: Any) -> str:
    period = str(value or "").strip().lower()
    if period in WEIGHTS_BY_PERIOD:
        return period
    return "mid_term"


def _analysis_scores(results: dict[str, Any]) -> dict[str, float]:
    return {
        "article": _finite_score(
            (results.get("article_analysis_agent") or {}).get("score")
        ),
        "fundamental": _finite_score(
            (results.get("fundamental_analysis_agent") or {}).get("score")
        ),
        "technical": _finite_score(
            (results.get("technical_analysis_agent") or {}).get("score")
        ),
    }


def _weights_for_state(
    state: AgentState,
    period: str,
) -> dict[str, float]:
    default_weights = WEIGHTS_BY_PERIOD[_normalize_period(period)]
    if state.get("mode") != "manual":
        return default_weights

    payload_weights = (
        (state.get("data_selection") or {}).get("weight") or {}
    )
    if not isinstance(payload_weights, dict):
        return default_weights

    manual_weights = {
        "article": _finite_score(payload_weights.get("news")),
        "technical": _finite_score(payload_weights.get("technical")),
        "fundamental": _finite_score(payload_weights.get("fundamental")),
    }
    if not math.isclose(
        sum(manual_weights.values()),
        1.0,
        abs_tol=1e-6,
    ):
        logger.warning(
            "Invalid manual recommendation weights; using period defaults"
        )
        return default_weights

    return manual_weights


def _calculate_total_score(
    period: str,
    scores: dict[str, float],
    weights: dict[str, float] | None = None,
) -> float:
    normalized_period = _normalize_period(period)
    effective_weights = weights or WEIGHTS_BY_PERIOD[normalized_period]
    return round(
        sum(
            scores[name] * effective_weights[name]
            for name in effective_weights
        ),
        4,
    )


def _passes_technical_gate(
    state: AgentState,
    period: str,
    technical_score: float,
    weights: dict[str, float],
) -> bool:
    if (
        state.get("mode") == "manual"
        and weights["technical"] < MANUAL_TECHNICAL_GATE_MIN_WEIGHT
    ):
        return True
    threshold = TECHNICAL_SCORE_THRESHOLD_BY_PERIOD[
        _normalize_period(period)
    ]
    return technical_score >= threshold


def _current_price(results: dict[str, Any]) -> float | None:
    technical = results.get("technical_agent") or {}
    price = (technical.get("current_price") or {}).get("value")
    try:
        parsed = float(price)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed) or parsed <= 0:
        return None
    return parsed


def _call_trading_plan_llm(
    state: AgentState,
    period: str,
    total_score: float,
    scores: dict[str, float],
) -> TradingPlanOutput:
    results = state.get("agent_results") or {}
    context = {
        "symbol": state.get("symbol"),
        "period": period,
        "interval": INTERVAL_BY_PERIOD[period],
        "total_score": total_score,
        "component_scores": scores,
        "current_price": _current_price(results),
        "trading_plan_constraints": {
            "take_profit_percent": {
                "min": PLAN_RULES_BY_PERIOD[period]["take_profit_pct"][0]
                * 100,
                "max": PLAN_RULES_BY_PERIOD[period]["take_profit_pct"][1]
                * 100,
            },
            "stop_loss_percent": {
                "min": PLAN_RULES_BY_PERIOD[period]["stop_loss_pct"][0]
                * 100,
                "max": PLAN_RULES_BY_PERIOD[period]["stop_loss_pct"][1]
                * 100,
            },
            "max_hold_candles": {
                "min": PLAN_RULES_BY_PERIOD[period][
                    "max_hold_candles"
                ][0],
                "max": PLAN_RULES_BY_PERIOD[period][
                    "max_hold_candles"
                ][1],
            },
            "minimum_reward_to_risk_ratio": MIN_REWARD_TO_RISK_RATIO,
        },
        "article": {
            "data": results.get("article_agent"),
            "analysis": results.get("article_analysis_agent"),
        },
        "fundamental": {
            "data": results.get("fundamental_agent"),
            "analysis": results.get("fundamental_analysis_agent"),
        },
        "technical": {
            "data": results.get("technical_agent"),
            "analysis": results.get("technical_analysis_agent"),
        },
    }

    return create_structured_completion(
        temperature=0.1,
        max_tokens=_MAX_OUTPUT_TOKENS,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    context,
                    ensure_ascii=False,
                    indent=2,
                ),
            },
        ],
        output_model=TradingPlanOutput,
    )


def _is_valid_plan(
    plan: TradingPlanOutput,
    current_price: float | None,
    period: str,
) -> bool:
    if current_price is None:
        return False
    if not plan.stop_loss < current_price < plan.take_profit:
        return False

    rules = PLAN_RULES_BY_PERIOD[_normalize_period(period)]
    take_profit_pct = (plan.take_profit - current_price) / current_price
    stop_loss_pct = (current_price - plan.stop_loss) / current_price
    take_profit_min, take_profit_max = rules["take_profit_pct"]
    stop_loss_min, stop_loss_max = rules["stop_loss_pct"]
    hold_min, hold_max = rules["max_hold_candles"]

    within_period_ranges = (
        take_profit_min <= take_profit_pct <= take_profit_max
        and stop_loss_min <= stop_loss_pct <= stop_loss_max
        and hold_min <= plan.max_hold_candles <= hold_max
    )
    if not within_period_ranges:
        return False

    reward_to_risk_ratio = take_profit_pct / stop_loss_pct
    return reward_to_risk_ratio >= MIN_REWARD_TO_RISK_RATIO


def _fallback_plan(
    period: str,
    current_price: float | None,
) -> TradingPlanOutput | None:
    if current_price is None:
        return None
    fallback = _FALLBACK_PLAN_BY_PERIOD[period]
    return TradingPlanOutput(
        take_profit=round(
            current_price * (1 + fallback["take_profit_pct"]),
            2,
        ),
        stop_loss=round(
            current_price * (1 - fallback["stop_loss_pct"]),
            2,
        ),
        max_hold_candles=fallback["max_hold_candles"],
    )


def recommendation_agent(state: AgentState) -> dict:
    """Combine the three normalized scores and build a trading plan."""
    results = state.get("agent_results") or {}
    period = _normalize_period(
        (state.get("risk_appetite") or {}).get("period")
    )
    scores = _analysis_scores(results)
    weights = _weights_for_state(state, period)
    total_score = _calculate_total_score(period, scores, weights)
    buy = (
        total_score >= SCORE_THRESHOLD
        and _passes_technical_gate(
            state,
            period,
            scores["technical"],
            weights,
        )
    )
    recommendation = localized_text(
        state.get("language"),
        vi="Mua" if buy else "Chờ",
        en="Buy" if buy else "Wait",
    )

    entry_price = 0.0
    take_profit = 0.0
    stop_loss = 0.0
    max_hold_candles = 0

    if buy:
        current_price = _current_price(results)
        if current_price is not None:
            entry_price = round(current_price, 2)
        plan = None
        try:
            candidate = _call_trading_plan_llm(
                state=state,
                period=period,
                total_score=total_score,
                scores=scores,
            )
            if _is_valid_plan(candidate, current_price, period):
                plan = candidate
            else:
                logger.warning(
                    "LLM trading plan violates constraints for period=%s; "
                    "using fallback",
                    period,
                )
        except Exception:
            logger.exception("Recommendation trading-plan generation failed")

        if plan is None:
            plan = _fallback_plan(period, current_price)

        if plan is not None:
            take_profit = round(plan.take_profit, 2)
            stop_loss = round(plan.stop_loss, 2)
            max_hold_candles = plan.max_hold_candles

    output = {
        "score": total_score,
        "buy": buy,
        "recommendation": recommendation,
        "entry_price": entry_price,
        "take_profit": take_profit,
        "stop_loss": stop_loss,
        "max_hold_candles": max_hold_candles,
    }

    print(f"Recommendation Agent output:\n{output}")

    return {
        "agent_results": {
            "recommendation_agent": output,
        },
    }
