from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd

from agentic_ai_v2.analyze.technical_scoring import (
    SCORE_COLUMN_BY_INDICATOR,
    score_indicators,
)
from app.services.technical_indicators_service import (
    TechnicalIndicatorsService,
)

DEFAULT_TRANSACTION_COST_PCT = 0.015


class IndicatorEngine:
    def __init__(
        self,
        rsi_period: int = 14,
        sma_short: int = 20,
        sma_long: int = 50,
        boll_period: int = 20,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        kdj_period: int = 9,
        kdj_smooth: int = 3,
    ) -> None:
        self.rsi_period = rsi_period
        self.sma_short = sma_short
        self.sma_long = sma_long
        self.boll_period = boll_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.kdj_period = kdj_period
        self.kdj_smooth = kdj_smooth

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()

        indicators = TechnicalIndicatorsService.calculate_all_indicators(data)
        for name, values in indicators.items():
            data[name] = values

        return data


class ScoringEngine:
    def score_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        score_values = {
            column: [0] * len(data)
            for column in SCORE_COLUMN_BY_INDICATOR.values()
        }

        for position in range(1, len(data)):
            results = score_indicators(
                data.iloc[position],
                data.iloc[position - 1],
            )
            for name, result in results.items():
                score_column = SCORE_COLUMN_BY_INDICATOR[name]
                score_values[score_column][position] = result["score"]

        for column, values in score_values.items():
            data[column] = values

        total_score = data[
            list(SCORE_COLUMN_BY_INDICATOR.values())
        ].sum(axis=1)
        warmup_mask = np.arange(len(data)) < 50
        total_score = total_score.astype(float)
        total_score[warmup_mask] = np.nan
        data["total_score"] = total_score

        return data


class SignalGenerator:
    def generate_signals(
        self,
        df: pd.DataFrame,
        min_score: float = 3.0,
    ) -> pd.DataFrame:
        data = df.copy()
        total_score = data["total_score"]
        triggered = total_score >= min_score
        signal = np.where(triggered, "BUY", None)
        if len(signal) > 0:
            signal[-1] = None
        data["signal"] = signal
        data["entry_price"] = data["open"].shift(-1)
        return data


