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
  "max_hold_candles": 20,
  "min_signal_score": 4,
  "exit_on_score_drop": false,
  "one_minute_lookback_days": 30,
  "use_intraday": true
}

## VN30 Aggregate Stats (local JSON)

Mỗi lần `run_full_backtest` chạy xong sẽ upsert thống kê của mã đó vào MỘT file
JSON tổng hợp local: `backtest/reports/vn30_stats.json` (key = symbol). Vì admin
dashboard chạy cả rổ VN30 bằng cách gọi `/api/agentic/backtest` tuần tự cho từng
mã, file này sẽ tự gom đủ 30 mã sau khi batch chạy xong.

Nội dung mỗi mã (`vn30_stats.py` → `build_symbol_stats`):
1. `performance` — n_trades, win_rate, total_return, avg_return, annualized_return,
   max_drawdown, sharpe_ratio, profit_factor (full pipeline).
2. `baseline_engine_performance` — cùng các chỉ số trên cho engine-only (không LLM).
3. `benchmark` — pipeline_return vs buy_hold_return (+delta), impact_on_returns,
   percentile/p-value so với chiến lược ngẫu nhiên.
4. `statistical_tests` — ttest, permutation, information_coefficient (ic + p_value),
   confidence_vs_outcome_anova (f_stat, p_value, group_means).
5. `walk_forward` — avg_sharpe, std_sharpe, consistent_wins + return từng window.
6. `regime` / `confidence_calibration` — win_rate / avg_return / n_trades theo nhóm.

Phần `aggregate` tổng hợp profit toàn rổ (mean / median / compounded) và so sánh
pipeline với baseline engine-only của các mã hiện có trong file.

## Notes

- LLM calls happen only on technical signal dates (to reduce cost).
- Requires working LLM configuration and data access via MarketService.
- Parity checks must pass before the full backtest runs.
