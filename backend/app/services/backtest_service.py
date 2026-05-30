"""
Backtest service for the technical-only strategy.

The implementation reuses the same indicator calculations and scoring rules as
the live technical analysis node, then simulates a non-overlapping long-only
strategy on historical candles.
"""

from __future__ import annotations

from datetime import datetime
from statistics import mean
from typing import Any
import math

import pandas as pd

from app.models.backtest_schemas import BacktestRequest
from app.services.market_service import MarketService
from app.services.technical_indicators_service import TechnicalIndicatorsService


def _parse_dt(trading_time: str) -> datetime:
    clean_time = trading_time.split("+")[0].replace("Z", "")
    try:
        return datetime.fromisoformat(clean_time)
    except ValueError:
        return datetime.strptime(clean_time[:19], "%Y-%m-%dT%H:%M:%S")


def _clean(value: Any) -> float | None:
    if value is None:
        return None
    try:
        numeric_value = float(value)
        if math.isnan(numeric_value) or math.isinf(numeric_value):
            return None
        return numeric_value
    except (TypeError, ValueError):
        return None


        if row["_dt"] < curve_start_boundary:
            continue

        equity_curve.append(
            {
                "time": row["_dt"].isoformat(),
                "equity": round(mark_to_market, 4),
                "cash": round(cash, 4),
                "in_position": active_trade is not None,
            }
        )
    if current < 35 and current > previous:
        return 1, f"RSI đang hồi phục từ vùng quá bán ({previous:.1f} → {current:.1f})"
    if current >= 70:
        return 0, f"RSI quá mua ({current:.1f}), rủi ro điều chỉnh"
    if current > previous:
        return 0, f"RSI tăng nhưng trong vùng 35–50, chưa đủ động lực ({previous:.1f} → {current:.1f})"
    return 0, f"RSI đang giảm ({previous:.1f} → {current:.1f})"


def _score_ma(
    sma20_current: float | None,
    sma20_previous: float | None,
    sma50_current: float | None,
    sma50_previous: float | None,
    price: float | None,
) -> tuple[int, str]:
    if sma20_current is None or sma50_current is None:
        return 0, "Không đủ dữ liệu MA"

    if sma20_previous is not None and sma50_previous is not None:
        if sma20_previous < sma50_previous and sma20_current >= sma50_current:
            return 1, f"Golden cross: SMA20 vừa cắt lên SMA50 ({sma20_current:,.2f} > {sma50_current:,.2f})"

    if sma20_previous is not None and sma50_previous is not None:
        gap_current = sma20_current - sma50_current
        gap_previous = sma20_previous - sma50_previous
        if sma20_current > sma50_current and gap_current > gap_previous:
            return 1, f"Uptrend tăng tốc: khoảng cách SMA20–SMA50 nới rộng ({gap_previous:,.2f} → {gap_current:,.2f})"

    if price is not None and sma20_current > sma50_current and price > sma20_current:
        return 1, f"Giá ({price:,.2f}) trên SMA20 ({sma20_current:,.2f}) và SMA20 trên SMA50 ({sma50_current:,.2f})"

    if sma20_current < sma50_current:
        return 0, f"SMA20 ({sma20_current:,.2f}) dưới SMA50 ({sma50_current:,.2f}), xu hướng giảm"
    if price is not None and price < sma20_current:
        return 0, f"Giá ({price:,.2f}) dưới SMA20 ({sma20_current:,.2f}), chưa xác nhận xu hướng tăng"
    return 0, f"SMA20 ({sma20_current:,.2f}) và SMA50 ({sma50_current:,.2f}) chưa có tín hiệu tích cực"


