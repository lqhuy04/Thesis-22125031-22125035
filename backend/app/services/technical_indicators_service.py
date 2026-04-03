"""
Technical Indicators Service
Calculates technical analysis indicators using TA-Lib
"""
import asyncio
import talib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
import math


class TechnicalIndicatorsService:
    """Service for calculating technical indicators"""

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
    
    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate technical indicators
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Dictionary containing all calculated indicators
        """
        if df.empty:
            raise ValueError("Insufficient data for indicator calculation (no data points)")

        if len(df) < 50:
            raise ValueError("Insufficient data for indicator calculation (no data points)")
        
        # Extract price arrays and convert to float64 (required by TA-Lib)
        # TA-Lib requires numpy arrays of type float64 (double)
        open_prices = np.array(df['open'].values, dtype=np.float64)
        high_prices = np.array(df['high'].values, dtype=np.float64)
        low_prices = np.array(df['low'].values, dtype=np.float64)
        close_prices = np.array(df['close'].values, dtype=np.float64)
        volume = np.array(df['volume'].values, dtype=np.float64)
        
        # Validate that arrays don't contain NaN or inf
        for name, arr in [('open', open_prices), ('high', high_prices), 
                          ('low', low_prices), ('close', close_prices), ('volume', volume)]:
            if np.any(np.isnan(arr)):
                raise ValueError(f"'{name}' prices contain NaN values. Please check your data.")
            if np.any(np.isinf(arr)):
                raise ValueError(f"'{name}' prices contain infinite values. Please check your data.")
        
        indicators = {}
        
        try:
            # 1. Simple Moving Averages (SMA)
            indicators['sma_20'] = talib.SMA(close_prices, timeperiod=20).tolist()
            indicators['sma_50'] = talib.SMA(close_prices, timeperiod=50).tolist()

            # 3. RSI (Relative Strength Index)
            indicators['rsi_14'] = talib.RSI(close_prices, timeperiod=14).tolist()
            
            # 4. MACD (Moving Average Convergence Divergence)
            macd, macd_signal, macd_hist = talib.MACD(
                close_prices,
                fastperiod=12,
                slowperiod=26,
                signalperiod=9
            )
            indicators['macd'] = macd.tolist()
            indicators['macd_signal'] = macd_signal.tolist()
            indicators['macd_histogram'] = macd_hist.tolist()
            
            # 5. Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(
                close_prices,
                timeperiod=20,
                nbdevup=2,
                nbdevdn=2,
                matype=0
            )
            indicators['bb_upper'] = bb_upper.tolist()
            indicators['bb_middle'] = bb_middle.tolist()
            indicators['bb_lower'] = bb_lower.tolist()
            
            slowk, slowd = talib.STOCH(
                high_prices,
                low_prices,
                close_prices,
                fastk_period=9,
                slowk_period=1,
                slowk_matype=0,
                slowd_period=3,
                slowd_matype=0
            )

            indicators['kdj_k'] = slowk.tolist()
            indicators['kdj_d'] = slowd.tolist()
            indicators['kdj_j'] = (3 * slowk - 2 * slowd).tolist()
            
            return TechnicalIndicatorsService._sanitize_indicators(indicators)
            
        except Exception as e:
            raise ValueError(f"Error calculating indicators: {str(e)}")