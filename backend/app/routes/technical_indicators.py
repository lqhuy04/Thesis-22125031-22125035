"""
Technical Indicators Routes
API endpoints for technical analysis indicators using TA-Lib
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import datetime
import uuid
import pandas as pd
from app.services.technical_indicators_service import TechnicalIndicatorsService
from app.services.market_service import MarketService
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/technical-indicators", tags=["Technical Indicators"], dependencies=[Depends(get_current_user)])

@router.get("/{symbol}",
            summary="Calculate Technical Indicators",
            description="Calculate technical indicators for a stock symbol using TA-Lib")
def get_technical_indicators(
    symbol: str,
    interval: str = Query("15m", description="Interval: 1m, 5m, 15m, 30m, 1h, 1d, 1w, 1M"),
):
    request_id = str(uuid.uuid4())
    try:
        symbol = symbol.upper()

        if interval not in {"1m", "5m", "15m", "30m", "1h", "1d", "1w", "1M"}:
            return {"success": False, "error": f"Unsupported interval: {interval}"}

        current_rows = MarketService.get_stock_price_by_interval(
            symbol=symbol,
            interval=interval,
        )

        if not current_rows:
            return {
                "data": [],
                "errorCode": 0,
                "errorDesc": "",
                "requestId": request_id,
                "result": False
            }
        
        # Convert to DataFrame để tính indicators
        df = pd.DataFrame(current_rows)

        if "trading_time" in df.columns:
            df = df.sort_values("trading_time").reset_index(drop=True)

        indicators = TechnicalIndicatorsService.calculate_all_indicators(df)

        # Zip candles + indicators thành từng record
        records = []
        for i, row in df.iterrows():

            t_str = row["trading_time"].split('+')[0].replace('Z', '')
            try:
                t_dt = datetime.fromisoformat(t_str)
            except ValueError:
                t_dt = datetime.strptime(t_str[:19], "%Y-%m-%dT%H:%M:%S")

            record = {
                "TradingDate": t_dt.strftime("%d/%m/%Y"),
                "Time": t_dt.strftime("%H:%M:%S"),
            }
            for key, values in indicators.items():
                record[key] = values[i] if i < len(values) else None
            records.append(record)
        

        return {
            "data": records,
            "errorCode": 0,
            "errorDesc": "",
            "requestId": request_id,
            "result": True
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in get_technical_indicators: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")