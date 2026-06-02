from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd

from .engine import ScoringEngine, SignalGenerator, TradeSimulator, MetricsCalculator
from .pipeline import BacktestPipeline


def walk_forward(
    df: pd.DataFrame,
    pipeline: BacktestPipeline,
    train_window: int = 252,
    test_window: int = 63,
    step: int = 21,
    min_score: int = 3,
    **trade_config: Any,
) -> dict[str, Any]:
    windows: list[dict[str, Any]] = []
    scorer = ScoringEngine()
    signal_gen = SignalGenerator()
    simulator = TradeSimulator(**trade_config)
    metrics_calc = MetricsCalculator()

    start = train_window
    while start + test_window <= len(df):
        test_df = df.iloc[start : start + test_window].copy()
        scored = scorer.score_dataframe(test_df)
        signaled = signal_gen.generate_signals(scored, min_score=min_score)

        signal_dates = pipeline.filter_signal_dates(signaled, min_score=min_score)
        pipeline_results = pipeline.run_pipeline_batch(signal_dates, interval="1d", lookback_days=train_window)
        approved_dates = {
            result.get("date")
            for result in pipeline_results
            if result.get("recommendation") == "Mua"
        }

        date_labels = pd.to_datetime(signaled["datetime"]).dt.strftime("%Y-%m-%d")
        signal_mask = (signaled["signal"] == "BUY") & date_labels.isin(approved_dates)
        signaled.loc[:, "signal"] = None
        signaled.loc[signal_mask, "signal"] = "BUY"

        trades = simulator.run(signaled)
        metrics = metrics_calc.calculate(trades)

        window_info = {
            "window_start": str(pd.to_datetime(test_df.iloc[0]["datetime"])),
            "window_end": str(pd.to_datetime(test_df.iloc[-1]["datetime"])),
            "metrics": metrics,
        }
        windows.append(window_info)

        start += step

    sharpe_values = [w["metrics"]["risk"]["sharpe_ratio"] for w in windows] if windows else []
    total_returns = [w["metrics"]["pnl"]["total_return"] for w in windows] if windows else []
    consistent_wins = float(np.mean([ret > 0 for ret in total_returns])) if total_returns else 0.0

    summary = {
        "n_windows": len(windows),
        "consistent_wins": consistent_wins,
        "avg_sharpe": float(np.mean(sharpe_values)) if sharpe_values else 0.0,
        "std_sharpe": float(np.std(sharpe_values, ddof=1)) if len(sharpe_values) > 1 else 0.0,
    }

    return {"windows": windows, "summary": summary}


def run_benchmarks(
    df: pd.DataFrame,
    pipeline_trades: list[dict[str, Any]],
    engine_trades: list[dict[str, Any]],
    n_random: int = 1000,
    transaction_cost_pct: float = 0.0015,
) -> dict[str, Any]:
    pipeline_entries = {t["entry_date"] for t in pipeline_trades}
    engine_entries = {t["entry_date"] for t in engine_trades}

    agreement_rate = float(len(pipeline_entries & engine_entries) / len(engine_entries)) if engine_entries else 0.0
    cases_filtered_out = len(engine_entries - pipeline_entries)

    pipeline_return = float(np.prod([1 + t["return_pct"] for t in pipeline_trades]) - 1) if pipeline_trades else 0.0
    engine_return = float(np.prod([1 + t["return_pct"] for t in engine_trades]) - 1) if engine_trades else 0.0
    impact_on_returns = pipeline_return - engine_return

    buy_hold_return = float(df.iloc[-1]["close"] / df.iloc[0]["open"] - 1)

    random_returns: list[float] = []
    if n_random > 0 and len(df) > 1:
        indices = np.arange(len(df) - 1)
        trade_count = max(len(pipeline_trades), 1)
        simulator = TradeSimulator(max_hold_candles=20, transaction_cost_pct=transaction_cost_pct)
        for _ in range(n_random):
            sampled = np.random.choice(indices, size=trade_count, replace=False if trade_count <= len(indices) else True)
            random_df = df.copy()
            random_df["signal"] = None
            for idx in sampled:
                random_df.at[random_df.index[idx], "signal"] = "BUY"
            random_trades = simulator.run(random_df)
            total_return = float(np.prod([1 + t["return_pct"] for t in random_trades]) - 1) if random_trades else 0.0
            random_returns.append(total_return)

    percentile_rank = float(np.mean([ret <= pipeline_return for ret in random_returns])) if random_returns else 0.0
    random_p_value = 1 - percentile_rank if random_returns else 1.0

    return {
        "llm_vs_engine": {
            "agreement_rate": agreement_rate,
            "cases_llm_filtered_out": cases_filtered_out,
            "impact_on_returns": impact_on_returns,
        },
        "llm_vs_buy_hold": {
            "pipeline_return": pipeline_return,
            "buy_hold_return": buy_hold_return,
            "delta": pipeline_return - buy_hold_return,
        },
        "llm_vs_random": {
            "percentile_rank": percentile_rank,
            "p_value": random_p_value,
        },
    }


