from datetime import datetime
import math
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


def _clean(value) -> float | None:
    if value is None:
        return None
    try:
        if math.isnan(float(value)):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value, spec: str) -> str:
    v = _clean(value)
    if v is None:
        return ""
    return format(v, spec)


def _signal(value, low, high) -> str:
    v = _clean(value)
    if v is None:
        return ""
    if v <= low:
        return "Quá bán"
    if v >= high:
        return "Quá mua"
    return "Trung tính"


def _format_technical_output(
    symbol: str,
    interval: str,
    records: list[dict],
    current_price: float | None = None,
    current_price_time: datetime | None = None,
) -> str:
    if not records:
        return "Không đủ dữ liệu để phân tích kỹ thuật."

    latest = records[-1]
    oldest = records[0]

    closes = [r["close"] for r in records if _clean(r.get("close")) is not None]
    price_trend = "Tăng" if len(closes) >= 2 and closes[-1] > closes[0] else "Giảm"

    rsi       = latest.get("rsi_14")
    macd      = latest.get("macd")
    macd_sig  = latest.get("macd_signal")
    macd_hist = latest.get("macd_histogram")
    bb_upper  = latest.get("bb_upper")
    bb_lower  = latest.get("bb_lower")
    bb_middle = latest.get("bb_middle")
    close     = latest.get("close")
    kdj_k     = latest.get("kdj_k")
    kdj_d     = latest.get("kdj_d")
    kdj_j     = latest.get("kdj_j")
    sma_20    = latest.get("sma_20")
    sma_50    = latest.get("sma_50")

    c_macd     = _clean(macd)
    c_macd_sig = _clean(macd_sig)
    c_close    = _clean(close)
    c_bb_upper = _clean(bb_upper)
    c_bb_lower = _clean(bb_lower)
    c_sma_20   = _clean(sma_20)
    c_sma_50   = _clean(sma_50)

    # Giá hiện tại: ưu tiên 1m, fallback về close của candle cuối
    display_price = current_price if current_price is not None else c_close
    display_time = (
        current_price_time.strftime("%H:%M %d/%m/%Y")
        if current_price_time else
        f"{latest['TradingDate']} {latest['Time']}"
    )

    macd_direction = (
        "Tăng (MACD > Signal)" if c_macd is not None and c_macd_sig is not None and c_macd > c_macd_sig
        else "Giảm (MACD < Signal)" if c_macd is not None and c_macd_sig is not None
        else ""
    )

    bb_pos = (
        "Gần band trên (có thể quá mua)" if c_close and c_bb_upper and c_close >= c_bb_upper * 0.99
        else "Gần band dưới (có thể quá bán)" if c_close and c_bb_lower and c_close <= c_bb_lower * 1.01
        else "Trong vùng giữa Bollinger Band" if c_close and c_bb_upper and c_bb_lower
        else ""
    )

    sma_trend = (
        "Tăng (SMA20 > SMA50)" if c_sma_20 and c_sma_50 and c_sma_20 > c_sma_50
        else "Giảm (SMA20 < SMA50)" if c_sma_20 and c_sma_50
        else ""
    )

    return f"""
## Phân tích kỹ thuật — {symbol} ({interval})
Khoảng thời gian: {oldest["TradingDate"]} {oldest["Time"]} → {latest["TradingDate"]} {latest["Time"]}
Số phiên: {len(records)}

### Giá hiện tại (cập nhật lúc {display_time})
- Giá: {_fmt(display_price, ",.2f")} đồng
- Xu hướng giá trong kỳ ({interval}): {price_trend}

### RSI (14)
- Giá trị: {_fmt(rsi, ".2f")}
- Tín hiệu: {_signal(rsi, 30, 70)}

### MACD
- MACD: {_fmt(macd, ".4f")}
- Signal: {_fmt(macd_sig, ".4f")}
- Histogram: {_fmt(macd_hist, ".4f")}
- Tín hiệu: {macd_direction}

### Bollinger Bands
- Upper: {_fmt(bb_upper, ",.2f")} | Middle: {_fmt(bb_middle, ",.2f")} | Lower: {_fmt(bb_lower, ",.2f")}
- Vị trí giá: {bb_pos}

### KDJ
- K: {_fmt(kdj_k, ".2f")} | D: {_fmt(kdj_d, ".2f")} | J: {_fmt(kdj_j, ".2f")}
- Tín hiệu K: {_signal(kdj_k, 20, 80)}

### Moving Averages
- SMA20: {_fmt(sma_20, ",.2f")} | SMA50: {_fmt(sma_50, ",.2f")}
- Tín hiệu: {sma_trend}
""".strip()


