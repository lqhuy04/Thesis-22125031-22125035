from __future__ import annotations

from typing import Any
import math
import numpy as np
from scipy import stats


def confidence_tier(value: Any) -> str | None:
    """Map a confidence score to a tier label (``high``/``medium``/``low``).

    The pipeline emits ``confidence`` as a numeric score in [0, 1] (computed
    deterministically by the aggregator, buy gate = 0.55), so calibration must
    *bin* it rather than match string labels. An already-tiered string is passed
    through unchanged. Thresholds are aligned with the 0.55 buy gate:
    ``>= 0.70`` high, ``>= 0.55`` medium, otherwise low. Returns ``None`` for
    missing/unparseable values so callers can skip them.
    """
    if value is None:
        return None
    if isinstance(value, str):
        label = value.strip().lower()
        return label if label in ("high", "medium", "low") else None
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(score):
        return None
    if score >= 0.70:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def ttest_returns(returns: list[float]) -> dict[str, Any]:
    values = np.array(returns, dtype=float)
    if len(values) == 0:
        return {"t_stat": 0.0, "p_value": 1.0, "significant": False, "confidence_level": ""}

    t_stat, p_value = stats.ttest_1samp(values, popmean=0.0, nan_policy="omit")
    return {
        "t_stat": float(t_stat),
        "p_value": float(p_value),
        "significant": bool(p_value < 0.05),
        "confidence_level": "95%",
    }


def permutation_test(actual_returns: list[float], n_permutations: int = 1000) -> dict[str, Any]:
    values = np.array(actual_returns, dtype=float)
    if len(values) == 0:
        return {"percentile_rank": 0.0, "p_value": 1.0, "significant": False}

    actual_mean = float(np.mean(values))
    permutations = []
    for _ in range(n_permutations):
        signs = np.random.choice([-1, 1], size=len(values))
        perm_mean = float(np.mean(values * signs))
        permutations.append(perm_mean)

    permutations = np.array(permutations)
    percentile_rank = float(np.mean(permutations <= actual_mean))
    p_value = float(np.mean(np.abs(permutations) >= abs(actual_mean)))

    return {
        "percentile_rank": percentile_rank,
        "p_value": p_value,
        "significant": bool(p_value < 0.05),
    }


def information_coefficient(scores: list[float], forward_returns: list[float]) -> dict[str, Any]:
    values = np.array(scores, dtype=float)
    returns = np.array(forward_returns, dtype=float)
    if len(values) < 2 or len(returns) < 2:
        return {"ic": 0.0, "p_value": 1.0, "interpretation": "insufficient_data"}

    ic, p_value = stats.pearsonr(values, returns)
    interpretation = "positive" if ic > 0 else "negative" if ic < 0 else "flat"
    return {
        "ic": float(ic),
        "p_value": float(p_value),
        "interpretation": interpretation,
    }


def confidence_vs_outcome_test(
    confidence_values: list[Any],
    returns: list[float],
) -> dict[str, Any]:
    # confidence_values may be numeric scores (the pipeline default) or tier
    # strings — confidence_tier normalizes both into high/medium/low buckets.
    data = {"high": [], "medium": [], "low": []}
    for value, ret in zip(confidence_values, returns):
        tier = confidence_tier(value)
        if tier in data:
            data[tier].append(ret)

    group_means = {k: float(np.mean(v)) if v else 0.0 for k, v in data.items()}

    # Run the ANOVA over whatever tiers actually have data. Since only approved
    # "Mua" trades are scored, the "low" bucket is often empty; comparing the
    # populated tiers (e.g. medium vs high) is still the meaningful test.
    testable = [v for v in data.values() if len(v) >= 2]
    if len(testable) < 2:
        return {
            "f_stat": 0.0,
            "p_value": 1.0,
            "significant": False,
            "group_means": group_means,
        }

    f_stat, p_value = stats.f_oneway(*testable)

    return {
        "f_stat": float(f_stat),
        "p_value": float(p_value),
        "significant": bool(p_value < 0.05),
        "group_means": group_means,
    }
