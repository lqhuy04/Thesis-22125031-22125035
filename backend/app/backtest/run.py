from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd

from agentic_ai.analyze.nodes.technical_analysis import technical_analysis_agent
from agentic_ai.analyze.state import AgentState

from .engine import IndicatorEngine, ScoringEngine, SignalGenerator, TradeSimulator, MetricsCalculator
from .pipeline import BacktestPipeline
from .experiments import walk_forward, run_benchmarks, regime_analysis, confidence_calibration
from .stats import ttest_returns, permutation_test, confidence_vs_outcome_test
from .validate import run_parity_suite


def _build_state(symbol: str, from_date: str, to_date: str) -> AgentState:
    return {
        "mode": "auto",
        "user_input": "Backtest parity check",
        "risk_appetite": {},
        "symbol": symbol,
        "plan": {
            "technical_analysis_agent": {
                "interval": "1d",
                "from_date": from_date,
                "to_date": to_date,
            }
        },
        "agent_results": {},
        "final_output": None,
        "error": None,
    }


def run_full_backtest(
    df_1d: pd.DataFrame,
    df_1m: pd.DataFrame,
    market_df: pd.DataFrame,
    symbol: str,
    stop_loss_pct: float = 0.05,
    take_profit_pct: float = 0.10,
    max_hold_candles: int = 20,
    exit_on_score_drop: bool = False,
) -> dict[str, Any]:
    indicator_engine = IndicatorEngine()
    scoring_engine = ScoringEngine()
    signal_generator = SignalGenerator()
    trade_config = {
        "stop_loss_pct": stop_loss_pct,
        "take_profit_pct": take_profit_pct,
        "max_hold_candles": max_hold_candles,
        "exit_on_score_drop": exit_on_score_drop,
    }

    if len(df_1d) <= 50:
        raise ValueError("Insufficient data: need more than 50 candles for parity check")

    scored_1d_for_parity = scoring_engine.score_dataframe(indicator_engine.add_indicators(df_1d))

    sample_count = min(10, len(df_1d) - 50)
    sample_indices = np.linspace(50, len(df_1d) - 1, num=sample_count, dtype=int)
    live_outputs: list[dict[str, Any]] = []
    for idx in sample_indices:
        date_str = pd.to_datetime(df_1d.iloc[idx]["datetime"]).strftime("%Y-%m-%d")
        from_date = (pd.to_datetime(date_str) - pd.Timedelta(days=200)).strftime("%Y-%m-%d")
        state = _build_state(symbol, from_date, date_str)
        output = technical_analysis_agent(state)
        live_outputs.append({
            "candle_index": idx,
            "live_output": output.get("agent_results", {}).get("technical_analysis_agent", {}),
        })

    parity_report = run_parity_suite(live_outputs, scored_1d_for_parity)
    if parity_report["pass_rate"] < 1.0:
        raise ValueError("Parity check failed: scoring parity < 100%")

    scored_1d = scoring_engine.score_dataframe(indicator_engine.add_indicators(df_1d))
    scored_1m = scoring_engine.score_dataframe(indicator_engine.add_indicators(df_1m))

    pipeline = BacktestPipeline(symbol, trade_config)
    signal_dates_1d = pipeline.filter_signal_dates(scored_1d)

    print(f"Goi LLM cho {len(signal_dates_1d)} signal dates tren 1d...")
    pipeline_results = pipeline.run_pipeline_batch(signal_dates_1d, interval="1d", lookback_days=252)

    approved_dates = {
        result.get("date")
        for result in pipeline_results
        if result.get("recommendation") == "Mua"
    }
    confidence_map = {result.get("date"): result.get("confidence") for result in pipeline_results}

    signaled_full = signal_generator.generate_signals(scored_1d)
    date_labels = pd.to_datetime(signaled_full["datetime"]).dt.strftime("%Y-%m-%d")
    allowed_mask = (signaled_full["signal"] == "BUY") & date_labels.isin(approved_dates)
    signaled_full.loc[:, "signal"] = None
    signaled_full.loc[allowed_mask, "signal"] = "BUY"
    signaled_full["confidence"] = date_labels.map(confidence_map)

    simulator = TradeSimulator(**trade_config)
    full_trades = simulator.run(signaled_full)

    signaled_engine = signal_generator.generate_signals(scored_1d)
    engine_trades = simulator.run(signaled_engine)

    metrics_calc = MetricsCalculator()
    full_metrics = metrics_calc.calculate(full_trades)
    engine_metrics = metrics_calc.calculate(engine_trades)

    walk_forward_results = walk_forward(scored_1d, pipeline, **trade_config)
    benchmark_results = run_benchmarks(scored_1d, full_trades, engine_trades)
    regime_results = regime_analysis(scored_1d, market_df, pipeline_results, full_trades)
    confidence_results = confidence_calibration(pipeline_results, full_trades)

    returns = [t["return_pct"] for t in full_trades]
    stats_results = {
        "ttest": ttest_returns(returns),
        "permutation": permutation_test(returns),
        "confidence_vs_outcome": confidence_vs_outcome_test(
            [t.get("confidence", "") for t in full_trades],
            returns,
        ),
    }

    def _pct(value: float) -> str:
        return f"{value * 100:.1f}%"

    print("=" * 50)
    print(f"BACKTEST RESULTS — {symbol}")
    print("=" * 50)
    print("\n[FULL PIPELINE — LLM + Technical + Article + Fundamental]")
    print(f"Signal dates found:    {len(signal_dates_1d)}")
    print(f"LLM calls made:        {len(pipeline_results)}")
    print(f"Trades executed:       {full_metrics['volume']['n_trades']}")
    print(f"Win Rate:              {_pct(full_metrics['volume']['win_rate'])}")
    print(f"Total Return:          {_pct(full_metrics['pnl']['total_return'])}")
    print(f"Sharpe Ratio:          {full_metrics['risk']['sharpe_ratio']:.2f}")
    print(f"Max Drawdown:         {_pct(full_metrics['risk']['max_drawdown'])}")
    print(f"vs Random:             top {_pct(benchmark_results['llm_vs_random']['percentile_rank'])} (p={benchmark_results['llm_vs_random']['p_value']:.2f})")

    print("\n[ABLATION — Technical Only, khong LLM]")
    print(f"Trades executed:       {engine_metrics['volume']['n_trades']}")
    print(f"Win Rate:              {_pct(engine_metrics['volume']['win_rate'])}")
    print(f"Total Return:          {_pct(engine_metrics['pnl']['total_return'])}")
    print(f"LLM contribution:      {_pct(full_metrics['pnl']['total_return'] - engine_metrics['pnl']['total_return'])} return, {_pct(full_metrics['volume']['win_rate'] - engine_metrics['volume']['win_rate'])} win_rate")

    print("\n[CONFIDENCE CALIBRATION]")
    print(
        f"High confidence:       win={_pct(confidence_results['confidence_summary']['high']['win_rate'])}, "
        f"avg_ret={_pct(confidence_results['confidence_summary']['high']['avg_return'])} (n={confidence_results['confidence_summary']['high']['n_trades']})"
    )
    print(
        f"Medium confidence:     win={_pct(confidence_results['confidence_summary']['medium']['win_rate'])}, "
        f"avg_ret={_pct(confidence_results['confidence_summary']['medium']['avg_return'])} (n={confidence_results['confidence_summary']['medium']['n_trades']})"
    )
    print(
        f"Low confidence:        win={_pct(confidence_results['confidence_summary']['low']['win_rate'])}, "
        f"avg_ret={_pct(confidence_results['confidence_summary']['low']['avg_return'])} (n={confidence_results['confidence_summary']['low']['n_trades']})"
    )
    print(
        f"ANOVA p-value:         {stats_results['confidence_vs_outcome']['p_value']:.3f} "
        f"(significant: {'yes' if stats_results['confidence_vs_outcome']['significant'] else 'no'})"
    )

    print("\n[WALK-FORWARD — 1D]")
    print(f"Windows tested:        {walk_forward_results['summary']['n_windows']}")
    print(
        f"Consistent wins:       {_pct(walk_forward_results['summary']['consistent_wins'])}"
    )
    print(
        f"Avg Sharpe:            {walk_forward_results['summary']['avg_sharpe']:.2f} "
        f"± {walk_forward_results['summary']['std_sharpe']:.2f}"
    )

    print("\n[REGIME ANALYSIS]")
    for regime, metrics in regime_results["regime_metrics"].items():
        conf_high = regime_results["confidence_distribution_by_regime"][regime]["high"]
        print(
            f"{regime.capitalize()}: win={_pct(metrics['win_rate'])}, "
            f"avg_ret={_pct(metrics['avg_return'])}, confidence_high={_pct(conf_high)}"
        )

    print("=" * 50)

    return {
        "parity_report": parity_report,
        "scored_1d": scored_1d,
        "scored_1m": scored_1m,
        "pipeline_results": pipeline_results,
        "full_trades": full_trades,
        "engine_trades": engine_trades,
        "full_metrics": full_metrics,
        "engine_metrics": engine_metrics,
        "walk_forward": walk_forward_results,
        "benchmarks": benchmark_results,
        "regime": regime_results,
        "confidence": confidence_results,
        "stats": stats_results,
    }