class TradeSimulator:
    def __init__(
        self,
        max_hold_candles: int,
        exit_on_score_drop: bool = False,
        transaction_cost_pct: float = DEFAULT_TRANSACTION_COST_PCT,
    ) -> None:
        self.max_hold_candles = max_hold_candles
        self.exit_on_score_drop = exit_on_score_drop
        self.transaction_cost_pct = transaction_cost_pct

    def _get_date(self, df: pd.DataFrame, index: int) -> str:
        if "datetime" in df.columns:
            value = df.iloc[index]["datetime"]
        else:
            value = df.index[index]
        return str(pd.to_datetime(value))

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            if value is None:
                return None
            number = float(value)
            if not np.isfinite(number):
                return None
            return number
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_int(value: Any) -> int | None:
        try:
            if value is None:
                return None
            number = int(value)
            return number if number > 0 else None
        except (TypeError, ValueError):
            return None

    def run(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        trades: list[dict[str, Any]] = []
        n = len(df)
        i = 0

        while i < n - 1:
            if df.iloc[i].get("signal") != "BUY":
                i += 1
                continue

            entry_index = i + 1
            signal_row = df.iloc[i]
            entry_price_override = self._to_float(signal_row.get("entry_price_override"))
            entry_price = entry_price_override if entry_price_override is not None else float(df.iloc[entry_index]["open"])
            entry_date = self._get_date(df, entry_index)
            score_at_entry = df.iloc[i].get("total_score")
            confidence = df.iloc[i].get("confidence") if "confidence" in df.columns else None

            stop_loss_override = self._to_float(signal_row.get("stop_loss_price"))
            take_profit_override = self._to_float(signal_row.get("take_profit_price"))
            max_hold_override = self._to_int(signal_row.get("max_hold_candles_override"))
            plan_invalid_at_entry = (
                stop_loss_override is not None
                and stop_loss_override >= entry_price
            ) or (
                take_profit_override is not None
                and take_profit_override <= entry_price
            )
            if plan_invalid_at_entry:
                # The recommendation was built around the signal-candle close.
                # If the next tradable open has already crossed either boundary,
                # the original risk/reward plan is no longer executable.
                i += 1
                continue

            stop_loss_level = stop_loss_override
            take_profit_level = take_profit_override

            exit_index = None
            exit_price = None
            exit_reason = None

            hold_limit = max_hold_override if max_hold_override is not None else self.max_hold_candles
            max_exit_index = min(entry_index + hold_limit - 1, n - 1)
            for j in range(entry_index, max_exit_index + 1):
                low = float(df.iloc[j]["low"])
                high = float(df.iloc[j]["high"])

                if stop_loss_level is not None and low <= stop_loss_level:
                    exit_index = j
                    exit_price = stop_loss_level
                    exit_reason = "STOP_LOSS"
                    break

                if take_profit_level is not None and high >= take_profit_level:
                    exit_index = j
                    exit_price = take_profit_level
                    exit_reason = "TAKE_PROFIT"
                    break

                if self.exit_on_score_drop and float(df.iloc[j].get("total_score", 0)) < 3:
                    if j + 1 <= max_exit_index:
                        exit_index = j + 1
                        exit_price = float(df.iloc[j + 1]["open"])
                        exit_reason = "SIGNAL_EXIT"
                        break

            if exit_index is None:
                exit_index = max_exit_index
                exit_price = float(df.iloc[exit_index]["close"])
                exit_reason = "TIMEOUT"

            exit_date = self._get_date(df, exit_index)
            hold_candles = exit_index - entry_index + 1
            gross_return_pct = (exit_price - entry_price) / entry_price
            return_pct = gross_return_pct - 2 * self.transaction_cost_pct

            trade: dict[str, Any] = {
                "entry_date": entry_date,
                "exit_date": exit_date,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "take_profit": take_profit_level,
                "stop_loss": stop_loss_level,
                "return_pct": return_pct,
                "gross_return_pct": gross_return_pct,
                "transaction_cost": 2 * self.transaction_cost_pct,
                "exit_reason": exit_reason,
                "hold_candles": hold_candles,
                "total_score_at_entry": score_at_entry,
            }
            if confidence is not None:
                trade["confidence"] = confidence

            trades.append(trade)
            i = exit_index

        return trades


class MetricsCalculator:
    def calculate(self, trades: list[dict[str, Any]]) -> dict[str, Any]:
        n_trades = len(trades)
        returns = np.array([t["return_pct"] for t in trades], dtype=float) if trades else np.array([])

        n_wins = int((returns > 0).sum()) if trades else 0
        n_losses = int((returns <= 0).sum()) if trades else 0
        win_rate = float(n_wins / n_trades) if n_trades else 0.0

        total_return = float(np.prod(1 + returns) - 1) if trades else 0.0
        avg_return = float(np.mean(returns)) if trades else 0.0
        median_return = float(np.median(returns)) if trades else 0.0
        best_trade = float(np.max(returns)) if trades else 0.0
        worst_trade = float(np.min(returns)) if trades else 0.0

        equity = np.cumprod(1 + returns) if trades else np.array([1.0])
        peak = np.maximum.accumulate(equity)
        drawdown = (equity - peak) / peak
        max_drawdown = float(drawdown.min()) if trades else 0.0

        if n_trades >= 2 and np.std(returns, ddof=1) > 0:
            sharpe_ratio = float(np.sqrt(n_trades) * np.mean(returns) / np.std(returns, ddof=1))
        else:
            sharpe_ratio = 0.0

        annualized_return = 0.0
        if trades:
            try:
                first_date = pd.to_datetime(trades[0]["entry_date"])
                last_date = pd.to_datetime(trades[-1]["exit_date"])
                days = max((last_date - first_date).days, 1)
                annualized_return = float((1 + total_return) ** (365 / days) - 1)
            except Exception:
                annualized_return = total_return

        calmar_ratio = float(annualized_return / abs(max_drawdown)) if max_drawdown < 0 else 0.0

        gross_profit = returns[returns > 0].sum() if trades else 0.0
        gross_loss = returns[returns < 0].sum() if trades else 0.0
        profit_factor = float(gross_profit / abs(gross_loss)) if gross_loss != 0 else 0.0

        exit_breakdown: dict[str, int] = {}
        for trade in trades:
            reason = trade.get("exit_reason", "UNKNOWN")
            exit_breakdown[reason] = exit_breakdown.get(reason, 0) + 1

        score_at_entry = np.array([t.get("total_score_at_entry") for t in trades], dtype=float) if trades else np.array([])
        avg_score_at_entry = float(np.nanmean(score_at_entry)) if trades else 0.0
        score_win_rate: dict[int, float] = {}
        for score in [3, 4, 5]:
            mask = score_at_entry == score
            if mask.any():
                score_win_rate[score] = float((returns[mask] > 0).mean())
            else:
                score_win_rate[score] = 0.0

        information_coefficient = 0.0
        if trades and len(score_at_entry) >= 2 and np.std(score_at_entry) > 0:
            information_coefficient = float(np.corrcoef(score_at_entry, returns)[0, 1])

        warning = "Không đủ trades" if n_trades < 30 else ""

        return {
            "volume": {
                "n_trades": n_trades,
                "n_wins": n_wins,
                "n_losses": n_losses,
                "win_rate": win_rate,
            },
            "pnl": {
                "total_return": total_return,
                "avg_return": avg_return,
                "median_return": median_return,
                "best_trade": best_trade,
                "worst_trade": worst_trade,
                "annualized_return": annualized_return,
            },
            "risk": {
                "max_drawdown": max_drawdown,
                "sharpe_ratio": sharpe_ratio,
                "calmar_ratio": calmar_ratio,
                "profit_factor": profit_factor,
            },
            "exit_breakdown": exit_breakdown,
            "signal_quality": {
                "avg_score_at_entry": avg_score_at_entry,
                "score_win_rate": score_win_rate,
                "information_coefficient": information_coefficient,
            },
            "warning": warning,
        }
