"""
Technical Indicators Routes
API endpoints for technical analysis indicators using TA-Lib
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import math
import uuid
import pandas as pd
from app.services.technical_indicators_service import TechnicalIndicatorsService
from app.models.base_schemas import success_response, error_response

router = APIRouter(prefix="/api/technical-indicators", tags=["Technical Indicators"])


@router.get("/{symbol}",
            summary="Calculate Technical Indicators",
            description="Calculate top 20 technical indicators for a stock symbol using TA-Lib")
async def get_technical_indicators(
    symbol: str,
    timeframe: str = Query("1D", description="Timeframe: 1D, 1W, 1M, 1Y, 5Y"),
    from_date: Optional[str] = Query(None, description="Start date (DD/MM/YYYY) - optional, inferred by timeframe"),
    to_date: Optional[str] = Query(None, description="End date (DD/MM/YYYY) - optional, inferred by timeframe"),
    include_history: bool = Query(True, description="Include full historical data for all indicators"),
    backfill_days: Optional[int] = Query(None, ge=0, le=10, description="Backfill previous days for 1D timeframe to stabilize indicators (auto if omitted)")
):
    """
    Calculate comprehensive technical indicators for a stock
    
    ### Top 20 Indicators Included:
    
    **Trend Indicators:**
    - SMA (10, 20, 50) - Simple Moving Averages
    - EMA (12, 26, 50) - Exponential Moving Averages
    - TEMA (30) - Triple Exponential Moving Average
    - SAR - Parabolic SAR
    
    **Momentum Indicators:**
    - RSI (14) - Relative Strength Index
    - MACD - Moving Average Convergence Divergence
    - Stochastic (K, D) - Stochastic Oscillator
    - Williams %R (14)
    - ROC (10) - Rate of Change
    - Momentum (10)
    - CMO (14) - Chande Momentum Oscillator
    - CCI (14) - Commodity Channel Index
    
    **Volatility Indicators:**
    - Bollinger Bands (Upper, Middle, Lower)
    - ATR (14) - Average True Range
    
    **Volume Indicators:**
    - OBV - On Balance Volume
    - MFI (14) - Money Flow Index
    
    **Directional Indicators:**
    - ADX (14) - Average Directional Index
    - Aroon (Up, Down)
    - BOP - Balance of Power
    - TRIX (15)
    
    ### Parameters:
    - **symbol**: Stock symbol (e.g., VNM, FPT, VCB)
    - **timeframe**: 1D, 1W, 1M, 1Y, 5Y (default: 1D)
    - **from_date**: Optional start date (DD/MM/YYYY). If omitted, inferred from timeframe
    - **to_date**: Optional end date (DD/MM/YYYY). If omitted, inferred from timeframe
    - **include_history**: If true, returns full time series data. If false (default), returns only latest values
    
    ### Timeframe Examples:
    - Daily: `timeframe=1D` (default)
    - Weekly: `timeframe=1W`
    - Monthly: `timeframe=1M`
    - Yearly: `timeframe=1Y`
    - 5 Years: `timeframe=5Y`
    
    ### Response:
    Returns all indicator values with trading signals and interpretations
    """
    request_id = str(uuid.uuid4())
    
    try:
        # Validate symbol
        if not symbol or len(symbol) > 10:
            raise HTTPException(
                status_code=400,
                detail="Invalid symbol format"
            )
        
        # Validate timeframe
        if timeframe not in {"1D", "1W", "1M", "1Y", "5Y"}:
            raise HTTPException(
                status_code=400,
                detail="Invalid timeframe. Valid values: 1D, 1W, 1M, 1Y, 5Y"
            )
        
        # Fetch OHLC data for the requested timeframe
        df = await TechnicalIndicatorsService.fetch_ohlc_data(
            symbol=symbol.upper(),
            from_date=from_date,
            to_date=to_date,
            timeframe=timeframe,
            resolution=None
        )
        
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No OHLC data found for symbol: {symbol}"
            )
        
        # Optionally backfill 1D with previous days for indicator calculation only
        df_for_calc = df
        target_day_str = None
        auto_backfill_days = 0
        required_points_for_indicators = 50
        backfill_from = None
        backfill_to = None
        required_indicators = {
            "sma_20", "sma_50",
            "bb_upper", "bb_middle", "bb_lower",
            "volume",
            "macd", "macd_signal", "macd_histogram",
            "rsi_14",
            "stoch_k", "stoch_d",
        }

        if timeframe == "1D" and len(df) < 50:
            now = datetime.now()
            target_day = now - timedelta(days=1) if (now.hour, now.minute) < (9, 15) else now
            target_day_str = target_day.strftime("%d/%m/%Y")

            # 09:15-11:15 (9 points) + 13:00-14:45 (8 points) -> 17 points/day
            expected_points_per_day = 17
            day_points = len(df[df["date"] == target_day_str])
            points_per_day = day_points if day_points > 0 else expected_points_per_day

            if backfill_days is None:
                missing = max(0, required_points_for_indicators - day_points)
                auto_backfill_days = math.ceil(missing / points_per_day) if points_per_day else 0
            else:
                auto_backfill_days = backfill_days

            if auto_backfill_days > 0:
                max_backfill_days = 10
                while True:
                    backfill_from = (target_day - timedelta(days=auto_backfill_days)).strftime("%d/%m/%Y")
                    backfill_to = target_day.strftime("%d/%m/%Y")

                    df_for_calc = await TechnicalIndicatorsService.fetch_ohlc_data(
                        symbol=symbol.upper(),
                        from_date=backfill_from,
                        to_date=backfill_to,
                        timeframe="intraday",
                        resolution=15
                    )

                    if len(df_for_calc) >= required_points_for_indicators:
                        indicators_for_calc = TechnicalIndicatorsService.calculate_all_indicators(df_for_calc)
                        series_points = TechnicalIndicatorsService.build_series_points(df_for_calc, indicators_for_calc)
                        series_points = [
                            point for point in series_points
                            if point.get("date") == target_day_str
                        ]
                        if series_points:
                            first_indicators = series_points[0].get("indicators", {})
                            if all(first_indicators.get(key) is not None for key in required_indicators):
                                break

                    if auto_backfill_days >= max_backfill_days:
                        break

                    auto_backfill_days += 1

        # Calculate indicators for series (requested interval) and for latest (optional backfill)
        indicators_for_series = TechnicalIndicatorsService.calculate_all_indicators(df)
        indicators_for_latest = indicators_for_series
        indicators_for_calc = None
        if df_for_calc is not df:
            indicators_for_calc = TechnicalIndicatorsService.calculate_all_indicators(df_for_calc)
            indicators_for_latest = indicators_for_calc
        
        # Prepare response based on include_history flag
        latest_indicators = TechnicalIndicatorsService.get_latest_indicator_values(indicators_for_latest)
        signals = TechnicalIndicatorsService.generate_signals(latest_indicators)

        allowed_indicators = {
            "sma_20", "sma_50",
            "bb_upper", "bb_middle", "bb_lower",
            "volume",
            "macd", "DIF", "DEA",
            "rsi_14",
            "stoch_k", "stoch_d", "stoch_j",
        }

        def _prune_latest(indicators: Dict[str, Any]) -> Dict[str, Any]:
            return {
                key: value
                for key, value in indicators.items()
                if key in allowed_indicators
            }

        def _normalize_series(points: list) -> list:
            # Keep only date/time + indicators to match frontend needs.
            normalized = [
                {
                    "date": point.get("date"),
                    "time": point.get("time"),
                    "indicators": {
                        "sma_20": (point.get("indicators", {}) or {}).get("sma_20"),
                        "sma_50": (point.get("indicators", {}) or {}).get("sma_50"),
                        "bb_upper": (point.get("indicators", {}) or {}).get("bb_upper"),
                        "bb_middle": (point.get("indicators", {}) or {}).get("bb_middle"),
                        "bb_lower": (point.get("indicators", {}) or {}).get("bb_lower"),
                        "volume": (point.get("indicators", {}) or {}).get("volume"),
                        "macd": (point.get("indicators", {}) or {}).get("macd_histogram"),
                        "DIF": (point.get("indicators", {}) or {}).get("macd"),
                        "DEA": (point.get("indicators", {}) or {}).get("macd_signal"),
                        "rsi_14": (point.get("indicators", {}) or {}).get("rsi_14"),
                        "stoch_k": (point.get("indicators", {}) or {}).get("stoch_k"),
                        "stoch_d": (point.get("indicators", {}) or {}).get("stoch_d"),
                        "stoch_j": (
                            (3 * (point.get("indicators", {}) or {}).get("stoch_k")
                             - 2 * (point.get("indicators", {}) or {}).get("stoch_d"))
                            if (point.get("indicators", {}) or {}).get("stoch_k") is not None
                            and (point.get("indicators", {}) or {}).get("stoch_d") is not None
                            else None
                        ),
                    }
                }
                for point in points
            ]

            normalized = [
                {
                    "date": point.get("date"),
                    "time": point.get("time"),
                    "indicators": {
                        key: value
                        for key, value in (point.get("indicators", {}) or {}).items()
                        if key in allowed_indicators
                    }
                }
                for point in normalized
            ]

            # Fill leading MACD nulls with the first available values.
            macd_fields = ["macd", "DIF", "DEA"]
            first_idx = None
            for idx, point in enumerate(normalized):
                indicators = point.get("indicators", {})
                if all(indicators.get(field) is not None for field in macd_fields):
                    first_idx = idx
                    break

            if first_idx is not None:
                first_vals = normalized[first_idx]["indicators"]
                for point in normalized[:first_idx]:
                    for field in macd_fields:
                        point["indicators"][field] = first_vals.get(field)

            return normalized

        if include_history:
            if indicators_for_calc is not None and target_day_str:
                series_points = TechnicalIndicatorsService.build_series_points(df_for_calc, indicators_for_calc)
                series_points = [
                    point for point in series_points
                    if point.get("date") == target_day_str
                ]
                if not series_points:
                    series_points = TechnicalIndicatorsService.build_series_points(df, indicators_for_series)
            else:
                series_points = TechnicalIndicatorsService.build_series_points(df, indicators_for_series)
            series_points = _normalize_series(series_points)
            response_data = {
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "from_date": series_points[0].get("date") if series_points else None,
                "to_date": series_points[-1].get("date") if series_points else None,
                "data_points": len(series_points),
                "series": series_points,
                "signals": signals
            }
        else:
            response_data = {
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "from_date": df['date'].iloc[0] if not df.empty else None,
                "to_date": df['date'].iloc[-1] if not df.empty else None,
                "data_points": len(df),
                "signals": signals
            }
        
        return {
            "data": response_data,
            "errorCode": 0,
            "errorDesc": "",
            "requestId": request_id,
            "result": True
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error in get_technical_indicators: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{symbol}/indicator/{indicator_name}",
            summary="Get Specific Indicator",
            description="Calculate a specific technical indicator")
async def get_specific_indicator(
    symbol: str,
    indicator_name: str,
    timeframe: str = Query("1D", description="Timeframe: 1D, 1W, 1M, 1Y, 5Y"),
    from_date: Optional[str] = Query(None, description="Start date (DD/MM/YYYY) - optional"),
    to_date: Optional[str] = Query(None, description="End date (DD/MM/YYYY) - optional")
):
    """
    Get a specific technical indicator
    
    ### Available Indicators:
    - sma_10, sma_20, sma_50
    - ema_12, ema_26, ema_50
    - rsi_14
    - macd, DIF, DEA, macd_signal, macd_histogram
    - bb_upper, bb_middle, bb_lower
    - stoch_k, stoch_d, stoch_j, J
    - atr_14
    - adx_14
    - cci_14
    - willr_14
    - mfi_14
    - obv
    - sar
    - roc_10
    - mom_10
    - trix_15
    - aroon_up, aroon_down
    - bop
    - cmo_14
    - tema_30
    """
    request_id = str(uuid.uuid4())
    
    try:
        # Validate timeframe
        if timeframe not in {"1D", "1W", "1M", "1Y", "5Y"}:
            raise HTTPException(
                status_code=400,
                detail="Invalid timeframe. Valid values: 1D, 1W, 1M, 1Y, 5Y"
            )
        
        # Fetch and calculate indicators
        df = await TechnicalIndicatorsService.fetch_ohlc_data(
            symbol=symbol.upper(),
            from_date=from_date,
            to_date=to_date,
            timeframe=timeframe,
            resolution=None
        )
        
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No OHLC data found for symbol: {symbol}"
            )
        
        indicators = TechnicalIndicatorsService.calculate_all_indicators(df)

        indicator_aliases = {
            "macd": "macd_histogram",
            "DIF": "macd",
            "DEA": "macd_signal",
            "J": "stoch_j",
            "stoch_j": "stoch_j",
            "kdj_j": "stoch_j",
        }
        requested_indicator = indicator_name.strip()
        internal_indicator = indicator_aliases.get(requested_indicator, requested_indicator)
        
        # Check if indicator exists
        if internal_indicator != "stoch_j" and internal_indicator not in indicators:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid indicator name: {indicator_name}. Use /api/technical-indicators/{symbol} to see all available indicators."
            )
        
        series_points = TechnicalIndicatorsService.build_series_points(df, indicators)
        indicator_series = [
            {
                "date": point.get("date"),
                "time": point.get("time"),
                "value": (
                    (3 * point.get("indicators", {}).get("stoch_k") - 2 * point.get("indicators", {}).get("stoch_d"))
                    if internal_indicator == "stoch_j"
                    and point.get("indicators", {}).get("stoch_k") is not None
                    and point.get("indicators", {}).get("stoch_d") is not None
                    else point.get("indicators", {}).get(internal_indicator)
                )
            }
            for point in series_points
        ]

        return {
            "data": {
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "indicator": requested_indicator,
                "from_date": indicator_series[0].get("date") if indicator_series else None,
                "to_date": indicator_series[-1].get("date") if indicator_series else None,
                "series": indicator_series
            },
            "errorCode": 0,
            "errorDesc": "",
            "requestId": request_id,
            "result": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_specific_indicator: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{symbol}/summary",
            summary="Get Indicators Summary",
            description="Get a quick summary of key technical indicators with trading signals")
async def get_indicators_summary(
    symbol: str,
    timeframe: str = Query("1D", description="Timeframe: 1D, 1W, 1M, 1Y, 5Y"),
    from_date: Optional[str] = Query(None, description="Start date (DD/MM/YYYY) - optional"),
    to_date: Optional[str] = Query(None, description="End date (DD/MM/YYYY) - optional")
):
    """
    Get a concise summary of key technical indicators
    
    Returns only the most important indicators with clear trading signals:
    - RSI with overbought/oversold status
    - MACD with trend direction
    - Moving averages (SMA 20, 50)
    - Bollinger Bands position
    - Volume indicators
    - Trend strength (ADX)
    """
    request_id = str(uuid.uuid4())
    
    try:
        # Validate timeframe
        if timeframe not in {"1D", "1W", "1M", "1Y", "5Y"}:
            raise HTTPException(
                status_code=400,
                detail="Invalid timeframe. Valid values: 1D, 1W, 1M, 1Y, 5Y"
            )
        
        # Fetch and calculate indicators
        df = await TechnicalIndicatorsService.fetch_ohlc_data(
            symbol=symbol.upper(),
            from_date=from_date,
            to_date=to_date,
            timeframe=timeframe,
            resolution=None
        )
        
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No OHLC data found for symbol: {symbol}"
            )
        
        indicators = TechnicalIndicatorsService.calculate_all_indicators(df)
        latest = TechnicalIndicatorsService.get_latest_indicator_values(indicators)
        signals = TechnicalIndicatorsService.generate_signals(latest)
        
        # Create summary response
        summary = {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "date": latest.get('dates'),
            "close_price": latest.get('close_prices'),
            "key_indicators": {
                "trend": {
                    "sma_20": latest.get('sma_20'),
                    "sma_50": latest.get('sma_50'),
                    "ema_12": latest.get('ema_12'),
                    "ema_26": latest.get('ema_26')
                },
                "momentum": {
                    "rsi_14": latest.get('rsi_14'),
                    "macd": latest.get('macd_histogram'),
                    "DIF": latest.get('macd'),
                    "DEA": latest.get('macd_signal'),
                    "stoch_k": latest.get('stoch_k'),
                    "stoch_d": latest.get('stoch_d'),
                    "stoch_j": (
                        3 * latest.get('stoch_k') - 2 * latest.get('stoch_d')
                        if latest.get('stoch_k') is not None and latest.get('stoch_d') is not None
                        else None
                    )
                },
                "volatility": {
                    "bb_upper": latest.get('bb_upper'),
                    "bb_middle": latest.get('bb_middle'),
                    "bb_lower": latest.get('bb_lower'),
                    "atr_14": latest.get('atr_14')
                },
                "volume": {
                    "obv": latest.get('obv'),
                    "mfi_14": latest.get('mfi_14')
                },
                "trend_strength": {
                    "adx_14": latest.get('adx_14')
                }
            },
            "signals": signals
        }
        
        return {
            "data": summary,
            "errorCode": 0,
            "errorDesc": "",
            "requestId": request_id,
            "result": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_indicators_summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
