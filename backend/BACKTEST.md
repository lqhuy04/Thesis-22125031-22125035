# Backtest Implementation

This repository now includes a thesis-friendly backtest for the technical strategy used by the agentic analysis flow.

## What was implemented

- A new API endpoint at `POST /api/agentic/backtest`.
- A reusable backtest service that reuses the same technical indicator scoring logic as the live technical analysis node.
- Trade-by-trade reporting, equity curve tracking, and summary metrics.
- Optional benchmark comparison against a reference symbol such as `VNINDEX`.

## Strategy rules

- Long-only strategy.
- A trade is opened only when `total_score >= min_total_score`.
- The signal is generated from the candle close.
- Entry is simulated at the next candle open.
- Exit is simulated after `holding_period` candles at the candle close.
- Only one position can be open at a time.
- Transaction cost and slippage are applied on both entry and exit.

## Inputs

Request body fields:

- `symbol`: stock symbol to test.
- `interval`: candle interval, default `1d`.
- `start_date`: optional ISO start date.
- `end_date`: optional ISO end date.
- `holding_period`: number of candles to hold each trade.
- `min_total_score`: signal threshold, default `3`.
- `transaction_cost_bps`: fee assumption in basis points.
- `slippage_bps`: slippage assumption in basis points.
- `initial_capital`: starting capital in VND.
- `benchmark_symbol`: optional benchmark symbol.

Example:

```json
{
  "symbol": "VNM",
  "interval": "1d",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "holding_period": 5,
  "min_total_score": 3,
  "transaction_cost_bps": 20,
  "slippage_bps": 10,
  "initial_capital": 100000000,
  "benchmark_symbol": "VNINDEX"
}
```

## Output

The API returns:

- `summary`: aggregate statistics for the run.
- `trades`: detailed trade log with signal snapshot and per-trade returns.
- `equity_curve`: time series of equity values.
- `assumptions`: a short list of methodology assumptions.

Key summary fields:

- `total_return_pct`
- `buy_and_hold_return_pct`
- `benchmark_return_pct`
- `win_rate_pct`
- `avg_trade_return_pct`
- `profit_factor`
- `max_drawdown_pct`
- `sharpe_ratio`

## Thesis note

The important methodological point is that the backtest is not a separate model. It is the live technical rule set applied to historical candles with no look-ahead, fixed execution assumptions, and explicit costs.