def _score_boll(
    upper: float | None,
    middle: float | None,
    lower: float | None,
    close_current: float | None,
    close_previous: float | None,
    current_price: float | None,
) -> tuple[int, str]:
    if upper is None or middle is None or lower is None:
        return 0, "Không đủ dữ liệu Bollinger Bands"

    price_now = current_price if current_price is not None else close_current

    if price_now is None or close_previous is None:
        return 0, "Không đủ dữ liệu giá để tính Bollinger Bands"

    if close_previous < middle and price_now >= middle:
        return 1, f"Giá vừa vượt lên trên BB middle ({close_previous:,.2f} → {price_now:,.2f}, middle={middle:,.2f})"

    if close_current is not None and close_current > middle:
        gap_current = close_current - middle
        gap_previous = close_previous - middle
        if gap_current > gap_previous:
            return 1, f"Giá trên BB middle và đà tăng mạnh dần (khoảng cách: {gap_previous:,.2f} → {gap_current:,.2f})"

    if price_now <= lower and price_now > close_previous:
        return 1, f"Giá hồi phục từ vùng quá bán BB lower ({close_previous:,.2f} → {price_now:,.2f}, lower={lower:,.2f})"

    if price_now > upper:
        return 0, f"Giá ({price_now:,.2f}) vượt BB upper ({upper:,.2f}), rủi ro quá mua"
    if price_now < middle:
        return 0, f"Giá ({price_now:,.2f}) dưới BB middle ({middle:,.2f}), xu hướng yếu"
    return 0, f"Giá ({price_now:,.2f}) trong vùng middle–upper nhưng đà tăng chưa rõ"


def _score_macd(
    macd_current: float | None,
    macd_previous: float | None,
    signal_current: float | None,
    signal_previous: float | None,
    hist_current: float | None,
    hist_previous: float | None,
) -> tuple[int, str]:
    if macd_current is None or signal_current is None or hist_current is None:
        return 0, "Không đủ dữ liệu MACD"

    if macd_previous is not None and signal_previous is not None:
        if macd_previous < signal_previous and macd_current >= signal_current:
            return 1, f"MACD vừa cắt lên Signal ({macd_previous:.4f} → {macd_current:.4f}, signal={signal_current:.4f})"

    if hist_previous is not None:
        if macd_current > signal_current and hist_current > hist_previous:
            return 1, f"MACD trên Signal và histogram tăng tốc ({hist_previous:.4f} → {hist_current:.4f})"

    if hist_previous is not None:
        if hist_previous < 0 and hist_current >= 0:
            return 1, f"Histogram vừa chuyển dương ({hist_previous:.4f} → {hist_current:.4f}), momentum đổi chiều"

    if macd_current < signal_current:
        return 0, f"MACD ({macd_current:.4f}) dưới Signal ({signal_current:.4f}), xu hướng giảm"
    if hist_current < 0:
        return 0, f"Histogram âm ({hist_current:.4f}), momentum tiêu cực"
    if hist_previous is not None and hist_current < hist_previous:
        return 0, f"MACD trên Signal nhưng histogram đang suy yếu ({hist_previous:.4f} → {hist_current:.4f})"
    return 0, "MACD chưa có tín hiệu tích cực rõ ràng"


def _score_kdj(
    k_current: float | None,
    k_previous: float | None,
    d_current: float | None,
    d_previous: float | None,
    j_current: float | None,
    j_previous: float | None,
) -> tuple[int, str]:
    if k_current is None or d_current is None or j_current is None:
        return 0, "Không đủ dữ liệu KDJ"

    if k_previous is not None and d_previous is not None:
        if k_previous < d_previous and k_current >= d_current:
            return 1, f"K vừa cắt lên D ({k_previous:.2f} → {k_current:.2f}, D={d_current:.2f})"

    if j_previous is not None:
        if k_current > d_current and j_current > j_previous:
            return 1, f"K trên D và J tăng tốc ({j_previous:.2f} → {j_current:.2f})"

    if k_previous is not None:
        if k_current < 20 and k_current > k_previous:
            return 1, f"K hồi phục từ vùng quá bán ({k_previous:.2f} → {k_current:.2f})"

    if k_current > 80:
        return 0, f"K ({k_current:.2f}) trong vùng quá mua, rủi ro điều chỉnh"
    if k_current < d_current:
        return 0, f"K ({k_current:.2f}) dưới D ({d_current:.2f}), xu hướng yếu"
    if j_previous is not None and j_current < j_previous:
        return 0, f"K trên D nhưng J đang suy yếu ({j_previous:.2f} → {j_current:.2f})"
    return 0, "KDJ chưa có tín hiệu tích cực rõ ràng"


