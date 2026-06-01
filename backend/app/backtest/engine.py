from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd


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

        close = data["close"].astype(float)
        high = data["high"].astype(float)
        low = data["low"].astype(float)

        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / self.rsi_period, adjust=False, min_periods=self.rsi_period).mean()
        avg_loss = loss.ewm(alpha=1 / self.rsi_period, adjust=False, min_periods=self.rsi_period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        data["rsi_14"] = 100 - (100 / (1 + rs))

        data["sma_20"] = close.rolling(self.sma_short, min_periods=self.sma_short).mean()
        data["sma_50"] = close.rolling(self.sma_long, min_periods=self.sma_long).mean()

        bb_middle = close.rolling(self.boll_period, min_periods=self.boll_period).mean()
        bb_std = close.rolling(self.boll_period, min_periods=self.boll_period).std()
        data["bb_middle"] = bb_middle
        data["bb_upper"] = bb_middle + 2 * bb_std
        data["bb_lower"] = bb_middle - 2 * bb_std

        ema_fast = close.ewm(span=self.macd_fast, adjust=False, min_periods=self.macd_fast).mean()
        ema_slow = close.ewm(span=self.macd_slow, adjust=False, min_periods=self.macd_slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=self.macd_signal, adjust=False, min_periods=self.macd_signal).mean()
        data["macd"] = macd
        data["macd_signal"] = macd_signal
        data["macd_histogram"] = macd - macd_signal

        low_min = low.rolling(self.kdj_period, min_periods=self.kdj_period).min()
        high_max = high.rolling(self.kdj_period, min_periods=self.kdj_period).max()
        denom = (high_max - low_min).replace(0, np.nan)
        rsv = (close - low_min) / denom * 100
        k = rsv.rolling(self.kdj_smooth, min_periods=self.kdj_smooth).mean()
        d = k.rolling(self.kdj_smooth, min_periods=self.kdj_smooth).mean()
        data["kdj_k"] = k
        data["kdj_d"] = d
        data["kdj_j"] = 3 * k - 2 * d

        return data


class ScoringEngine:
    def _score_rsi(self, current: float | None, previous: float | None) -> tuple[int, str]:
        """
        1 điểm nếu thỏa MỘT trong 3 điều kiện (ưu tiên theo thứ tự):
          1. RSI vừa vượt 50 từ dưới lên (kỳ trước < 50, kỳ này >= 50)
          2. 50 <= RSI <= 70 VÀ RSI kỳ này > RSI kỳ trước
          3. RSI < 35 VÀ RSI kỳ này > RSI kỳ trước
        0 điểm: mọi trường hợp còn lại
        """
        if current is None or previous is None:
            return 0, "Không đủ dữ liệu RSI"
        if previous < 50 and current >= 50:
            return 1, f"RSI vừa vượt 50 từ dưới lên ({previous:.1f} → {current:.1f})"
        if 50 <= current <= 70 and current > previous:
            return 1, f"RSI trong vùng tăng động lực 50–70 và đang tăng ({previous:.1f} → {current:.1f})"
        if current < 35 and current > previous:
            return 1, f"RSI đang hồi phục từ vùng quá bán ({previous:.1f} → {current:.1f})"
        if current >= 70:
            return 0, f"RSI quá mua ({current:.1f}), rủi ro điều chỉnh"
        if current > previous:
            return 0, f"RSI tăng nhưng trong vùng 35–50, chưa đủ động lực ({previous:.1f} → {current:.1f})"
        return 0, f"RSI đang giảm ({previous:.1f} → {current:.1f})"

    def _score_ma(
        self,
        sma20_current: float | None,
        sma20_previous: float | None,
        sma50_current: float | None,
        sma50_previous: float | None,
        price: float | None,
    ) -> tuple[int, str]:
        """
        1 điểm nếu thỏa BẤT KỲ 1 trong 3 điều kiện:
          1. Golden cross: kỳ trước SMA20 < SMA50, kỳ này SMA20 >= SMA50
          2. SMA20 > SMA50 VÀ khoảng cách đang nới rộng so với kỳ trước
          3. current_price > SMA20 VÀ SMA20 > SMA50
        0 điểm: mọi trường hợp còn lại
        """
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
        self,
        upper: float | None,
        middle: float | None,
        lower: float | None,
        close_current: float | None,
        close_previous: float | None,
        current_price: float | None,
    ) -> tuple[int, str]:
        """
        1 điểm nếu thỏa BẤT KỲ 1 trong 3 điều kiện:
          1. Giá vừa vượt lên trên bb_middle (close kỳ trước < middle, current_price/close kỳ này >= middle)
          2. Giá (close) > bb_middle VÀ (close - middle) kỳ này > (close - middle) kỳ trước
          3. Giá (current_price/close) <= bb_lower VÀ kỳ này > kỳ trước
        0 điểm: mọi trường hợp còn lại
        """
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
        self,
        macd_current: float | None,
        macd_previous: float | None,
        signal_current: float | None,
        signal_previous: float | None,
        hist_current: float | None,
        hist_previous: float | None,
    ) -> tuple[int, str]:
        """
        1 điểm nếu thỏa BẤT KỲ 1 trong 3 điều kiện:
          1. MACD vừa cắt lên Signal (kỳ trước macd < signal, kỳ này macd >= signal)
          2. MACD > Signal VÀ histogram kỳ này > histogram kỳ trước
          3. Histogram vừa chuyển dương (kỳ trước < 0, kỳ này >= 0)
        0 điểm: mọi trường hợp còn lại
        """
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
        self,
        k_current: float | None,
        k_previous: float | None,
        d_current: float | None,
        d_previous: float | None,
        j_current: float | None,
        j_previous: float | None,
    ) -> tuple[int, str]:
        """
        1 điểm nếu thỏa BẤT KỲ 1 trong 3 điều kiện:
          1. K vừa cắt lên D (kỳ trước K < D, kỳ này K >= D)
          2. K > D VÀ J kỳ này > J kỳ trước
          3. K < 20 VÀ K kỳ này > K kỳ trước
        0 điểm: mọi trường hợp còn lại
        """
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

    def score_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()

        rsi = data["rsi_14"]
        rsi_prev = rsi.shift(1)
        rsi_valid = rsi.notna() & rsi_prev.notna()
        rsi_score = np.select(
            [
                rsi_valid & (rsi_prev < 50) & (rsi >= 50),
                rsi_valid & (rsi >= 50) & (rsi <= 70) & (rsi > rsi_prev),
                rsi_valid & (rsi < 35) & (rsi > rsi_prev),
            ],
            [1, 1, 1],
            default=0,
        )
        data["rsi_score"] = rsi_score

        sma20 = data["sma_20"]
        sma50 = data["sma_50"]
        sma20_prev = sma20.shift(1)
        sma50_prev = sma50.shift(1)
        price = data["close"]
        ma_valid = sma20.notna() & sma50.notna()
        gap_current = sma20 - sma50
        gap_previous = sma20_prev - sma50_prev
        ma_score = np.select(
            [
                ma_valid
                & sma20_prev.notna()
                & sma50_prev.notna()
                & (sma20_prev < sma50_prev)
                & (sma20 >= sma50),
                ma_valid
                & sma20_prev.notna()
                & sma50_prev.notna()
                & (sma20 > sma50)
                & (gap_current > gap_previous),
                ma_valid & price.notna() & (sma20 > sma50) & (price > sma20),
            ],
            [1, 1, 1],
            default=0,
        )
        data["ma_score"] = ma_score

        bb_upper = data["bb_upper"]
        bb_middle = data["bb_middle"]
        bb_lower = data["bb_lower"]
        close_current = data["close"]
        close_previous = close_current.shift(1)
        price_now = close_current
        boll_valid = bb_upper.notna() & bb_middle.notna() & bb_lower.notna() & price_now.notna() & close_previous.notna()
        gap_current = close_current - bb_middle
        gap_previous = close_previous - bb_middle
        boll_score = np.select(
            [
                boll_valid & (close_previous < bb_middle) & (price_now >= bb_middle),
                boll_valid & close_current.notna() & (close_current > bb_middle) & (gap_current > gap_previous),
                boll_valid & (price_now <= bb_lower) & (price_now > close_previous),
            ],
            [1, 1, 1],
            default=0,
        )
        data["boll_score"] = boll_score

        macd = data["macd"]
        signal = data["macd_signal"]
        hist = data["macd_histogram"]
        macd_prev = macd.shift(1)
        signal_prev = signal.shift(1)
        hist_prev = hist.shift(1)
        macd_valid = macd.notna() & signal.notna() & hist.notna()
        macd_score = np.select(
            [
                macd_valid
                & macd_prev.notna()
                & signal_prev.notna()
                & (macd_prev < signal_prev)
                & (macd >= signal),
                macd_valid & hist_prev.notna() & (macd > signal) & (hist > hist_prev),
                macd_valid & hist_prev.notna() & (hist_prev < 0) & (hist >= 0),
            ],
            [1, 1, 1],
            default=0,
        )
        data["macd_score"] = macd_score

        k = data["kdj_k"]
        d = data["kdj_d"]
        j = data["kdj_j"]
        k_prev = k.shift(1)
        d_prev = d.shift(1)
        j_prev = j.shift(1)
        kdj_valid = k.notna() & d.notna() & j.notna()
        kdj_score = np.select(
            [
                kdj_valid & k_prev.notna() & d_prev.notna() & (k_prev < d_prev) & (k >= d),
                kdj_valid & j_prev.notna() & (k > d) & (j > j_prev),
                kdj_valid & k_prev.notna() & (k < 20) & (k > k_prev),
            ],
            [1, 1, 1],
            default=0,
        )
        data["kdj_score"] = kdj_score

        total_score = data[["rsi_score", "ma_score", "boll_score", "macd_score", "kdj_score"]].sum(axis=1)
        warmup_mask = np.arange(len(data)) < 50
        total_score = total_score.astype(float)
        total_score[warmup_mask] = np.nan
        data["total_score"] = total_score

        return data


class SignalGenerator:
    def generate_signals(self, df: pd.DataFrame, min_score: int = 3) -> pd.DataFrame:
        data = df.copy()
        total_score = data["total_score"]
        triggered = (total_score >= min_score) & (total_score.shift(1) < min_score)
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
    ) -> None:
        self.max_hold_candles = max_hold_candles
        self.exit_on_score_drop = exit_on_score_drop

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
            if stop_loss_override is not None and stop_loss_override >= entry_price:
                stop_loss_override = None
            if take_profit_override is not None and take_profit_override <= entry_price:
                take_profit_override = None

            stop_loss_level = stop_loss_override
            take_profit_level = take_profit_override

            exit_index = None
            exit_price = None
            exit_reason = None

            hold_limit = max_hold_override if max_hold_override is not None else self.max_hold_candles
            max_exit_index = min(entry_index + hold_limit, n - 1)
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
                    if j + 1 < n:
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
            return_pct = (exit_price - entry_price) / entry_price

            trade: dict[str, Any] = {
                "entry_date": entry_date,
                "exit_date": exit_date,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "return_pct": return_pct,
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
