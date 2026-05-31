from __future__ import annotations

from typing import Any
import pandas as pd


def validate_scoring_parity(live_output: dict[str, Any], df_scored: pd.DataFrame, candle_index: int) -> dict[str, Any]:
    diffs: list[str] = []

    indicators = live_output.get("indicators", {})
    expected_scores = {
        "rsi_score": indicators.get("rsi", {}).get("score"),
        "ma_score": indicators.get("ma", {}).get("score"),
        "boll_score": indicators.get("boll", {}).get("score"),
        "macd_score": indicators.get("macd", {}).get("score"),
        "kdj_score": indicators.get("kdj", {}).get("score"),
        "total_score": live_output.get("total_score"),
    }

    for key, expected in expected_scores.items():
        actual = df_scored.iloc[candle_index].get(key)
        if pd.isna(actual) and expected is None:
            continue
        if expected is None or actual is None or float(actual) != float(expected):
            diffs.append(f"{key}: expected={expected}, actual={actual}")

    return {"match": len(diffs) == 0, "diffs": diffs}


def validate_pipeline_consistency(
    pipeline_result: dict[str, Any],
    direct_agent_result: dict[str, Any],
) -> dict[str, Any]:
    recommendation_match = pipeline_result.get("recommendation") == direct_agent_result.get("recommendation")
    confidence_match = pipeline_result.get("confidence") == direct_agent_result.get("confidence")

    return {
        "match": recommendation_match and confidence_match,
        "recommendation_match": recommendation_match,
        "confidence_match": confidence_match,
    }


def run_parity_suite(live_outputs: list[dict[str, Any]], df: pd.DataFrame) -> dict[str, Any]:
    pass_count = 0
    results: list[dict[str, Any]] = []

    for item in live_outputs:
        candle_index = item.get("candle_index")
        live_output = item.get("live_output")
        if candle_index is None or live_output is None:
            results.append({"match": False, "diffs": ["missing_input"]})
            continue

        parity = validate_scoring_parity(live_output, df, candle_index)
        results.append(parity)
        if parity["match"]:
            pass_count += 1

    pass_rate = float(pass_count / len(results)) if results else 0.0

    return {
        "pass_rate": pass_rate,
        "results": results,
    }
