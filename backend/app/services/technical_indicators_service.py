"""
Technical Indicators Service
Calculates technical analysis indicators using TA-Lib
"""
import talib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from app.services.ssi_service import get_ssi_service


class TechnicalIndicatorsService:
    """Service for calculating technical indicators"""
    
    @staticmethod
    async def fetch_ohlc_data(
        symbol: str,
        from_date: str,
        to_date: str,
        timeframe: str = "1D",
        resolution: Optional[int] = None,
        page_size: int = 1000
    ) -> pd.DataFrame:
        """
        Fetch OHLC data and convert to pandas DataFrame
        
        Args:
            symbol: Stock symbol
            from_date: Start date (DD/MM/YYYY)
            to_date: End date (DD/MM/YYYY)
            timeframe: Timeframe for data ('1D' for daily, 'intraday' for intraday)
            resolution: Resolution in minutes for intraday (1, 5, 15, 30, 60)
            page_size: Number of records to fetch
            
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        try:
            service = get_ssi_service()
            
            # Determine if intraday or daily
            if timeframe.lower() == 'intraday' and resolution:
                # Fetch intraday data
                result = service.get_intraday_ohlc(
                    symbol.lower(),
                    from_date,
                    to_date,
                    page_index=1,
                    page_size=page_size,
                    ascending=True,
                    resolution=resolution
                )
            else:
                # Fetch daily data (default)
                result = service.get_daily_ohlc(
                    symbol.lower(),
                    from_date,
                    to_date,
                    page_index=1,
                    page_size=page_size,
                    ascending=True
                )
            
            # Check if API call was successful
            if not result.get("success"):
                error_msg = result.get("error", "Unknown API error")
                raise ValueError(f"API request failed: {error_msg}")
            
            data = result.get("data")
            if not data:
                raise ValueError(
                    f"No data returned from API for {symbol}. "
                    f"Check if the symbol is valid and the date range has trading data."
                )
            
            # Handle nested response structure
            # The SSI API returns: {"success": True, "data": {"data": [...], "message": ..., "status": ...}}
            if isinstance(data, dict) and "data" in data:
                # Extract the actual data array from nested structure
                actual_data = data.get("data")
                if not actual_data:
                    raise ValueError(
                        f"No OHLC records found for {symbol}. "
                        f"The API returned: {data}"
                    )
                data = actual_data
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            if df.empty:
                raise ValueError(
                    f"Empty dataset for {symbol}. "
                    f"Check if the symbol is valid and the date range contains trading days."
                )
            
            # Map various possible column names to standardized names
            # Priority order: prefer more specific names first
            column_mapping = {
                # Date columns (in priority order)
                'tradingDate': 'date',
                'TradingDate': 'date',
                'time': 'date',
                'Time': 'date',
                'date': 'date',
                'Date': 'date',
                # OHLC columns
                'openPrice': 'open',
                'open': 'open',
                'Open': 'open',
                'highPrice': 'high',
                'high': 'high',
                'High': 'high',
                'lowPrice': 'low',
                'low': 'low',
                'Low': 'low',
                'closePrice': 'close',
                'close': 'close',
                'Close': 'close',
                # Volume columns
                'totalVolume': 'volume',
                'TotalVolume': 'volume',
                'volume': 'volume',
                'Volume': 'volume'
            }
            
            # Smart mapping: only map the first occurrence of each target column
            existing_mapping = {}
            mapped_targets = set()
            
            for col in df.columns:
                if col in column_mapping:
                    target = column_mapping[col]
                    # Only map if we haven't already mapped to this target
                    if target not in mapped_targets:
                        existing_mapping[col] = target
                        mapped_targets.add(target)
            
            # Rename columns that exist
            if existing_mapping:
                df = df.rename(columns=existing_mapping)
            
            # Drop any remaining duplicate columns (shouldn't happen, but just in case)
            df = df.loc[:, ~df.columns.duplicated()]
            
            # Check if we have the required columns after mapping
            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                available_cols = list(df.columns)
                raise ValueError(
                    f"OHLC data missing required columns: {missing_cols}. "
                    f"Available columns: {available_cols}"
                )
            
            # Convert data types to numeric
            df['open'] = pd.to_numeric(df['open'], errors='coerce')
            df['high'] = pd.to_numeric(df['high'], errors='coerce')
            df['low'] = pd.to_numeric(df['low'], errors='coerce')
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
            
            # Drop rows with NaN values in critical columns
            df = df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])
            
            if df.empty:
                raise ValueError("No valid data after removing rows with missing values")
            
            # Sort by date
            df = df.sort_values('date')
            df = df.reset_index(drop=True)
            
            return df
            
        except Exception as e:
            raise ValueError(f"Error fetching OHLC data: {str(e)}")
    
    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate top 20 technical indicators
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Dictionary containing all calculated indicators
        """
        if df.empty or len(df) < 50:
            raise ValueError("Insufficient data for indicator calculation (minimum 50 data points required)")
        
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
            indicators['sma_10'] = talib.SMA(close_prices, timeperiod=10).tolist()
            indicators['sma_20'] = talib.SMA(close_prices, timeperiod=20).tolist()
            indicators['sma_50'] = talib.SMA(close_prices, timeperiod=50).tolist()
            
            # 2. Exponential Moving Averages (EMA)
            indicators['ema_12'] = talib.EMA(close_prices, timeperiod=12).tolist()
            indicators['ema_26'] = talib.EMA(close_prices, timeperiod=26).tolist()
            indicators['ema_50'] = talib.EMA(close_prices, timeperiod=50).tolist()
            
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
            
            # 6. Stochastic Oscillator
            slowk, slowd = talib.STOCH(
                high_prices,
                low_prices,
                close_prices,
                fastk_period=14,
                slowk_period=3,
                slowk_matype=0,
                slowd_period=3,
                slowd_matype=0
            )
            indicators['stoch_k'] = slowk.tolist()
            indicators['stoch_d'] = slowd.tolist()
            
            # 7. ATR (Average True Range)
            indicators['atr_14'] = talib.ATR(
                high_prices,
                low_prices,
                close_prices,
                timeperiod=14
            ).tolist()
            
            # 8. ADX (Average Directional Index)
            indicators['adx_14'] = talib.ADX(
                high_prices,
                low_prices,
                close_prices,
                timeperiod=14
            ).tolist()
            
            # 9. CCI (Commodity Channel Index)
            indicators['cci_14'] = talib.CCI(
                high_prices,
                low_prices,
                close_prices,
                timeperiod=14
            ).tolist()
            
            # 10. Williams %R
            indicators['willr_14'] = talib.WILLR(
                high_prices,
                low_prices,
                close_prices,
                timeperiod=14
            ).tolist()
            
            # 11. MFI (Money Flow Index)
            indicators['mfi_14'] = talib.MFI(
                high_prices,
                low_prices,
                close_prices,
                volume,
                timeperiod=14
            ).tolist()
            
            # 12. OBV (On Balance Volume)
            indicators['obv'] = talib.OBV(close_prices, volume).tolist()
            
            # 13. Parabolic SAR
            indicators['sar'] = talib.SAR(
                high_prices,
                low_prices,
                acceleration=0.02,
                maximum=0.2
            ).tolist()
            
            # 14. ROC (Rate of Change)
            indicators['roc_10'] = talib.ROC(close_prices, timeperiod=10).tolist()
            
            # 15. Momentum
            indicators['mom_10'] = talib.MOM(close_prices, timeperiod=10).tolist()
            
            # 16. TRIX (Triple Exponential Average)
            indicators['trix_15'] = talib.TRIX(close_prices, timeperiod=15).tolist()
            
            # 17. Aroon
            aroon_down, aroon_up = talib.AROON(
                high_prices,
                low_prices,
                timeperiod=14
            )
            indicators['aroon_up'] = aroon_up.tolist()
            indicators['aroon_down'] = aroon_down.tolist()
            
            # 18. Balance of Power
            indicators['bop'] = talib.BOP(
                open_prices,
                high_prices,
                low_prices,
                close_prices
            ).tolist()
            
            # 19. CMO (Chande Momentum Oscillator)
            indicators['cmo_14'] = talib.CMO(close_prices, timeperiod=14).tolist()
            
            # 20. TEMA (Triple Exponential Moving Average)
            indicators['tema_30'] = talib.TEMA(close_prices, timeperiod=30).tolist()
            
            # Add metadata
            indicators['dates'] = df['date'].tolist()
            indicators['close_prices'] = close_prices.tolist()
            
            return indicators
            
        except Exception as e:
            raise ValueError(f"Error calculating indicators: {str(e)}")
    
    @staticmethod
    def get_latest_indicator_values(indicators: Dict[str, Any]) -> Dict[str, Optional[float]]:
        """
        Extract the latest (most recent) values from all indicators
        
        Args:
            indicators: Dictionary of calculated indicators
            
        Returns:
            Dictionary with latest value for each indicator
        """
        latest_values = {}
        
        for key, value_list in indicators.items():
            if key in ['dates', 'close_prices']:
                latest_values[key] = value_list[-1] if value_list else None
            elif isinstance(value_list, list) and len(value_list) > 0:
                # Get the last non-NaN value
                for val in reversed(value_list):
                    if val is not None and not (isinstance(val, float) and np.isnan(val)):
                        latest_values[key] = round(val, 4) if isinstance(val, (int, float)) else val
                        break
                else:
                    latest_values[key] = None
            else:
                latest_values[key] = None
        
        return latest_values
    
    @staticmethod
    def generate_signals(indicators: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate trading signals based on indicator values
        
        Args:
            indicators: Dictionary with latest indicator values
            
        Returns:
            Dictionary with signals for each indicator
        """
        signals = {}
        
        # RSI signals
        rsi = indicators.get('rsi_14')
        if rsi is not None:
            if rsi < 30:
                signals['rsi_signal'] = 'Oversold - Potential BUY'
            elif rsi > 70:
                signals['rsi_signal'] = 'Overbought - Potential SELL'
            else:
                signals['rsi_signal'] = 'Neutral'
        
        # MACD signals
        macd = indicators.get('macd')
        macd_signal = indicators.get('macd_signal')
        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                signals['macd_signal'] = 'Bullish - BUY'
            else:
                signals['macd_signal'] = 'Bearish - SELL'
        
        # Stochastic signals
        stoch_k = indicators.get('stoch_k')
        stoch_d = indicators.get('stoch_d')
        if stoch_k is not None and stoch_d is not None:
            if stoch_k < 20 and stoch_d < 20:
                signals['stoch_signal'] = 'Oversold - Potential BUY'
            elif stoch_k > 80 and stoch_d > 80:
                signals['stoch_signal'] = 'Overbought - Potential SELL'
            else:
                signals['stoch_signal'] = 'Neutral'
        
        # ADX signals
        adx = indicators.get('adx_14')
        if adx is not None:
            if adx > 25:
                signals['adx_signal'] = 'Strong Trend'
            elif adx > 20:
                signals['adx_signal'] = 'Moderate Trend'
            else:
                signals['adx_signal'] = 'Weak Trend'
        
        # Williams %R signals
        willr = indicators.get('willr_14')
        if willr is not None:
            if willr < -80:
                signals['willr_signal'] = 'Oversold - Potential BUY'
            elif willr > -20:
                signals['willr_signal'] = 'Overbought - Potential SELL'
            else:
                signals['willr_signal'] = 'Neutral'
        
        # CCI signals
        cci = indicators.get('cci_14')
        if cci is not None:
            if cci < -100:
                signals['cci_signal'] = 'Oversold - Potential BUY'
            elif cci > 100:
                signals['cci_signal'] = 'Overbought - Potential SELL'
            else:
                signals['cci_signal'] = 'Neutral'
        
        return signals
