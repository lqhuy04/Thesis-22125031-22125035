from datetime import datetime
import math
import pandas as pd
from agentic_ai.analyze.state import AgentState
from app.backtest.engine import IndicatorEngine
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


def _score_rsi(current: float | None, previous: float | None) -> tuple[int, str]:
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
        gap_current  = sma20_current - sma50_current
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
        gap_current  = close_current - middle
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


def _fetch_current_price(symbol: str) -> tuple[float | None, datetime | None]:
    """Bước 1: Fetch giá 1m để lấy giá hiện tại chính xác."""
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
            return _clean(latest_1m.get("close")), latest_1m["_dt"]
    except Exception:
        pass
    return None, None


def _build_records(
    symbol: str,
    interval: str,
    from_date: str,
    to_date: str,
    indicator_source: str = "live",
) -> list[dict] | str:
    """
    Bước 2–7: Fetch, tính indicators, gộp thành records, filter theo thời gian.
    Trả về list[dict] nếu thành công, hoặc str (error message) nếu thất bại.
    """
    current_rows = MarketService.get_stock_price_by_interval(
        symbol=symbol,
        interval=interval,
    )

    df = pd.DataFrame(current_rows)
    if df.empty:
        return "Không có dữ liệu thị trường."

    if "trading_time" in df.columns:
        df["_dt"] = df["trading_time"].apply(_parse_dt)
        df = df.sort_values("_dt").reset_index(drop=True)

    start = datetime.fromisoformat(from_date) if from_date else None
    end = datetime.fromisoformat(to_date) if to_date else None
    if end and end.hour == 0 and end.minute == 0 and end.second == 0:
        end = end.replace(hour=23, minute=59, second=59)

    if indicator_source == "backtest":
        if start is not None:
            df = df[df["_dt"] >= start]
        if end is not None:
            df = df[df["_dt"] <= end]
        df = df.reset_index(drop=True)

        if df.empty:
            return "Không có dữ liệu trong khoảng thời gian được chỉ định."

        indicator_engine = IndicatorEngine()
        df = indicator_engine.add_indicators(df)
        indicators = {
            "rsi_14": df["rsi_14"].tolist(),
            "sma_20": df["sma_20"].tolist(),
            "sma_50": df["sma_50"].tolist(),
            "bb_upper": df["bb_upper"].tolist(),
            "bb_middle": df["bb_middle"].tolist(),
            "bb_lower": df["bb_lower"].tolist(),
            "macd": df["macd"].tolist(),
            "macd_signal": df["macd_signal"].tolist(),
            "macd_histogram": df["macd_histogram"].tolist(),
            "kdj_k": df["kdj_k"].tolist(),
            "kdj_d": df["kdj_d"].tolist(),
            "kdj_j": df["kdj_j"].tolist(),
        }
    else:
        indicators = TechnicalIndicatorsService.calculate_all_indicators(df)

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

    if from_date:
        records = [r for r in records if r["_dt"] >= start]
    if to_date:
        records = [r for r in records if r["_dt"] <= end]

    for r in records:
        r.pop("_dt", None)

    if not records:
        return "Không có dữ liệu trong khoảng thời gian được chỉ định."

    return records


