"""
Run 5 separate VN30 backtests, one per technical indicator (RSI, MACD, KDJ,
Bollinger Bands, MA Crossover), engine-only (no LLM).

Reuses the existing scoring/signal/trade engine from app.backtest.engine —
each run isolates a single indicator's 0/1 score column as the signal source
instead of the combined total_score used by the LLM pipeline.

Usage (from backend/):
    python -m app.backtest.single_indicator_backtest
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from app.backtest.engine import (
    DEFAULT_TRANSACTION_COST_PCT,
    IndicatorEngine,
    MetricsCalculator,
    ScoringEngine,
    SignalGenerator,
    TradeSimulator,
)
from app.services.backtest_pipeline_service import _build_dataframe
from app.utils.market_index import get_index_symbols

START_DATE = "2023-01-01"
END_DATE = "2025-12-31"
MAX_HOLD_CANDLES = 20

INDICATORS = {
    "RSI": "rsi_score",
    "MACD": "macd_score",
    "KDJ": "kdj_score",
    "Bollinger Bands": "boll_score",
    "MA Crossover": "ma_score",
}


def _sanitize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _sanitize_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_json(v) for v in value]
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if np.isfinite(number) else None
    if isinstance(value, (np.integer, int)):
        return int(value)
    return value


def _backtest_symbol_for_indicator(df_1d: pd.DataFrame, score_column: str) -> dict[str, Any]:
    indicator_engine = IndicatorEngine()
    scoring_engine = ScoringEngine()
    signal_generator = SignalGenerator()
    simulator = TradeSimulator(
        max_hold_candles=MAX_HOLD_CANDLES,
        transaction_cost_pct=DEFAULT_TRANSACTION_COST_PCT,
    )
    metrics_calc = MetricsCalculator()

    scored = scoring_engine.score_dataframe(indicator_engine.add_indicators(df_1d))
    scored["total_score"] = scored[score_column]

    signaled = signal_generator.generate_signals(scored, min_score=1)
    trades = simulator.run(signaled)
    metrics = metrics_calc.calculate(trades)
    return {"trades": trades, "metrics": metrics}


def _safe_mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else 0.0


def _safe_median(values: list[float]) -> float:
    return float(np.median(values)) if values else 0.0


def _aggregate_metrics(per_symbol: dict[str, Any]) -> dict[str, Any]:
    win_rates, total_returns, sharpe_ratios, max_drawdowns, n_trades_list = [], [], [], [], []
    all_trades: list[dict[str, Any]] = []

    for result in per_symbol.values():
        m = result["metrics"]
        n_trades_list.append(m["volume"]["n_trades"])
        if m["volume"]["n_trades"] > 0:
            win_rates.append(m["volume"]["win_rate"])
            total_returns.append(m["pnl"]["total_return"])
            sharpe_ratios.append(m["risk"]["sharpe_ratio"])
            max_drawdowns.append(m["risk"]["max_drawdown"])
        all_trades.extend(result["trades"])

    return {
        "n_symbols_with_trades": len(win_rates),
        "total_trades_all_symbols": sum(n_trades_list),
        "avg_trades_per_symbol": _safe_mean(n_trades_list),
        "mean_win_rate": _safe_mean(win_rates),
        "median_win_rate": _safe_median(win_rates),
        "mean_total_return": _safe_mean(total_returns),
        "median_total_return": _safe_median(total_returns),
        "mean_sharpe_ratio": _safe_mean(sharpe_ratios),
        "mean_max_drawdown": _safe_mean(max_drawdowns),
        "pooled_metrics_all_trades": MetricsCalculator().calculate(all_trades),
    }


def run_single_indicator_backtests(
    indicators: dict[str, str] | None = None,
    symbols: list[str] | None = None,
    start_date: str = START_DATE,
    end_date: str = END_DATE,
    output_dir: str | None = None,
) -> dict[str, str]:
    indicators = indicators or INDICATORS
    symbols = symbols or get_index_symbols("VN30")
    if not symbols:
        raise ValueError("No VN30 symbols resolved from Supabase")

    output_dir = output_dir or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "reports", "single_indicator"
    )
    os.makedirs(output_dir, exist_ok=True)

    output_paths: dict[str, str] = {}

    for indicator_name, score_column in indicators.items():
        print("=" * 60)
        print(f"BACKTEST — {indicator_name} only — VN30 — {start_date} to {end_date}")
        print("=" * 60)

        per_symbol: dict[str, Any] = {}
        errors: dict[str, str] = {}

        for symbol in symbols:
            try:
                df_1d = _build_dataframe(symbol=symbol, interval="1d", start_date=start_date, end_date=end_date)
                if len(df_1d) <= 50:
                    raise ValueError("Insufficient data (<=50 candles)")
                result = _backtest_symbol_for_indicator(df_1d, score_column)
                per_symbol[symbol] = result
                m = result["metrics"]
                print(
                    f"[{indicator_name}] {symbol}: {m['volume']['n_trades']} trades, "
                    f"win_rate={m['volume']['win_rate']:.2%}, "
                    f"total_return={m['pnl']['total_return']:.2%}"
                )
            except Exception as e:  # noqa: BLE001 — one symbol failing shouldn't stop the batch
                errors[symbol] = str(e)
                print(f"[{indicator_name}] {symbol}: FAILED — {e}")

        aggregate = _aggregate_metrics(per_symbol)

        payload = {
            "indicator": indicator_name,
            "score_column": score_column,
            "universe": "VN30",
            "start_date": start_date,
            "end_date": end_date,
            "max_hold_candles": MAX_HOLD_CANDLES,
            "transaction_cost_pct": DEFAULT_TRANSACTION_COST_PCT,
            "generated_at": datetime.now().isoformat(),
            "symbols_tested": len(symbols),
            "symbols_succeeded": len(per_symbol),
            "errors": errors,
            "aggregate": aggregate,
            "per_symbol": per_symbol,
        }

        filename = f"vn30_{score_column.replace('_score', '')}_backtest.json"
        output_path = os.path.join(output_dir, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(_sanitize_json(payload), f, ensure_ascii=False, indent=2)

        output_paths[indicator_name] = output_path
        print(f"Saved {indicator_name} backtest results to {output_path}\n")

    return output_paths


if __name__ == "__main__":
    run_single_indicator_backtests()
