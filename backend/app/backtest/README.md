# Backtest Engine (LLM Pipeline)

This folder contains the end-to-end backtest engine used by the LLM-backed
pipeline. It is invoked by the API endpoint at /api/agentic/backtest and by
app/services/backtest_pipeline_service.py.

## What It Does

- Computes indicators and technical scores (RSI, MA, Bollinger, MACD, KDJ).
- Generates technical signals, then calls the live LLM pipeline only on signal dates.
- Simulates trades and calculates metrics, benchmarks, and statistical tests.
- Runs walk-forward validation, regime analysis, and confidence calibration.

## Key Entry Point

- run_full_backtest in backtest/run.py

Signature:

run_full_backtest(
    df_1d,        # 5y daily OHLCV
    df_1m,        # 1m OHLCV (recent window)
    market_df,    # VN-Index daily OHLCV
    symbol,
    stop_loss_pct=0.05,
    take_profit_pct=0.10,
    max_hold_candles=20,
    exit_on_score_drop=False,
)

## Data Requirements

All DataFrames must include:
- datetime (timestamp)
- open, high, low, close, volume

No look-ahead is used; indicators at index i only use data up to i.
Entry price is the next candle open (open[i+1]).

## API Usage (Backtest Pipeline)

POST /api/agentic/backtest

Example payload:
{
  "symbol": "VNM",
  "start_date": "2021-01-01",
  "end_date": "2024-12-31",
  "market_symbol": "VNINDEX",
  "stop_loss_pct": 0.05,
  "take_profit_pct": 0.10,
  "max_hold_candles": 20,
  "exit_on_score_drop": false,
  "one_minute_lookback_days": 30
}

## Notes

- LLM calls happen only on technical signal dates (to reduce cost).
- Requires working LLM configuration and data access via MarketService.
- Parity checks must pass before the full backtest runs.