def _format_technical_output(
    symbol: str,
    interval: str,
    records: list[dict],
    current_price: float | None = None,
    current_price_time: datetime | None = None,
) -> dict:
    if not records:
        return {"error": "Không đủ dữ liệu để phân tích kỹ thuật."}

    latest   = records[-1]
    previous = records[-2] if len(records) >= 2 else None

    # RSI
    rsi_current  = _clean(latest.get("rsi_14"))
    rsi_previous = _clean(previous.get("rsi_14")) if previous else None
    rsi_score, rsi_reason = _score_rsi(rsi_current, rsi_previous)

    # MA
    sma20_current  = _clean(latest.get("sma_20"))
    sma20_previous = _clean(previous.get("sma_20")) if previous else None
    sma50_current  = _clean(latest.get("sma_50"))
    sma50_previous = _clean(previous.get("sma_50")) if previous else None
    price_for_ma   = current_price if current_price is not None else _clean(latest.get("close"))
    ma_score, ma_reason = _score_ma(
        sma20_current, sma20_previous,
        sma50_current, sma50_previous,
        price_for_ma,
    )

    # BOLL
    bb_upper       = _clean(latest.get("bb_upper"))
    bb_middle      = _clean(latest.get("bb_middle"))
    bb_lower       = _clean(latest.get("bb_lower"))
    close_current  = _clean(latest.get("close"))
    close_previous = _clean(previous.get("close")) if previous else None
    boll_score, boll_reason = _score_boll(
        bb_upper, bb_middle, bb_lower,
        close_current, close_previous,
        current_price,
    )

    # MACD
    macd_current    = _clean(latest.get("macd"))
    macd_previous   = _clean(previous.get("macd")) if previous else None
    signal_current  = _clean(latest.get("macd_signal"))
    signal_previous = _clean(previous.get("macd_signal")) if previous else None
    hist_current    = _clean(latest.get("macd_histogram"))
    hist_previous   = _clean(previous.get("macd_histogram")) if previous else None
    macd_score, macd_reason = _score_macd(
        macd_current, macd_previous,
        signal_current, signal_previous,
        hist_current, hist_previous,
    )

    # KDJ
    k_current  = _clean(latest.get("kdj_k"))
    k_previous = _clean(previous.get("kdj_k")) if previous else None
    d_current  = _clean(latest.get("kdj_d"))
    d_previous = _clean(previous.get("kdj_d")) if previous else None
    j_current  = _clean(latest.get("kdj_j"))
    j_previous = _clean(previous.get("kdj_j")) if previous else None
    kdj_score, kdj_reason = _score_kdj(
        k_current, k_previous,
        d_current, d_previous,
        j_current, j_previous,
    )

    # Tổng điểm
    total_score = rsi_score + ma_score + boll_score + macd_score + kdj_score

    # Display price
    display_price = current_price if current_price is not None else close_current
    display_time  = (
        current_price_time.strftime("%H:%M %d/%m/%Y")
        if current_price_time else
        f"{latest['TradingDate']} {latest['Time']}"
    )

    return {
        "symbol":   symbol,
        "interval": interval,
        "period": {
            "from":    f"{records[0]['TradingDate']} {records[0]['Time']}",
            "to":      f"{latest['TradingDate']} {latest['Time']}",
            "candles": len(records),
        },
        "current_price": {
            "value": display_price,
            "time":  display_time,
        },
        "total_score": total_score,   # tổng điểm 0–5, >= 3 → Mua
        "indicators": {
            "rsi": {
                "value":  {"current": rsi_current, "previous": rsi_previous},
                "score":  rsi_score,
                "reason": rsi_reason,
            },
            "ma": {
                "value": {
                    "sma20_current":  sma20_current,
                    "sma20_previous": sma20_previous,
                    "sma50_current":  sma50_current,
                    "sma50_previous": sma50_previous,
                },
                "score":  ma_score,
                "reason": ma_reason,
            },
            "boll": {
                "value": {
                    "upper":          bb_upper,
                    "middle":         bb_middle,
                    "lower":          bb_lower,
                    "close_current":  close_current,
                    "close_previous": close_previous,
                },
                "score":  boll_score,
                "reason": boll_reason,
            },
            "macd": {
                "value": {
                    "macd_current":    macd_current,
                    "macd_previous":   macd_previous,
                    "signal_current":  signal_current,
                    "signal_previous": signal_previous,
                    "hist_current":    hist_current,
                    "hist_previous":   hist_previous,
                },
                "score":  macd_score,
                "reason": macd_reason,
            },
            "kdj": {
                "value": {
                    "k_current":  k_current,
                    "k_previous": k_previous,
                    "d_current":  d_current,
                    "d_previous": d_previous,
                    "j_current":  j_current,
                    "j_previous": j_previous,
                },
                "score":  kdj_score,
                "reason": kdj_reason,
            },
        },
    }


def technical_analysis_agent(state: AgentState) -> AgentState:
    myTask    = state.get("plan", {}).get("technical_analysis_agent", {})
    symbol    = state.get("symbol", "")
    interval  = myTask.get("interval", "1d")
    from_date = myTask.get("from_date", "")
    to_date   = myTask.get("to_date", "")
    use_current_price = myTask.get("use_current_price", True)
    indicator_source = myTask.get("indicator_source", "live")

    if use_current_price:
        current_price, current_price_time = _fetch_current_price(symbol)
    else:
        current_price, current_price_time = None, None

    records = _build_records(symbol, interval, from_date, to_date, indicator_source)
    if isinstance(records, str):
        return {"agent_results": {"technical_analysis_agent": {"error": records}}}

    output = _format_technical_output(symbol, interval, records, current_price, current_price_time)

    print("[Technical Analysis Agent] Output:", output)

    return {
        "agent_results": {
            "technical_analysis_agent": output,
        },
    }