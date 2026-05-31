from __future__ import annotations

from typing import Any
import numpy as np
from scipy import stats


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
    confidence_labels: list[str],
    returns: list[float],
) -> dict[str, Any]:
    data = {"high": [], "medium": [], "low": []}
    for label, ret in zip(confidence_labels, returns):
        if label in data:
            data[label].append(ret)

    if any(len(values) == 0 for values in data.values()):
        return {
            "f_stat": 0.0,
            "p_value": 1.0,
            "significant": False,
            "group_means": {k: float(np.mean(v)) if v else 0.0 for k, v in data.items()},
        }

    f_stat, p_value = stats.f_oneway(data["high"], data["medium"], data["low"])

    return {
        "f_stat": float(f_stat),
        "p_value": float(p_value),
        "significant": bool(p_value < 0.05),
        "group_means": {k: float(np.mean(v)) for k, v in data.items()},
    }
