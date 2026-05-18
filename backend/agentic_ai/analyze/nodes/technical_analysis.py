from datetime import datetime
import pandas as pd
from agentic_ai.analyze.state import AgentState
from app.services.market_service import MarketService
from app.services.technical_indicators_service import TechnicalIndicatorsService


def _parse_dt(trading_time: str) -> datetime:
    t_str = trading_time.split('+')[0].replace('Z', '')
    try:
        return datetime.fromisoformat(t_str)
    except ValueError:
        return datetime.strptime(t_str[:19], "%Y-%m-%dT%H:%M:%S")


def _signal(value, low, high) -> str:
    if value is None:
        return "N/A"
    if value <= low:
        return "Quá bán"
    if value >= high:
        return "Quá mua"
    return "Trung tính"


def _fmt(value, spec: str, fallback: str = "N/A") -> str:
    if value is None:
        return fallback
    return format(value, spec)


def _format_technical_output(symbol: str, interval: str, records: list[dict]) -> str:
    valid = [r for r in records if r.get("rsi_14") is not None]

    if not valid:
        return "Không đủ dữ liệu để phân tích kỹ thuật."

    latest = valid[-1]
    oldest = valid[0]

    closes = [r["close"] for r in valid if r.get("close") is not None]
    price_trend = "Tăng" if len(closes) >= 2 and closes[-1] > closes[0] else "Giảm"

    rsi      = latest.get("rsi_14")
    macd     = latest.get("macd")
    macd_sig = latest.get("macd_signal")
    macd_hist = latest.get("macd_histogram")
    bb_upper = latest.get("bb_upper")
    bb_lower = latest.get("bb_lower")
    bb_middle = latest.get("bb_middle")
    close    = latest.get("close")
    kdj_k    = latest.get("kdj_k")
    kdj_d    = latest.get("kdj_d")
    kdj_j    = latest.get("kdj_j")
    sma_20   = latest.get("sma_20")
    sma_50   = latest.get("sma_50")

    macd_direction = "Tăng (MACD > Signal)" if macd and macd_sig and macd > macd_sig else "Giảm (MACD < Signal)"

    bb_pos = (
        "Gần band trên (có thể quá mua)" if close and bb_upper and close >= bb_upper * 0.98
        else "Gần band dưới (có thể quá bán)" if close and bb_lower and close <= bb_lower * 1.02
        else "Trong vùng giữa Bollinger Band"
    )

    sma_trend = "Tăng (SMA20 > SMA50)" if sma_20 and sma_50 and sma_20 > sma_50 else "Giảm (SMA20 < SMA50)"

    return f"""
## Phân tích kỹ thuật — {symbol} ({interval})
Khoảng thời gian: {oldest["TradingDate"]} {oldest["Time"]} → {latest["TradingDate"]} {latest["Time"]}
Số phiên hợp lệ: {len(valid)}

### Giá hiện tại
- Giá đóng cửa gần nhất: {_fmt(close, ",.0f")} đồng
- Xu hướng giá trong kỳ: {price_trend}

### RSI (14)
- Giá trị: {_fmt(rsi, ".2f")}
- Tín hiệu: {_signal(rsi, 30, 70)}

### MACD
- MACD: {_fmt(macd, ".4f")}
- Signal: {_fmt(macd_sig, ".4f")}
- Histogram: {_fmt(macd_hist, ".4f")}
- Tín hiệu: {macd_direction}

### Bollinger Bands
- Upper: {_fmt(bb_upper, ",.0f")} | Middle: {_fmt(bb_middle, ",.0f")} | Lower: {_fmt(bb_lower, ",.0f")}
- Vị trí giá: {bb_pos}

### KDJ
- K: {_fmt(kdj_k, ".2f")} | D: {_fmt(kdj_d, ".2f")} | J: {_fmt(kdj_j, ".2f")}
- Tín hiệu K: {_signal(kdj_k, 20, 80)}

### Moving Averages
- SMA20: {_fmt(sma_20, ",.0f")} | SMA50: {_fmt(sma_50, ",.0f")}
- Tín hiệu: {sma_trend}
""".strip()


def technical_analysis_agent(state: AgentState) -> AgentState:
    myTask = state.get("plan", {}).get("technical_analysis_agent", {})
    symbol = state.get("symbol", "")
    interval = myTask.get("interval", "1d")
    from_date = myTask.get("from_date", "")
    to_date = myTask.get("to_date", "")

    current_rows = MarketService.get_stock_price_by_interval(
        symbol=symbol,
        interval=interval,
    )

    df = pd.DataFrame(current_rows)

    if df.empty:
        return {"agent_results": {"technical_analysis_agent": "Không có dữ liệu thị trường."}}

    if "trading_time" in df.columns:
        df["_dt"] = df["trading_time"].apply(_parse_dt)
        df = df.sort_values("_dt").reset_index(drop=True)

        if from_date:
            start = datetime.fromisoformat(from_date)
            df = df[df["_dt"] >= start]
        if to_date:
            end = datetime.fromisoformat(to_date)
            df = df[df["_dt"] <= end]

        df = df.reset_index(drop=True)

    indicators = TechnicalIndicatorsService.calculate_all_indicators(df)

    records = []
    for i, row in df.iterrows():
        t_dt = row["_dt"]
        record = {
            "TradingDate": t_dt.strftime("%d/%m/%Y"),
            "Time": t_dt.strftime("%H:%M:%S"),
            "close": row.get("close"),
        }
        for key, values in indicators.items():
            record[key] = values[i] if i < len(values) else None
        records.append(record)

    output = _format_technical_output(symbol, interval, records)

    return {
        "agent_results": {
            "technical_analysis_agent": output,
        },
    }