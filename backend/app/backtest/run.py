from __future__ import annotations

from typing import Any
import logging
import math
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

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
                "use_current_price": False,
                "indicator_source": "backtest",
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
    max_hold_candles: int = 20,
    min_signal_score: int = 3,
    exit_on_score_drop: bool = False,
    transaction_cost_pct: float = 0.0015,
    mode: str = "auto",
    data_selection: dict | None = None,
) -> dict[str, Any]:
    indicator_engine = IndicatorEngine()
    scoring_engine = ScoringEngine()
    signal_generator = SignalGenerator()
    trade_config = {
        "max_hold_candles": max_hold_candles,
        "exit_on_score_drop": exit_on_score_drop,
        "transaction_cost_pct": transaction_cost_pct,
    }

    if len(df_1d) <= 50:
        raise ValueError("Insufficient data: need more than 50 candles for parity check")

    scored_1d_for_parity = scoring_engine.score_dataframe(indicator_engine.add_indicators(df_1d))

    sample_count = min(10, len(df_1d) - 50)
    sample_indices = np.linspace(50, len(df_1d) - 1, num=sample_count, dtype=int)
    parity_start = pd.to_datetime(df_1d["datetime"].min()).strftime("%Y-%m-%d")
    live_outputs: list[dict[str, Any]] = []
    for idx in sample_indices:
        date_str = pd.to_datetime(df_1d.iloc[idx]["datetime"]).strftime("%Y-%m-%d")
        state = _build_state(symbol, parity_start, date_str)
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

    pipeline = BacktestPipeline(symbol, trade_config, mode=mode, data_selection=data_selection)
    signal_dates_1d = pipeline.filter_signal_dates(scored_1d, min_score=min_signal_score)

    print(f"Goi LLM cho {len(signal_dates_1d)} signal dates tren 1d...")
    pipeline_results = pipeline.run_pipeline_batch(signal_dates_1d, interval="1d", lookback_days=252)

    approved_dates = {
        result.get("date")
        for result in pipeline_results
        if result.get("recommendation") == "Mua"
    }
    confidence_map = {result.get("date"): result.get("confidence") for result in pipeline_results}
    entry_price_map = {result.get("date"): result.get("entry_price") for result in pipeline_results}
    take_profit_map = {result.get("date"): result.get("take_profit_price") for result in pipeline_results}
    stop_loss_map = {result.get("date"): result.get("stop_loss_price") for result in pipeline_results}
    max_hold_map = {result.get("date"): result.get("max_hold_candles") for result in pipeline_results}

    signaled_full = signal_generator.generate_signals(scored_1d, min_score=min_signal_score)
    date_labels = pd.to_datetime(signaled_full["datetime"]).dt.strftime("%Y-%m-%d")
    allowed_mask = (signaled_full["signal"] == "BUY") & date_labels.isin(approved_dates)
    signaled_full.loc[:, "signal"] = None
    signaled_full.loc[allowed_mask, "signal"] = "BUY"
    signaled_full["confidence"] = date_labels.map(confidence_map)
    signaled_full["entry_price_override"] = date_labels.map(entry_price_map)
    signaled_full["take_profit_price"] = date_labels.map(take_profit_map)
    signaled_full["stop_loss_price"] = date_labels.map(stop_loss_map)
    signaled_full["max_hold_candles_override"] = date_labels.map(max_hold_map)

    simulator = TradeSimulator(**trade_config)
    full_trades = simulator.run(signaled_full)

    signaled_engine = signal_generator.generate_signals(scored_1d, min_score=min_signal_score)
    engine_trades = simulator.run(signaled_engine)

    metrics_calc = MetricsCalculator()
    full_metrics = metrics_calc.calculate(full_trades)
    engine_metrics = metrics_calc.calculate(engine_trades)

    walk_forward_results = walk_forward(
        scored_1d,
        pipeline,
        interval="1d",
        min_score=min_signal_score,
        **trade_config,
    )
    benchmark_results = run_benchmarks(scored_1d, full_trades, engine_trades, transaction_cost_pct=transaction_cost_pct)
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

    def _sanitize_json(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: _sanitize_json(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_sanitize_json(v) for v in value]
        if isinstance(value, (np.floating, float)):
            number = float(value)
            return number if math.isfinite(number) else None
        if isinstance(value, (np.integer, int)):
            return int(value)
        return value

    print("=" * 50)
    print(f"BACKTEST RESULTS — {symbol}")
    print("=" * 50)
    print(f"\n[FULL PIPELINE — LLM + Technical + Article + Fundamental]")
    print(f"Transaction cost:      {transaction_cost_pct*100:.2f}% per side ({transaction_cost_pct*2*100:.2f}% round-trip)")
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

    # Save visualization
    visualization_file = None
    visualization_data = None
    try:
        import os
        from .visualizer import generate_backtest_json, get_backtest_visualization_data
        current_dir = os.path.dirname(os.path.abspath(__file__))
        visualizations_dir = os.path.join(current_dir, "visualizations")
        timestamp_str = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        
        json_output_filename = f"{symbol}_{timestamp_str}_backtest.json"
        json_output_path = os.path.join(visualizations_dir, json_output_filename)
        generate_backtest_json(
            df=scored_1d,
            trades=full_trades,
            metrics=full_metrics,
            symbol=symbol,
            output_path=json_output_path,
            engine_trades=engine_trades,
            engine_metrics=engine_metrics,
            pipeline_results=pipeline_results,
        )

        visualization_file = f"/visualizations/{json_output_filename}"
        visualization_data = get_backtest_visualization_data(
            df=scored_1d,
            trades=full_trades,
            metrics=full_metrics,
            symbol=symbol,
            engine_trades=engine_trades,
            engine_metrics=engine_metrics,
            pipeline_results=pipeline_results,
        )
        print(f"Visualization JSON file created: {json_output_path}")

        # Upload to Supabase Storage
        json_supabase_url = None
        try:
            from app.utils.supabase_storage import upload_backtest_file
            logger.info("Uploading JSON visualization to Supabase Storage...")
            json_supabase_url = upload_backtest_file(json_output_path, json_output_filename, "application/json")
        except Exception as upload_err:
            print(f"Failed to upload to Supabase Storage: {upload_err}")
    except Exception as e:
        print(f"Failed to generate visualization files: {e}")
        json_supabase_url = None

    # Aggregate VN30 stats vào MỘT file JSON local (upsert theo symbol).
    vn30_stats_file = None
    try:
        import os
        from .vn30_stats import build_symbol_stats, update_vn30_stats_file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        vn30_stats_path = os.path.join(current_dir, "reports", "vn30_stats.json")
        symbol_stats = build_symbol_stats(
            symbol=symbol,
            full_metrics=full_metrics,
            engine_metrics=engine_metrics,
            benchmarks=benchmark_results,
            walk_forward=walk_forward_results,
            regime=regime_results,
            confidence=confidence_results,
            stats=stats_results,
            full_trades=full_trades,
        )
        update_vn30_stats_file(symbol, symbol_stats, vn30_stats_path)
        vn30_stats_file = vn30_stats_path
        print(f"VN30 aggregate stats updated: {vn30_stats_path}")
    except Exception as e:
        print(f"Failed to update VN30 aggregate stats: {e}")

    result = {
        "parity_report": parity_report,
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
        "visualization_file": visualization_file,
        "visualization_data": visualization_data,
        "visualization_data_url": json_supabase_url,
        "vn30_stats_file": vn30_stats_file,
    }

    return _sanitize_json(result)
