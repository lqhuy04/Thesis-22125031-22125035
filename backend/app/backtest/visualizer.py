import json
import math
import os
from datetime import datetime
from typing import Any
import numpy as np
import pandas as pd


def get_backtest_visualization_data(
    df: pd.DataFrame,
    trades: list[dict[str, Any]],
    metrics: dict[str, Any],
    symbol: str,
    engine_trades: list[dict[str, Any]] | None = None,
    engine_metrics: dict[str, Any] | None = None,
    pipeline_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Extracts and prepares all visualization data required for interactive charts.

    engine_trades / engine_metrics: kết quả baseline (technical-only, không LLM)
    để hiển thị so sánh cạnh full pipeline.
    pipeline_results: output của agent theo từng ngày tín hiệu, dùng dựng report.
    """
    # Create copy to avoid modifying original
    data = df.copy()
    
    # Identify datetime column
    if "datetime" in data.columns:
        times = pd.to_datetime(data["datetime"])
    else:
        times = pd.to_datetime(data.index)
        data["datetime"] = times
        
    # Check if data is intraday
    is_intraday = False
    if len(times) > 1:
        time_diff = (times.iloc[1] - times.iloc[0]).total_seconds()
        if time_diff < 86400:
            is_intraday = True

    # Format times for Lightweight Charts
    if is_intraday:
        # UNIX timestamp in seconds
        data["time"] = times.astype(np.int64) // 10**9
    else:
        # Date string YYYY-MM-DD
        data["time"] = times.dt.strftime("%Y-%m-%d")

    # Prepare candlestick data
    ohlc_data = []
    for _, row in data.iterrows():
        ohlc_data.append({
            "time": row["time"],
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
        })

    # Prepare volume data
    volume_data = []
    for _, row in data.iterrows():
        volume_data.append({
            "time": row["time"],
            "value": float(row["volume"]) if pd.notna(row.get("volume")) else 0.0,
            "color": "#26a69a" if row["close"] >= row["open"] else "#ef5350"
        })

    # Prepare indicators
    sma20_data = []
    sma50_data = []
    rsi_data = []
    macd_line_data = []
    macd_signal_data = []
    macd_hist_data = []

    for _, row in data.iterrows():
        t = row["time"]
        if pd.notna(row.get("sma_20")):
            sma20_data.append({"time": t, "value": float(row["sma_20"])})
        if pd.notna(row.get("sma_50")):
            sma50_data.append({"time": t, "value": float(row["sma_50"])})
        if pd.notna(row.get("rsi_14")):
            rsi_data.append({"time": t, "value": float(row["rsi_14"])})
        if pd.notna(row.get("macd")):
            macd_line_data.append({"time": t, "value": float(row["macd"])})
        if pd.notna(row.get("macd_signal")):
            macd_signal_data.append({"time": t, "value": float(row["macd_signal"])})
        if pd.notna(row.get("macd_histogram")):
            macd_hist_data.append({
                "time": t,
                "value": float(row["macd_histogram"]),
                "color": "#26a69a" if row["macd_histogram"] >= 0 else "#ef5350"
            })

    # Prepare trade markers and lines
    # Map dates to their formatted string representation for matching
    date_to_time = {}
    for _, row in data.iterrows():
        dt_str = pd.to_datetime(row["datetime"]).strftime("%Y-%m-%d")
        date_to_time[dt_str] = row["time"]

    def _format_trades(trade_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        formatted: list[dict[str, Any]] = []
        for idx, trade in enumerate(trade_list):
            entry_dt = pd.to_datetime(trade["entry_date"]).strftime("%Y-%m-%d")
            exit_dt = pd.to_datetime(trade["exit_date"]).strftime("%Y-%m-%d")

            entry_time = date_to_time.get(entry_dt)
            exit_time = date_to_time.get(exit_dt)

            if entry_time is None or exit_time is None:
                continue

            # Extract trade details
            formatted_trade = {
                "index": idx + 1,
                "entry_date": trade["entry_date"],
                "exit_date": trade["exit_date"],
                "entry_time": entry_time,
                "exit_time": exit_time,
                "entry_price": float(trade["entry_price"]),
                "exit_price": float(trade["exit_price"]),
                "take_profit": float(trade["take_profit"]) if trade.get("take_profit") else None,
                "stop_loss": float(trade["stop_loss"]) if trade.get("stop_loss") else None,
                "return_pct": float(trade["return_pct"]),
                "exit_reason": trade.get("exit_reason", "TIMEOUT"),
                "confidence": trade.get("confidence", "N/A"),
            }

            # Build segment data points for the visual line of this trade
            # Find all records in our data window
            trade_indices = data[(times >= pd.to_datetime(trade["entry_date"])) & (times <= pd.to_datetime(trade["exit_date"]))]
            segment_points = [r["time"] for _, r in trade_indices.iterrows()]

            formatted_trade["segment_times"] = segment_points
            formatted.append(formatted_trade)
        return formatted

    formatted_trades = _format_trades(trades)

    # Baseline (technical-only, không LLM) để so sánh trên web.
    baseline = None
    if engine_trades is not None or engine_metrics is not None:
        baseline = {
            "metrics": engine_metrics or {},
            "trades": _format_trades(engine_trades or []),
        }

    return {
        "symbol": symbol,
        "ohlc_data": ohlc_data,
        "volume_data": volume_data,
        "sma20_data": sma20_data,
        "sma50_data": sma50_data,
        "rsi_data": rsi_data,
        "macd_line_data": macd_line_data,
        "macd_signal_data": macd_signal_data,
        "macd_hist_data": macd_hist_data,
        "trades": formatted_trades,
        "metrics": metrics,
        "baseline": baseline,
        "agent_reports": pipeline_results or [],
    }


def generate_backtest_json(
    df: pd.DataFrame,
    trades: list[dict[str, Any]],
    metrics: dict[str, Any],
    symbol: str,
    output_path: str,
    engine_trades: list[dict[str, Any]] | None = None,
    engine_metrics: dict[str, Any] | None = None,
    pipeline_results: list[dict[str, Any]] | None = None,
) -> None:
    """
    Saves a sanitized JSON file containing all interactive visualization details.
    """
    viz_data = get_backtest_visualization_data(
        df,
        trades,
        metrics,
        symbol,
        engine_trades=engine_trades,
        engine_metrics=engine_metrics,
        pipeline_results=pipeline_results,
    )
    
    def _sanitize(val: Any) -> Any:
        if isinstance(val, dict):
            return {k: _sanitize(v) for k, v in val.items()}
        if isinstance(val, list):
            return [_sanitize(v) for v in val]
        if isinstance(val, (np.floating, float)):
            number = float(val)
            return number if math.isfinite(number) else None
        if isinstance(val, (np.integer, int)):
            return int(val)
        return val
        
    sanitized_data = _sanitize(viz_data)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sanitized_data, f, ensure_ascii=False, indent=2)
    print(f"Visualization JSON saved successfully to {output_path}")