def regime_analysis(
    df: pd.DataFrame,
    market_df: pd.DataFrame,
    pipeline_results: list[dict[str, Any]],
    trade_results: list[dict[str, Any]],
) -> dict[str, Any]:
    market = market_df.copy()
    market["datetime"] = pd.to_datetime(market["datetime"])
    market = market.sort_values("datetime").reset_index(drop=True)
    market["return_60d"] = market["close"].pct_change(60)

    def _regime(value: float) -> str:
        if value > 0.15:
            return "uptrend"
        if value < -0.15:
            return "downtrend"
        return "sideway"

    market["regime"] = market["return_60d"].apply(lambda v: _regime(v) if pd.notna(v) else "sideway")

    regime_map = dict(zip(market["datetime"].dt.strftime("%Y-%m-%d"), market["regime"]))

    regime_metrics: dict[str, Any] = {}
    for regime in ["uptrend", "downtrend", "sideway"]:
        trades = [t for t in trade_results if regime_map.get(str(pd.to_datetime(t["entry_date"]).date())) == regime]
        returns = [t["return_pct"] for t in trades]
        win_rate = float(np.mean([ret > 0 for ret in returns])) if returns else 0.0
        avg_return = float(np.mean(returns)) if returns else 0.0
        regime_metrics[regime] = {
            "win_rate": win_rate,
            "avg_return": avg_return,
            "n_trades": len(trades),
        }

    confidence_distribution: dict[str, dict[str, float]] = {}
    for regime in ["uptrend", "downtrend", "sideway"]:
        labels = [
            r.get("confidence")
            for r in pipeline_results
            if regime_map.get(r.get("date")) == regime
        ]
        total = len(labels)
        confidence_distribution[regime] = {
            "high": float(labels.count("high") / total) if total else 0.0,
            "medium": float(labels.count("medium") / total) if total else 0.0,
            "low": float(labels.count("low") / total) if total else 0.0,
        }

    return {
        "regime_metrics": regime_metrics,
        "confidence_distribution_by_regime": confidence_distribution,
    }


def confidence_calibration(
    pipeline_results: list[dict[str, Any]],
    trade_results: list[dict[str, Any]],
) -> dict[str, Any]:
    confidence_map = {result.get("date"): result.get("confidence") for result in pipeline_results}
    grouped: dict[str, list[float]] = {"high": [], "medium": [], "low": []}

    for trade in trade_results:
        entry_date = str(pd.to_datetime(trade["entry_date"]).date())
        label = trade.get("confidence") or confidence_map.get(entry_date)
        if label in grouped:
            grouped[label].append(trade["return_pct"])

    summary: dict[str, Any] = {}
    for label, returns in grouped.items():
        win_rate = float(np.mean([ret > 0 for ret in returns])) if returns else 0.0
        avg_return = float(np.mean(returns)) if returns else 0.0
        summary[label] = {
            "win_rate": win_rate,
            "avg_return": avg_return,
            "n_trades": len(returns),
        }

    confidence_numeric = []
    return_values = []
    mapping = {"high": 3, "medium": 2, "low": 1}
    for label, returns in grouped.items():
        for ret in returns:
            confidence_numeric.append(mapping[label])
            return_values.append(ret)

    correlation = 0.0
    if len(return_values) >= 2:
        conf_std = float(np.std(confidence_numeric))
        ret_std = float(np.std(return_values))
        if conf_std > 0 and ret_std > 0:
            correlation = float(np.corrcoef(confidence_numeric, return_values)[0, 1])

    interpretation = (
        f"high confidence trades co win_rate {summary['high']['win_rate']:.2%} "
        f"vs low confidence {summary['low']['win_rate']:.2%}"
    )

    return {
        "confidence_summary": summary,
        "confidence_accuracy": correlation,
        "interpretation": interpretation,
    }
