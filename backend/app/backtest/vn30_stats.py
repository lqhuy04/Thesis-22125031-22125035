"""
vn30_stats.py
Tổng hợp kết quả thống kê backtest cho rổ VN30 vào MỘT file JSON local.

Bối cảnh: admin dashboard chạy cả rổ bằng cách gọi /api/agentic/backtest tuần tự
cho từng mã (30 request độc lập). Backend không biết một lần gọi thuộc "batch VN30",
nên mỗi lần run_full_backtest chạy xong sẽ UPSERT thống kê của mã đó vào file dùng
chung (key = symbol), rồi tính lại phần tổng hợp (aggregate) + so sánh với baseline
engine-only của các mã hiện có trong file.

File mặc định: backend/app/backtest/reports/vn30_stats.json
"""

from __future__ import annotations

import json
import math
import os
from typing import Any

import numpy as np

from .stats import information_coefficient


def _f(value: Any, default: float = 0.0) -> float:
    """Ép về float hữu hạn (loại NaN/Inf) để JSON hợp lệ."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def build_symbol_stats(
    symbol: str,
    full_metrics: dict[str, Any],
    engine_metrics: dict[str, Any],
    benchmarks: dict[str, Any],
    regime: dict[str, Any],
    confidence: dict[str, Any],
    stats: dict[str, Any],
    full_trades: list[dict[str, Any]],
) -> dict[str, Any]:
    """Rút gọn output của run_full_backtest thành thống kê cho một mã."""

    vol = full_metrics.get("volume", {})
    pnl = full_metrics.get("pnl", {})
    risk = full_metrics.get("risk", {})

    # 1. Hiệu suất (full pipeline)
    performance = {
        "n_trades": int(vol.get("n_trades", 0)),
        "win_rate": _f(vol.get("win_rate")),
        "total_return": _f(pnl.get("total_return")),
        "avg_return": _f(pnl.get("avg_return")),
        "annualized_return": _f(pnl.get("annualized_return")),
        "max_drawdown": _f(risk.get("max_drawdown")),
        "sharpe_ratio": _f(risk.get("sharpe_ratio")),
        "profit_factor": _f(risk.get("profit_factor")),
    }

    # Hiệu suất baseline engine-only (technical, không LLM) — để so sánh.
    e_vol = engine_metrics.get("volume", {})
    e_pnl = engine_metrics.get("pnl", {})
    e_risk = engine_metrics.get("risk", {})
    baseline_engine_performance = {
        "n_trades": int(e_vol.get("n_trades", 0)),
        "win_rate": _f(e_vol.get("win_rate")),
        "total_return": _f(e_pnl.get("total_return")),
        "avg_return": _f(e_pnl.get("avg_return")),
        "annualized_return": _f(e_pnl.get("annualized_return")),
        "max_drawdown": _f(e_risk.get("max_drawdown")),
        "sharpe_ratio": _f(e_risk.get("sharpe_ratio")),
        "profit_factor": _f(e_risk.get("profit_factor")),
    }

    # 2. Benchmark
    vs_bh = benchmarks.get("llm_vs_buy_hold", {})
    vs_engine = benchmarks.get("llm_vs_engine", {})
    benchmark = {
        "pipeline_return": _f(vs_bh.get("pipeline_return")),
        "buy_hold_return": _f(vs_bh.get("buy_hold_return")),
        "delta_vs_buy_hold": _f(vs_bh.get("delta")),
        "impact_on_returns": _f(vs_engine.get("impact_on_returns")),
        "agreement_rate": _f(vs_engine.get("agreement_rate")),
        "cases_llm_filtered_out": int(vs_engine.get("cases_llm_filtered_out", 0)),
    }

    # 3. Kiểm định thống kê
    ttest = stats.get("ttest", {})
    permutation = stats.get("permutation", {})
    anova = stats.get("confidence_vs_outcome", {})

    # Information Coefficient (ic, p_value): tương quan điểm kỹ thuật lúc vào lệnh
    # với return thực tế. Tính từ full_trades vì run.py không trả sẵn p_value.
    scores = [t.get("total_score_at_entry") for t in full_trades if t.get("total_score_at_entry") is not None]
    returns_for_ic = [t.get("return_pct") for t in full_trades if t.get("total_score_at_entry") is not None]
    ic_result = information_coefficient(scores, returns_for_ic)

    group_means = anova.get("group_means", {}) or {}
    statistical_tests = {
        "ttest": {
            "t_stat": _f(ttest.get("t_stat")),
            "p_value": _f(ttest.get("p_value"), default=1.0),
            "significant": bool(ttest.get("significant", False)),
        },
        "permutation": {
            "p_value": _f(permutation.get("p_value"), default=1.0),
            "percentile_rank": _f(permutation.get("percentile_rank")),
            "significant": bool(permutation.get("significant", False)),
        },
        "information_coefficient": {
            "ic": _f(ic_result.get("ic")),
            "p_value": _f(ic_result.get("p_value"), default=1.0),
            "interpretation": ic_result.get("interpretation", ""),
        },
        "confidence_vs_outcome_anova": {
            "f_stat": _f(anova.get("f_stat")),
            "p_value": _f(anova.get("p_value"), default=1.0),
            "significant": bool(anova.get("significant", False)),
            "group_means": {
                "high": _f(group_means.get("high")),
                "medium": _f(group_means.get("medium")),
                "low": _f(group_means.get("low")),
            },
        },
    }

    # 4. Regime analysis
    regime_metrics = regime.get("regime_metrics", {})
    regime_out: dict[str, Any] = {}
    for name in ["uptrend", "downtrend", "sideway"]:
        m = regime_metrics.get(name, {})
        regime_out[name] = {
            "win_rate": _f(m.get("win_rate")),
            "avg_return": _f(m.get("avg_return")),
            "n_trades": int(m.get("n_trades", 0)),
        }

    # 5. Confidence calibration
    conf_summary = confidence.get("confidence_summary", {})
    confidence_out: dict[str, Any] = {}
    for tier in ["high", "medium", "low"]:
        m = conf_summary.get(tier, {})
        confidence_out[tier] = {
            "win_rate": _f(m.get("win_rate")),
            "avg_return": _f(m.get("avg_return")),
            "n_trades": int(m.get("n_trades", 0)),
        }

    return {
        "performance": performance,
        "baseline_engine_performance": baseline_engine_performance,
        "benchmark": benchmark,
        "statistical_tests": statistical_tests,
        "regime": regime_out,
        "confidence_calibration": confidence_out,
    }


def _compute_aggregate(symbols: dict[str, Any]) -> dict[str, Any]:
    """Tổng hợp profit toàn rổ và so sánh pipeline vs baseline engine-only."""
    pipeline_perfs = [s["performance"] for s in symbols.values() if "performance" in s]
    engine_perfs = [s["baseline_engine_performance"] for s in symbols.values() if "baseline_engine_performance" in s]

    def _summary(perfs: list[dict[str, Any]]) -> dict[str, Any]:
        if not perfs:
            return {
                "mean_total_return": 0.0,
                "median_total_return": 0.0,
                "compounded_return": 0.0,
                "mean_win_rate": 0.0,
                "mean_sharpe": 0.0,
                "mean_max_drawdown": 0.0,
                "total_trades": 0,
                "profitable_symbols": 0,
            }
        total_returns = [p["total_return"] for p in perfs]
        # compounded_return: lợi nhuận danh mục cân bằng (equal-weight), gộp các mã.
        compounded = float(np.prod([1 + r for r in total_returns]) ** (1 / len(total_returns)) - 1)
        return {
            "mean_total_return": float(np.mean(total_returns)),
            "median_total_return": float(np.median(total_returns)),
            "compounded_return": compounded,
            "mean_win_rate": float(np.mean([p["win_rate"] for p in perfs])),
            "mean_sharpe": float(np.mean([p["sharpe_ratio"] for p in perfs])),
            "mean_max_drawdown": float(np.mean([p["max_drawdown"] for p in perfs])),
            "total_trades": int(sum(p["n_trades"] for p in perfs)),
            "profitable_symbols": int(sum(1 for r in total_returns if r > 0)),
        }

    pipeline_summary = _summary(pipeline_perfs)
    engine_summary = _summary(engine_perfs)

    symbols_pipeline_beats_engine = sum(
        1
        for s in symbols.values()
        if "performance" in s and "baseline_engine_performance" in s
        and s["performance"]["total_return"] > s["baseline_engine_performance"]["total_return"]
    )

    return {
        "pipeline": pipeline_summary,
        "baseline_engine": engine_summary,
        "comparison": {
            "delta_mean_total_return": pipeline_summary["mean_total_return"] - engine_summary["mean_total_return"],
            "delta_compounded_return": pipeline_summary["compounded_return"] - engine_summary["compounded_return"],
            "delta_mean_win_rate": pipeline_summary["mean_win_rate"] - engine_summary["mean_win_rate"],
            "delta_mean_sharpe": pipeline_summary["mean_sharpe"] - engine_summary["mean_sharpe"],
            "symbols_pipeline_beats_engine": symbols_pipeline_beats_engine,
        },
    }


def update_vn30_stats_file(
    symbol: str,
    symbol_stats: dict[str, Any],
    output_path: str,
    allowed_symbols: list[str] | None = None,
) -> str:
    """
    Upsert thống kê của 1 mã vào file JSON tổng hợp rồi tính lại aggregate.
    Trả về đường dẫn file đã ghi.
    """
    import pandas as pd

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    report: dict[str, Any] = {"symbols": {}}
    if os.path.exists(output_path):
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict) and isinstance(loaded.get("symbols"), dict):
                report = loaded
        except (json.JSONDecodeError, OSError):
            report = {"symbols": {}}

    # Remove symbols that are no longer in the current VN30 universe before
    # recalculating the aggregate. This prevents an older constituent from
    # surviving indefinitely when a later batch runs only the current basket.
    allowed = {item.upper() for item in allowed_symbols} if allowed_symbols is not None else None
    if allowed is not None:
        report["symbols"] = {
            existing_symbol: entry
            for existing_symbol, entry in report["symbols"].items()
            if existing_symbol.upper() in allowed
        }

    # Remove the retired walk-forward section from legacy aggregate files.
    for existing_entry in report["symbols"].values():
        if isinstance(existing_entry, dict):
            existing_entry.pop("walk_forward", None)

    now = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    symbol_entry = dict(symbol_stats)
    symbol_entry["updated_at"] = now
    normalized_symbol = symbol.upper()
    if allowed is None or normalized_symbol in allowed:
        report["symbols"][normalized_symbol] = symbol_entry

    report["aggregate"] = _compute_aggregate(report["symbols"])
    report["n_symbols"] = len(report["symbols"])
    report["generated_at"] = now

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return output_path
