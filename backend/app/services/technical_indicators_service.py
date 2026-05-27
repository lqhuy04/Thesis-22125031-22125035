"""
Technical Indicators Service
Calculates technical analysis indicators using pure numpy/pandas (no TA-Lib)
"""
import numpy as np
import pandas as pd
from typing import Dict, Any
import math


class TechnicalIndicatorsService:
    """Service for calculating technical indicators without TA-Lib"""

    @staticmethod
    def _sanitize_indicators(indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Replace NaN/inf with None for JSON compliance"""
        sanitized = {}
        for key, values in indicators.items():
            if isinstance(values, list):
                sanitized[key] = [
                    None if (v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))))
                    else round(v, 4)
                    for v in values
                ]
            else:
                sanitized[key] = values
        return sanitized

    # ------------------------------------------------------------------ #
    #  Internal calculation helpers                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _sma(series: np.ndarray, period: int) -> np.ndarray:
        """Simple Moving Average"""
        result = np.full(len(series), np.nan)
        for i in range(period - 1, len(series)):
            result[i] = series[i - period + 1 : i + 1].mean()
        return result

    @staticmethod
    def _ema(series: np.ndarray, period: int) -> np.ndarray:
        """
        Exponential Moving Average
        Uses the same 'SMA seed' approach as TA-Lib:
        - First value = SMA of the first `period` bars
        - Subsequent values use multiplier k = 2 / (period + 1)
        """
        result = np.full(len(series), np.nan)
        if len(series) < period:
            return result

        k = 2.0 / (period + 1)
        # Seed with the first SMA
        result[period - 1] = series[:period].mean()
        for i in range(period, len(series)):
            result[i] = series[i] * k + result[i - 1] * (1 - k)
        return result

    @staticmethod
    def _rsi(close: np.ndarray, period: int = 14) -> np.ndarray:
        """
        RSI — Wilder's Smoothed Moving Average method (identical to TA-Lib)
        """
        result = np.full(len(close), np.nan)
        if len(close) <= period:
            return result

        deltas = np.diff(close)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)

        # First average gain/loss = SMA of first `period` deltas
        avg_gain = gains[:period].mean()
        avg_loss = losses[:period].mean()

        idx = period  # result index (offset by 1 because of np.diff)
        if avg_loss == 0:
            result[idx] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[idx] = 100.0 - 100.0 / (1 + rs)

        # Wilder smoothing for subsequent bars
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            if avg_loss == 0:
                result[i + 1] = 100.0
            else:
                rs = avg_gain / avg_loss
                result[i + 1] = 100.0 - 100.0 / (1 + rs)

        return result

    @staticmethod
    def _macd(
        close: np.ndarray,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ):
        """
        MACD = EMA(fast) - EMA(slow)
        Signal = EMA(MACD, signal)
        Histogram = MACD - Signal
        Returns (macd, signal_line, histogram)
        """
        ema_fast = TechnicalIndicatorsService._ema(close, fast)
        ema_slow = TechnicalIndicatorsService._ema(close, slow)

        macd_line = ema_fast - ema_slow  # NaN where either EMA is NaN

        # Signal EMA is seeded from the first valid MACD value
        signal_line = np.full(len(close), np.nan)
        first_valid = np.where(~np.isnan(macd_line))[0]
        if len(first_valid) == 0:
            return macd_line, signal_line, macd_line - signal_line

        start = first_valid[0]
        valid_macd = macd_line[start:]

        if len(valid_macd) < signal:
            return macd_line, signal_line, macd_line - signal_line

        k = 2.0 / (signal + 1)
        sig = np.full(len(valid_macd), np.nan)
        sig[signal - 1] = valid_macd[:signal].mean()
        for i in range(signal, len(valid_macd)):
            sig[i] = valid_macd[i] * k + sig[i - 1] * (1 - k)

        signal_line[start:] = sig
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def _bbands(
        close: np.ndarray,
        period: int = 20,
        nb_dev_up: float = 2.0,
        nb_dev_dn: float = 2.0,
    ):
        """
        Bollinger Bands
        Middle = SMA(period)
        Upper  = Middle + nb_dev_up * std(period, ddof=1)
        Lower  = Middle - nb_dev_dn * std(period, ddof=1)

        Note: TA-Lib uses population std (ddof=0). Pass ddof=0 to match TA-Lib exactly.
        Most charting apps (SSI, TradingView) display population std → use ddof=0.
        """
        n = len(close)
        middle = np.full(n, np.nan)
        upper = np.full(n, np.nan)
        lower = np.full(n, np.nan)

        for i in range(period - 1, n):
            window = close[i - period + 1 : i + 1]
            m = window.mean()
            # ddof=0 → population std (matches TA-Lib / SSI)
            s = window.std(ddof=0)
            middle[i] = m
            upper[i] = m + nb_dev_up * s
            lower[i] = m - nb_dev_dn * s

        return upper, middle, lower

    @staticmethod
    def _kdj(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        fastk_period: int = 9,
        signal_period: int = 3,
    ):
        n = len(close)
        raw_k = np.full(n, np.nan)

        for i in range(fastk_period - 1, n):
            h = high[i - fastk_period + 1 : i + 1].max()
            l = low[i - fastk_period + 1 : i + 1].min()
            if h == l:
                raw_k[i] = 50.0
            else:
                raw_k[i] = (close[i] - l) / (h - l) * 100.0

        # ✅ Wilder's smoothing: multiplier = 1/period (khớp SSI)
        multiplier = 1.0 / signal_period

        k_line = np.full(n, np.nan)
        d_line = np.full(n, np.nan)

        first = np.where(~np.isnan(raw_k))[0]
        if len(first) == 0:
            return k_line, d_line, 3 * k_line - 2 * d_line

        # Seed K bằng giá trị raw_k đầu tiên (50 nếu không đủ dữ liệu)
        # Một số app seed = 50, một số seed = raw_k đầu tiên
        # SSI thường seed = 50
        k_line[first[0]] = 50.0
        d_line[first[0]] = 50.0

        for i in range(first[0] + 1, n):
            if np.isnan(raw_k[i]):
                continue
            k_line[i] = raw_k[i] * multiplier + k_line[i - 1] * (1 - multiplier)
            d_line[i] = k_line[i] * multiplier + d_line[i - 1] * (1 - multiplier)

        j_line = 3 * k_line - 2 * d_line
        return k_line, d_line, j_line

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate technical indicators (pure numpy/pandas, no TA-Lib)

        Args:
            df: DataFrame with columns [open, high, low, close, volume]

        Returns:
            Dictionary containing all calculated indicators
        """
        if df.empty:
            raise ValueError("Insufficient data for indicator calculation (no data points)")
        if len(df) < 50:
            raise ValueError("Insufficient data for indicator calculation (need at least 50 bars)")

        open_prices  = np.array(df['open'].values,   dtype=np.float64)
        high_prices  = np.array(df['high'].values,   dtype=np.float64)
        low_prices   = np.array(df['low'].values,    dtype=np.float64)
        close_prices = np.array(df['close'].values,  dtype=np.float64)
        volume       = np.array(df['volume'].values, dtype=np.float64)

        for name, arr in [
            ('open',   open_prices),
            ('high',   high_prices),
            ('low',    low_prices),
            ('close',  close_prices),
            ('volume', volume),
        ]:
            if np.any(np.isnan(arr)):
                raise ValueError(f"'{name}' contains NaN values. Please check your data.")
            if np.any(np.isinf(arr)):
                raise ValueError(f"'{name}' contains infinite values. Please check your data.")

        indicators: Dict[str, Any] = {}

        try:
            # 1. SMA
            indicators['sma_20'] = TechnicalIndicatorsService._sma(close_prices, 20).tolist()
            indicators['sma_50'] = TechnicalIndicatorsService._sma(close_prices, 50).tolist()

            # 2. RSI
            indicators['rsi_14'] = TechnicalIndicatorsService._rsi(close_prices, 14).tolist()

            # 3. MACD
            macd, macd_signal, macd_hist = TechnicalIndicatorsService._macd(
                close_prices, fast=12, slow=26, signal=9
            )
            indicators['macd']           = macd.tolist()
            indicators['macd_signal']    = macd_signal.tolist()
            indicators['macd_histogram'] = macd_hist.tolist()

            # 4. Bollinger Bands
            bb_upper, bb_middle, bb_lower = TechnicalIndicatorsService._bbands(
                close_prices, period=20, nb_dev_up=2.0, nb_dev_dn=2.0
            )
            indicators['bb_upper']  = bb_upper.tolist()
            indicators['bb_middle'] = bb_middle.tolist()
            indicators['bb_lower']  = bb_lower.tolist()

            # 5. KDJ
            k, d, j = TechnicalIndicatorsService._kdj(
                high_prices, low_prices, close_prices,
                fastk_period=9, signal_period=3
            )
            indicators['kdj_k'] = k.tolist()
            indicators['kdj_d'] = d.tolist()
            indicators['kdj_j'] = j.tolist()

            # 6. Volume MA
            indicators['volume_ma_20'] = TechnicalIndicatorsService._sma(volume, 20).tolist()
            indicators['volume_ma_50'] = TechnicalIndicatorsService._sma(volume, 50).tolist()

            return TechnicalIndicatorsService._sanitize_indicators(indicators)

        except Exception as e:
            raise ValueError(f"Error calculating indicators: {str(e)}")