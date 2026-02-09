"""
Technical Indicators Routes
API endpoints for technical analysis indicators using TA-Lib
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
import uuid
from app.services.technical_indicators_service import TechnicalIndicatorsService
from app.models.base_schemas import success_response, error_response

router = APIRouter(prefix="/api/technical-indicators", tags=["Technical Indicators"])


@router.get("/{symbol}",
            summary="Calculate Technical Indicators",
            description="Calculate top 20 technical indicators for a stock symbol using TA-Lib")
async def get_technical_indicators(
    symbol: str,
    from_date: str = Query(..., description="Start date (DD/MM/YYYY)", example="01/01/2024"),
    to_date: str = Query(..., description="End date (DD/MM/YYYY)", example="31/12/2024"),
    timeframe: str = Query("1D", description="Timeframe: '1D' for daily, 'intraday' for intraday data"),
    resolution: Optional[int] = Query(None, description="Intraday resolution in minutes (1, 5, 15, 30, 60). Required when timeframe='intraday'"),
    include_history: bool = Query(False, description="Include full historical data for all indicators")
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
    - **from_date**: Start date in DD/MM/YYYY format
    - **to_date**: End date in DD/MM/YYYY format
    - **timeframe**: '1D' for daily (default), 'intraday' for intraday data
    - **resolution**: Intraday resolution in minutes (1, 5, 15, 30, 60). Required when timeframe='intraday'
    - **include_history**: If true, returns full time series data. If false (default), returns only latest values
    
    ### Timeframe Examples:
    - Daily: `timeframe=1D` (default)
    - 1-minute: `timeframe=intraday&resolution=1`
    - 5-minute: `timeframe=intraday&resolution=5`
    - 15-minute: `timeframe=intraday&resolution=15`
    - 30-minute: `timeframe=intraday&resolution=30`
    - 1-hour: `timeframe=intraday&resolution=60`
    
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
        
        # Validate timeframe and resolution
        if timeframe.lower() == 'intraday' and not resolution:
            raise HTTPException(
                status_code=400,
                detail="Resolution is required when timeframe is 'intraday'. Valid values: 1, 5, 15, 30, 60 (minutes)"
            )
        
        if resolution and resolution not in [1, 5, 15, 30, 60]:
            raise HTTPException(
                status_code=400,
                detail="Invalid resolution. Valid values: 1, 5, 15, 30, 60 (minutes)"
            )
        
        # Fetch OHLC data
        df = await TechnicalIndicatorsService.fetch_ohlc_data(
            symbol=symbol.upper(),
            from_date=from_date,
            to_date=to_date,
            timeframe=timeframe,
            resolution=resolution
        )
        
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No OHLC data found for symbol: {symbol}"
            )
        
        # Calculate all indicators
        indicators = TechnicalIndicatorsService.calculate_all_indicators(df)
        
        # Prepare response based on include_history flag
        if include_history:
            # Return full historical data
            response_data = {
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "resolution": f"{resolution}min" if resolution else "daily",
                "from_date": from_date,
                "to_date": to_date,
                "data_points": len(df),
                "indicators": indicators
            }
        else:
            # Return only latest values
            latest_indicators = TechnicalIndicatorsService.get_latest_indicator_values(indicators)
            signals = TechnicalIndicatorsService.generate_signals(latest_indicators)
            
            response_data = {
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "resolution": f"{resolution}min" if resolution else "daily",
                "from_date": from_date,
                "to_date": to_date,
                "data_points": len(df),
                "latest_date": latest_indicators.get('dates'),
                "latest_close": latest_indicators.get('close_prices'),
                "indicators": latest_indicators,
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
    from_date: str = Query(..., description="Start date (DD/MM/YYYY)"),
    to_date: str = Query(..., description="End date (DD/MM/YYYY)"),
    timeframe: str = Query("1D", description="Timeframe: '1D' for daily, 'intraday' for intraday data"),
    resolution: Optional[int] = Query(None, description="Intraday resolution in minutes (1, 5, 15, 30, 60)")
):
    """
    Get a specific technical indicator
    
    ### Available Indicators:
    - sma_10, sma_20, sma_50
    - ema_12, ema_26, ema_50
    - rsi_14
    - macd, macd_signal, macd_histogram
    - bb_upper, bb_middle, bb_lower
    - stoch_k, stoch_d
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
        # Validate timeframe and resolution
        if timeframe.lower() == 'intraday' and not resolution:
            raise HTTPException(
                status_code=400,
                detail="Resolution is required when timeframe is 'intraday'"
            )
        
        # Fetch and calculate indicators
        df = await TechnicalIndicatorsService.fetch_ohlc_data(
            symbol=symbol.upper(),
            from_date=from_date,
            to_date=to_date,
            timeframe=timeframe,
            resolution=resolution
        )
        
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No OHLC data found for symbol: {symbol}"
            )
        
        indicators = TechnicalIndicatorsService.calculate_all_indicators(df)
        
        # Check if indicator exists
        if indicator_name not in indicators:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid indicator name: {indicator_name}. Use /api/technical-indicators/{symbol} to see all available indicators."
            )
        
        return {
            "data": {
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "resolution": f"{resolution}min" if resolution else "daily",
                "indicator": indicator_name,
                "dates": indicators['dates'],
                "values": indicators[indicator_name]
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
    from_date: str = Query(..., description="Start date (DD/MM/YYYY)"),
    to_date: str = Query(..., description="End date (DD/MM/YYYY)"),
    timeframe: str = Query("1D", description="Timeframe: '1D' for daily, 'intraday' for intraday data"),
    resolution: Optional[int] = Query(None, description="Intraday resolution in minutes (1, 5, 15, 30, 60)")
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
        # Validate timeframe and resolution
        if timeframe.lower() == 'intraday' and not resolution:
            raise HTTPException(
                status_code=400,
                detail="Resolution is required when timeframe is 'intraday'"
            )
        
        # Fetch and calculate indicators
        df = await TechnicalIndicatorsService.fetch_ohlc_data(
            symbol=symbol.upper(),
            from_date=from_date,
            to_date=to_date,
            timeframe=timeframe,
            resolution=resolution
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
            "resolution": f"{resolution}min" if resolution else "daily",
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
                    "macd": latest.get('macd'),
                    "macd_signal": latest.get('macd_signal'),
                    "stoch_k": latest.get('stoch_k'),
                    "stoch_d": latest.get('stoch_d')
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