def _parse_date_boundary(value: str | None, end_of_day: bool) -> datetime | None:
    if not value:
        return None

    parsed = datetime.fromisoformat(value)
    if len(value) == 10:
        if end_of_day:
            return parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
        return parsed.replace(hour=0, minute=0, second=0, microsecond=0)
    return parsed


def _safe_division(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _max_drawdown(equity_values: list[float]) -> float:
    if not equity_values:
        return 0.0

    peak = equity_values[0]
    max_drawdown = 0.0

    for value in equity_values:
        if value > peak:
            peak = value
        if peak > 0:
            drawdown = (value - peak) / peak
            if drawdown < max_drawdown:
                max_drawdown = drawdown

    return abs(max_drawdown) * 100.0


def _sharpe_ratio(equity_values: list[float]) -> float | None:
    if len(equity_values) < 3:
        return None

    daily_returns: list[float] = []
    for index in range(1, len(equity_values)):
        previous = equity_values[index - 1]
        current = equity_values[index]
        if previous <= 0:
            continue
        daily_returns.append((current / previous) - 1.0)

    if len(daily_returns) < 2:
        return None

    avg_return = mean(daily_returns)
    variance = sum((value - avg_return) ** 2 for value in daily_returns) / (len(daily_returns) - 1)
    if variance <= 0:
        return None

    return (avg_return / math.sqrt(variance)) * math.sqrt(252)


def _technical_snapshot(
    slice_df: pd.DataFrame,
    symbol: str,
    interval: str,
    min_total_score: int,
) -> dict[str, Any]:
    indicators = TechnicalIndicatorsService.calculate_all_indicators(
        slice_df[["open", "high", "low", "close", "volume"]]
    )

    latest = slice_df.iloc[-1]
    previous = slice_df.iloc[-2] if len(slice_df) >= 2 else None

    rsi_current = _clean(indicators["rsi_14"][-1])
    rsi_previous = _clean(indicators["rsi_14"][-2]) if len(indicators["rsi_14"]) >= 2 else None
    rsi_score, rsi_reason = _score_rsi(rsi_current, rsi_previous)

    sma20_current = _clean(indicators["sma_20"][-1])
    sma20_previous = _clean(indicators["sma_20"][-2]) if len(indicators["sma_20"]) >= 2 else None
    sma50_current = _clean(indicators["sma_50"][-1])
    sma50_previous = _clean(indicators["sma_50"][-2]) if len(indicators["sma_50"]) >= 2 else None
    price_for_ma = _clean(latest.get("close"))
    ma_score, ma_reason = _score_ma(
        sma20_current,
        sma20_previous,
        sma50_current,
        sma50_previous,
        price_for_ma,
    )

    bb_upper = _clean(indicators["bb_upper"][-1])
    bb_middle = _clean(indicators["bb_middle"][-1])
    bb_lower = _clean(indicators["bb_lower"][-1])
    close_current = _clean(latest.get("close"))
    close_previous = _clean(previous.get("close")) if previous is not None else None
    boll_score, boll_reason = _score_boll(
        bb_upper,
        bb_middle,
        bb_lower,
        close_current,
        close_previous,
        close_current,
    )

    macd_current = _clean(indicators["macd"][-1])
    macd_previous = _clean(indicators["macd"][-2]) if len(indicators["macd"]) >= 2 else None
    signal_current = _clean(indicators["macd_signal"][-1])
    signal_previous = _clean(indicators["macd_signal"][-2]) if len(indicators["macd_signal"]) >= 2 else None
    hist_current = _clean(indicators["macd_histogram"][-1])
    hist_previous = _clean(indicators["macd_histogram"][-2]) if len(indicators["macd_histogram"]) >= 2 else None
    macd_score, macd_reason = _score_macd(
        macd_current,
        macd_previous,
        signal_current,
        signal_previous,
        hist_current,
        hist_previous,
    )

    k_current = _clean(indicators["kdj_k"][-1])
    k_previous = _clean(indicators["kdj_k"][-2]) if len(indicators["kdj_k"]) >= 2 else None
    d_current = _clean(indicators["kdj_d"][-1])
    d_previous = _clean(indicators["kdj_d"][-2]) if len(indicators["kdj_d"]) >= 2 else None
    j_current = _clean(indicators["kdj_j"][-1])
    j_previous = _clean(indicators["kdj_j"][-2]) if len(indicators["kdj_j"]) >= 2 else None
    kdj_score, kdj_reason = _score_kdj(
        k_current,
        k_previous,
        d_current,
        d_previous,
        j_current,
        j_previous,
    )

    total_score = rsi_score + ma_score + boll_score + macd_score + kdj_score

    return {
        "symbol": symbol,
        "interval": interval,
        "signal_time": latest["_dt"].isoformat(),
        "current_price": _clean(latest.get("close")),
        "total_score": total_score,
        "recommendation": "Mua" if total_score >= min_total_score else "Chờ",
        "indicators": {
            "rsi": {
                "value": {"current": rsi_current, "previous": rsi_previous},
                "score": rsi_score,
                "reason": rsi_reason,
            },
            "ma": {
                "value": {
                    "sma20_current": sma20_current,
                    "sma20_previous": sma20_previous,
                    "sma50_current": sma50_current,
                    "sma50_previous": sma50_previous,
                },
                "score": ma_score,
                "reason": ma_reason,
            },
            "boll": {
                "value": {
                    "upper": bb_upper,
                    "middle": bb_middle,
                    "lower": bb_lower,
                    "close_current": close_current,
                    "close_previous": close_previous,
                },
                "score": boll_score,
                "reason": boll_reason,
            },
            "macd": {
                "value": {
                    "macd_current": macd_current,
                    "macd_previous": macd_previous,
                    "signal_current": signal_current,
                    "signal_previous": signal_previous,
                    "hist_current": hist_current,
                    "hist_previous": hist_previous,
                },
                "score": macd_score,
                "reason": macd_reason,
            },
            "kdj": {
                "value": {
                    "k_current": k_current,
                    "k_previous": k_previous,
                    "d_current": d_current,
                    "d_previous": d_previous,
                    "j_current": j_current,
                    "j_previous": j_previous,
                },
                "score": kdj_score,
                "reason": kdj_reason,
            },
        },
    }


def _build_window_dataframe(
    symbol: str,
    interval: str,
    end_date: str | None,
) -> pd.DataFrame:
    rows = MarketService.get_stock_price_by_interval(symbol=symbol, interval=interval)
    if not rows:
        raise ValueError(f"Không có dữ liệu giá cho mã {symbol} ở interval {interval}")

    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError(f"Không có dữ liệu giá cho mã {symbol} ở interval {interval}")

    if "trading_time" not in df.columns:
        raise ValueError("Dữ liệu thị trường thiếu cột trading_time")

    df["_dt"] = df["trading_time"].apply(_parse_dt)
    df = df.sort_values("_dt").reset_index(drop=True)

    for column in ["open", "high", "low", "close", "volume"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["open", "high", "low", "close", "volume"]).reset_index(drop=True)
    if end_date:
        end_boundary = _parse_date_boundary(end_date, end_of_day=True)
        df = df[df["_dt"] <= end_boundary].reset_index(drop=True)

    return df


def _build_benchmark_return(
    symbol: str | None,
    interval: str,
    start_time: datetime,
    end_time: datetime,
) -> float | None:
    if not symbol:
        return None

    rows = MarketService.get_stock_price_by_interval(symbol=symbol, interval=interval)
    if not rows:
        return None

    df = pd.DataFrame(rows)
    if df.empty or "trading_time" not in df.columns:
        return None

    df["_dt"] = df["trading_time"].apply(_parse_dt)
    df = df.sort_values("_dt").reset_index(drop=True)
    df = df[(df["_dt"] >= start_time) & (df["_dt"] <= end_time)].reset_index(drop=True)
    if len(df) < 2:
        return None

    first_open = _clean(df.iloc[0].get("open"))
    last_close = _clean(df.iloc[-1].get("close"))
    if first_open is None or last_close is None or first_open == 0:
        return None

    return (last_close / first_open) - 1.0


def run_backtest(request: BacktestRequest) -> dict[str, Any]:
    symbol = request.symbol.upper().strip()
    interval = request.interval

    if interval not in {"1m", "5m", "15m", "30m", "1h", "1d", "1w", "1M"}:
        raise ValueError(f"Unsupported interval: {interval}")

    start_boundary = _parse_date_boundary(request.start_date, end_of_day=False)
    df = _build_window_dataframe(symbol=symbol, interval=interval, end_date=request.end_date)
    if len(df) < 55:
        raise ValueError("Không đủ dữ liệu lịch sử để backtest. Cần tối thiểu khoảng 55 candles.")

    curve_start_boundary = start_boundary if start_boundary is not None else df.iloc[0]["_dt"]
    evaluation_df = df[df["_dt"] >= curve_start_boundary].reset_index(drop=True)
    if evaluation_df.empty:
        raise ValueError("Không có dữ liệu trong khoảng thời gian backtest được chọn.")

    candidates: list[dict[str, Any]] = []
    for signal_index in range(49, len(df) - 1):
        slice_df = df.iloc[: signal_index + 1].reset_index(drop=True)
        snapshot = _technical_snapshot(
            slice_df=slice_df,
            symbol=symbol,
            interval=interval,
            min_total_score=request.min_total_score,
        )

        if start_boundary is not None:
            signal_time = datetime.fromisoformat(snapshot["signal_time"])
            if signal_time < start_boundary:
                continue

        if snapshot["total_score"] < request.min_total_score:
            continue

        entry_index = signal_index + 1
        exit_index = entry_index + request.holding_period - 1
        if exit_index >= len(df):
            continue

        candidates.append(
            {
                "signal_index": signal_index,
                "entry_index": entry_index,
                "exit_index": exit_index,
                "snapshot": snapshot,
            }
        )

    equity = request.initial_capital
    cash = request.initial_capital
    units = 0.0
    pending_trade: dict[str, Any] | None = None
    active_trade: dict[str, Any] | None = None
    trade_cursor = 0
    trades: list[dict[str, Any]] = []
    equity_curve: list[dict[str, Any]] = []

    total_fee = (request.transaction_cost_bps + request.slippage_bps) / 10_000.0

    for index, row in df.iterrows():
        if pending_trade is not None and index == pending_trade["entry_index"]:
            entry_open = _clean(row.get("open"))
            if entry_open is None or entry_open <= 0:
                pending_trade = None
            else:
                entry_price = entry_open * (1 + total_fee)
                if cash > 0:
                    units = cash / entry_price
                    active_trade = {
                        **pending_trade,
                        "entry_time": row["_dt"],
                        "entry_price": entry_price,
                        "entry_cash": cash,
                    }
                    cash = 0.0
                pending_trade = None

        mark_to_market = cash if active_trade is None else units * float(row["close"])

        if row["_dt"] < curve_start_boundary:
            continue

        if active_trade is not None and index == active_trade["exit_index"]:
            exit_close = _clean(row.get("close"))
            if exit_close is not None and exit_close > 0:
                exit_price = exit_close * (1 - total_fee)
                cash = units * exit_price
                mark_to_market = cash

                trade_return = _safe_division(cash, active_trade["entry_cash"])
                net_return_pct = ((trade_return - 1.0) * 100.0) if trade_return is not None else 0.0

                gross_return = _safe_division(exit_close, active_trade["entry_price"])
                gross_return_pct = ((gross_return - 1.0) * 100.0) if gross_return is not None else 0.0

                trades.append(
                    {
                        "signal_time": active_trade["snapshot"]["signal_time"],
                        "entry_time": active_trade["entry_time"].isoformat(),
                        "exit_time": row["_dt"].isoformat(),
                        "signal_index": active_trade["signal_index"],
                        "entry_index": active_trade["entry_index"],
                        "exit_index": active_trade["exit_index"],
                        "recommendation": active_trade["snapshot"]["recommendation"],
                        "total_score": active_trade["snapshot"]["total_score"],
                        "entry_price": round(active_trade["entry_price"], 4),
                        "exit_price": round(exit_close, 4),
                        "gross_return_pct": round(gross_return_pct, 4),
                        "net_return_pct": round(net_return_pct, 4),
                        "signal_snapshot": active_trade["snapshot"],
                    }
                )

                equity = cash
                units = 0.0
                active_trade = None

        equity_curve.append(
            {
                "time": row["_dt"].isoformat(),
                "equity": round(mark_to_market, 4),
                "cash": round(cash, 4),
                "in_position": active_trade is not None,
            }
        )

        if active_trade is None and pending_trade is None and trade_cursor < len(candidates):
            candidate = candidates[trade_cursor]
            if candidate["signal_index"] == index:
                pending_trade = candidate
                trade_cursor += 1

    equity_values = [point["equity"] for point in equity_curve]
    max_drawdown_pct = _max_drawdown(equity_values)
    sharpe_ratio = _sharpe_ratio(equity_values)

    total_return_pct = ((equity / request.initial_capital) - 1.0) * 100.0 if request.initial_capital else 0.0
    trade_returns = [trade["net_return_pct"] for trade in trades]

    win_rate_pct = (sum(1 for trade in trade_returns if trade > 0) / len(trade_returns) * 100.0) if trade_returns else 0.0
    avg_trade_return_pct = mean(trade_returns) if trade_returns else 0.0
    positive_sum = sum(trade for trade in trade_returns if trade > 0)
    negative_sum = abs(sum(trade for trade in trade_returns if trade < 0))
    profit_factor = (positive_sum / negative_sum) if negative_sum > 0 else None

    buy_and_hold_return_pct = None
    benchmark_return_pct = None

    if len(evaluation_df) >= 2:
        first_open = _clean(evaluation_df.iloc[0].get("open"))
        last_close = _clean(evaluation_df.iloc[-1].get("close"))
        if first_open is not None and last_close is not None and first_open > 0:
            buy_and_hold_return_pct = ((last_close / first_open) - 1.0) * 100.0

    if len(evaluation_df) > 0:
        benchmark_return = _build_benchmark_return(
            symbol=request.benchmark_symbol,
            interval=interval,
            start_time=evaluation_df.iloc[0]["_dt"],
            end_time=evaluation_df.iloc[-1]["_dt"],
        )
        if benchmark_return is not None:
            benchmark_return_pct = benchmark_return * 100.0

    summary = {
        "symbol": symbol,
        "interval": interval,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "holding_period": request.holding_period,
        "min_total_score": request.min_total_score,
        "transaction_cost_bps": request.transaction_cost_bps,
        "slippage_bps": request.slippage_bps,
        "initial_capital": request.initial_capital,
        "final_equity": round(equity, 4),
        "total_return_pct": round(total_return_pct, 4),
        "buy_and_hold_return_pct": round(buy_and_hold_return_pct, 4) if buy_and_hold_return_pct is not None else None,
        "benchmark_symbol": request.benchmark_symbol,
        "benchmark_return_pct": round(benchmark_return_pct, 4) if benchmark_return_pct is not None else None,
        "total_bars": len(evaluation_df),
        "signals_generated": len(candidates),
        "trades_taken": len(trades),
        "win_rate_pct": round(win_rate_pct, 4),
        "avg_trade_return_pct": round(avg_trade_return_pct, 4),
        "profit_factor": round(profit_factor, 4) if profit_factor is not None else None,
        "max_drawdown_pct": round(max_drawdown_pct, 4),
        "sharpe_ratio": round(sharpe_ratio, 4) if sharpe_ratio is not None else None,
    }

    assumptions = [
        "Long-only strategy: chỉ mở vị thế khi total_score đạt ngưỡng.",
        "Tín hiệu được tạo tại giá đóng cửa của candle tín hiệu và khớp lệnh ở candle kế tiếp.",
        "Mỗi trade là non-overlapping: chỉ giữ tối đa một vị thế tại một thời điểm.",
        "Chi phí giao dịch và slippage được áp dụng theo basis points trên cả chiều mua và bán.",
        "Backtest dùng cùng bộ indicator và scoring rule với logic phân tích kỹ thuật hiện tại.",
    ]

    return {
        "summary": summary,
        "trades": trades,
        "equity_curve": equity_curve,
        "assumptions": assumptions,
    }