def technical_analysis_agent(state: AgentState) -> AgentState:
    myTask = state.get("plan", {}).get("technical_analysis_agent", {})
    symbol = state.get("symbol", "")
    interval = myTask.get("interval", "1d")
    from_date = myTask.get("from_date", "")
    to_date = myTask.get("to_date", "")

    # 1. Fetch giá 1m để lấy giá hiện tại chính xác
    current_price = None
    current_price_time = None
    try:
        price_1m_rows = MarketService.get_stock_price_by_interval(
            symbol=symbol,
            interval="1m",
        )
        price_1m_df = pd.DataFrame(price_1m_rows)
        if not price_1m_df.empty and "trading_time" in price_1m_df.columns:
            price_1m_df["_dt"] = price_1m_df["trading_time"].apply(_parse_dt)
            price_1m_df = price_1m_df.sort_values("_dt")
            latest_1m = price_1m_df.iloc[-1]
            current_price = _clean(latest_1m.get("close"))
            current_price_time = latest_1m["_dt"]
    except Exception:
        pass  # fallback về close của candle interval cuối

    # 2. Fetch giá theo interval để tính indicators
    current_rows = MarketService.get_stock_price_by_interval(
        symbol=symbol,
        interval=interval,
    )

    df = pd.DataFrame(current_rows)

    if df.empty:
        return {"agent_results": {"technical_analysis_agent": "Không có dữ liệu thị trường."}}

    # 3. Sort
    if "trading_time" in df.columns:
        df["_dt"] = df["trading_time"].apply(_parse_dt)
        df = df.sort_values("_dt").reset_index(drop=True)

    # 4. Tính indicators trên toàn bộ df trước khi filter (đảm bảo warm-up đủ)
    indicators = TechnicalIndicatorsService.calculate_all_indicators(df)

    # 5. Gộp giá + indicators thành records
    records = []
    for i, row in df.iterrows():
        t_dt = row["_dt"]
        record = {
            "TradingDate": t_dt.strftime("%d/%m/%Y"),
            "Time": t_dt.strftime("%H:%M:%S"),
            "_dt": t_dt,
            "close": _clean(row.get("close")),
        }
        for key, values in indicators.items():
            record[key] = _clean(values[i] if i < len(values) else None)
        records.append(record)

    # 6. Filter theo thời gian SAU khi đã tính indicators
    if from_date:
        start = datetime.fromisoformat(from_date)
        records = [r for r in records if r["_dt"] >= start]
    if to_date:
        end = datetime.fromisoformat(to_date)
        if end.hour == 0 and end.minute == 0 and end.second == 0:
            end = end.replace(hour=23, minute=59, second=59)
        records = [r for r in records if r["_dt"] <= end]

    # 7. Bỏ _dt khỏi record trước khi format
    for r in records:
        r.pop("_dt", None)

    if not records:
        return {"agent_results": {"technical_analysis_agent": "Không có dữ liệu trong khoảng thời gian được chỉ định."}}

    output = _format_technical_output(symbol, interval, records, current_price, current_price_time)

    print("[Technical Analysis Agent] Output:", output)

    return {
        "agent_results": {
            "technical_analysis_agent": output,
        },
    }