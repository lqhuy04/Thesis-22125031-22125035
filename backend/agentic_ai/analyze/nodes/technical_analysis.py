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


# ─────────────────────────────────────────────────────────────
# Pre-computed scoring — đếm bullish points trong code thay vì LLM
# ─────────────────────────────────────────────────────────────

def _compute_technical_score(records: list[dict]) -> dict:
    """
    Đếm bullish points theo đúng 9 quy tắc trong aggregator prompt.
    Trả về: {score, max_score, classification, signals: [...], trend_info: {...}}
    """
    if not records:
        return {
            "score": 0,
            "max_score": 9,
            "classification": "NO_DATA",
            "signals": [],
            "trend_info": {},
        }

    latest = records[-1]

    rsi      = _clean(latest.get("rsi_14"))
    macd     = _clean(latest.get("macd"))
    macd_sig = _clean(latest.get("macd_signal"))
    macd_h   = _clean(latest.get("macd_histogram"))
    bb_upper = _clean(latest.get("bb_upper"))
    bb_lower = _clean(latest.get("bb_lower"))
    close    = _clean(latest.get("close"))
    kdj_k    = _clean(latest.get("kdj_k"))
    kdj_d    = _clean(latest.get("kdj_d"))
    sma_20   = _clean(latest.get("sma_20"))
    sma_50   = _clean(latest.get("sma_50"))

    signals: list[str] = []
    score = 0

    # 1. RSI vùng 45–70
    if rsi is not None and 45 <= rsi <= 70:
        score += 1
        signals.append(f"RSI={rsi:.1f} trong vùng 45–70 (đà tăng lành mạnh)")
    # 2. RSI < 30 oversold
    if rsi is not None and rsi < 30:
        score += 1
        signals.append(f"RSI={rsi:.1f} oversold (tiềm năng hồi)")
    # 3. MACD > Signal
    if macd is not None and macd_sig is not None and macd > macd_sig:
        score += 1
        signals.append(f"MACD ({macd:.4f}) > Signal ({macd_sig:.4f})")
    # 4. Histogram > 0
    if macd_h is not None and macd_h > 0:
        score += 1
        signals.append(f"MACD Histogram dương ({macd_h:.4f})")
    # 5. Giá > SMA20
    if close is not None and sma_20 is not None and close > sma_20:
        score += 1
        signals.append(f"Giá ({close:.2f}) > SMA20 ({sma_20:.2f})")
    # 6. SMA20 > SMA50
    if sma_20 is not None and sma_50 is not None and sma_20 > sma_50:
        score += 1
        signals.append(f"SMA20 > SMA50 (xu hướng ngắn–trung hạn tích cực)")
    # 7. Giá trong vùng giữa BB (không quá mua)
    if (close is not None and bb_upper is not None and bb_lower is not None
            and close < bb_upper * 0.99 and close > bb_lower * 1.01):
        score += 1
        signals.append("Giá trong vùng giữa Bollinger Band (còn dư địa)")
    # 8. KDJ K < 20 oversold
    if kdj_k is not None and kdj_k < 20:
        score += 1
        signals.append(f"KDJ K={kdj_k:.1f} oversold")
    # 9. KDJ K cắt lên D — cần ≥ 2 records để xác định
    if len(records) >= 2:
        prev = records[-2]
        prev_k = _clean(prev.get("kdj_k"))
        prev_d = _clean(prev.get("kdj_d"))
        if (kdj_k is not None and kdj_d is not None
                and prev_k is not None and prev_d is not None
                and prev_k <= prev_d and kdj_k > kdj_d):
            score += 1
            signals.append("KDJ K vừa cắt lên D (tín hiệu mua)")

    # ─── Classification ───
    if score >= 5:
        classification = "BULLISH"
    elif score >= 3:
        classification = "TRUNG TÍNH"
    else:
        classification = "BEARISH"

    # ─── Thêm trend info: hướng của RSI/MACD trong N nến gần nhất ───
    trend_info = _compute_trend_info(records)

    return {
        "score": score,
        "max_score": 9,
        "classification": classification,
        "signals": signals,
        "trend_info": trend_info,
    }


def _compute_trend_info(records: list[dict]) -> dict:
    """
    Phân tích xu hướng của các indicator trong N nến gần nhất.
    Quan trọng cho ngắn hạn — không chỉ giá trị mà cả động lượng.
    """
    info: dict = {}
    n = min(len(records), 10)
    if n < 2:
        return info

    window = records[-n:]

    # RSI direction
    rsi_vals = [_clean(r.get("rsi_14")) for r in window]
    rsi_vals = [v for v in rsi_vals if v is not None]
    if len(rsi_vals) >= 2:
        delta = rsi_vals[-1] - rsi_vals[0]
        if delta > 3:
            info["rsi_direction"] = f"RSI đang TĂNG ({rsi_vals[0]:.1f} → {rsi_vals[-1]:.1f})"
        elif delta < -3:
            info["rsi_direction"] = f"RSI đang GIẢM ({rsi_vals[0]:.1f} → {rsi_vals[-1]:.1f})"
        else:
            info["rsi_direction"] = f"RSI đi ngang quanh {rsi_vals[-1]:.1f}"

    # MACD histogram direction
    hist_vals = [_clean(r.get("macd_histogram")) for r in window]
    hist_vals = [v for v in hist_vals if v is not None]
    if len(hist_vals) >= 2:
        if hist_vals[-1] > hist_vals[0] and hist_vals[-1] > 0:
            info["macd_momentum"] = "MACD Histogram tăng và dương — động lượng tăng mạnh dần"
        elif hist_vals[-1] > hist_vals[0]:
            info["macd_momentum"] = "MACD Histogram đang cải thiện (chưa dương)"
        elif hist_vals[-1] < hist_vals[0] and hist_vals[-1] < 0:
            info["macd_momentum"] = "MACD Histogram giảm và âm — động lượng bearish mạnh dần"
        else:
            info["macd_momentum"] = "MACD Histogram đang yếu đi"

    # MACD cross recent
    macds = [(_clean(r.get("macd")), _clean(r.get("macd_signal"))) for r in window]
    cross_idx = None
    cross_type = None
    for i in range(1, len(macds)):
        m0, s0 = macds[i-1]
        m1, s1 = macds[i]
        if None in (m0, s0, m1, s1):
            continue
        if m0 <= s0 and m1 > s1:
            cross_idx, cross_type = i, "golden"
        elif m0 >= s0 and m1 < s1:
            cross_idx, cross_type = i, "death"
    if cross_idx is not None:
        bars_ago = len(macds) - 1 - cross_idx
        kind = "MACD Golden Cross" if cross_type == "golden" else "MACD Death Cross"
        info["macd_cross"] = f"{kind} cách đây {bars_ago} nến"

    # SMA cross recent (golden / death cross)
    smas = [(_clean(r.get("sma_20")), _clean(r.get("sma_50"))) for r in window]
    sma_cross_idx = None
    sma_cross_type = None
    for i in range(1, len(smas)):
        a0, b0 = smas[i-1]
        a1, b1 = smas[i]
        if None in (a0, b0, a1, b1):
            continue
        if a0 <= b0 and a1 > b1:
            sma_cross_idx, sma_cross_type = i, "golden"
        elif a0 >= b0 and a1 < b1:
            sma_cross_idx, sma_cross_type = i, "death"
    if sma_cross_idx is not None:
        bars_ago = len(smas) - 1 - sma_cross_idx
        kind = "Golden Cross (SMA20 cắt lên SMA50)" if sma_cross_type == "golden" else "Death Cross (SMA20 cắt xuống SMA50)"
        info["sma_cross"] = f"{kind} cách đây {bars_ago} nến"

    # Divergence đơn giản: giá vs RSI trên window
    closes = [_clean(r.get("close")) for r in window]
    closes = [c for c in closes if c is not None]
    if len(closes) >= 3 and len(rsi_vals) >= 3:
        price_delta = closes[-1] - closes[0]
        rsi_delta = rsi_vals[-1] - rsi_vals[0]
        if price_delta > 0 and rsi_delta < -3:
            info["divergence"] = "Bearish divergence: giá tăng nhưng RSI giảm"
        elif price_delta < 0 and rsi_delta > 3:
            info["divergence"] = "Bullish divergence: giá giảm nhưng RSI tăng"

    return info


def _compute_price_position(
    close: float | None,
    bb_upper: float | None,
    bb_lower: float | None,
    rsi: float | None,
) -> str:
    """
    Vị trí giá so với kháng cự / hỗ trợ — dùng cho deterministic Mua/Chờ rule.
      "near_resistance" : giá ≥ 98% upper BB HOẶC RSI > 70
      "near_support"    : giá ≤ 102% lower BB
      "mid"             : ở giữa
      "unknown"         : thiếu dữ liệu
    """
    if close is None:
        return "unknown"
    if rsi is not None and rsi > 70:
        return "near_resistance"
    if bb_upper is not None and close >= bb_upper * 0.98:
        return "near_resistance"
    if bb_lower is not None and close <= bb_lower * 1.02:
        return "near_support"
    if bb_upper is None and bb_lower is None:
        return "unknown"
    return "mid"


def _format_technical_output(
    symbol: str,
    interval: str,
    records: list[dict],
    current_price: float | None = None,
    current_price_time: datetime | None = None,
) -> dict:
    """
    Trả về dict gồm:
      - display: markdown để hiển thị / log
      - signal: BULLISH | TRUNG TÍNH | BEARISH | NO_DATA
      - score: int
      - max_score: int
      - signals: danh sách tín hiệu cụ thể đã thỏa mãn
      - trend_info: hướng RSI, MACD, cross, divergence
      - current_price: giá hiện tại để aggregator dùng cho entry/exit hint
    """
    if not records:
        return {
            "display": "Không đủ dữ liệu để phân tích kỹ thuật.",
            "signal": "NO_DATA",
            "score": 0,
            "max_score": 9,
            "signals": [],
            "trend_info": {},
            "price_position": "unknown",
            "current_price": None,
        }

    latest = records[-1]
    oldest = records[0]

    closes = [r["close"] for r in records if _clean(r.get("close")) is not None]
    price_trend = "Tăng" if len(closes) >= 2 and closes[-1] > closes[0] else "Giảm"

    score_info = _compute_technical_score(records)

    # Vị trí giá so với kháng cự/hỗ trợ — quyết định Mua/Chờ deterministic
    price_position = _compute_price_position(
        close=_clean(latest.get("close")),
        bb_upper=_clean(latest.get("bb_upper")),
        bb_lower=_clean(latest.get("bb_lower")),
        rsi=_clean(latest.get("rsi_14")),
    )

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

    trend_lines = "\n".join(f"- {v}" for v in score_info["trend_info"].values()) or "- (không có)"
    signals_lines = "\n".join(f"  ✓ {s}" for s in score_info["signals"]) or "  (không có tín hiệu bullish)"

    position_label = {
        "near_resistance": "Gần KHÁNG CỰ (upper BB hoặc RSI cao)",
        "near_support":    "Gần HỖ TRỢ (lower BB)",
        "mid":             "Vùng giữa",
        "unknown":         "Không xác định",
    }.get(price_position, "Không xác định")

    display = f"""
## Phân tích kỹ thuật — {symbol} ({interval})
Khoảng thời gian: {oldest["TradingDate"]} {oldest["Time"]} → {latest["TradingDate"]} {latest["Time"]}
Số phiên: {len(records)}

### Đánh giá tổng hợp (pre-computed)
- Phân loại: **{score_info["classification"]}** ({score_info["score"]}/{score_info["max_score"]} điểm bullish)
- Vị trí giá: **{position_label}** (`price_position={price_position}`)
- Tín hiệu bullish đã thỏa mãn:
{signals_lines}

### Xu hướng động lượng (last 10 nến)
{trend_lines}

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

    return {
        "display": display,
        "signal": score_info["classification"],
        "score": score_info["score"],
        "max_score": score_info["max_score"],
        "signals": score_info["signals"],
        "trend_info": score_info["trend_info"],
        "price_position": price_position,
        "current_price": _clean(display_price),
        "bb_upper": c_bb_upper,
        "bb_lower": c_bb_lower,
        "sma_20": c_sma_20,
        "sma_50": c_sma_50,
    }


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
        return {"agent_results": {"technical_analysis_agent": {
            "display": "Không có dữ liệu thị trường.",
            "signal": "NO_DATA",
            "score": 0,
            "max_score": 9,
            "signals": [],
            "trend_info": {},
            "price_position": "unknown",
            "current_price": None,
        }}}

    # 3. Sort
    if "trading_time" in df.columns:
        df["_dt"] = df["trading_time"].apply(_parse_dt)
        df = df.sort_values("_dt").reset_index(drop=True)

    # 4. Tính indicators trên toàn bộ df trước khi filter
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
        return {"agent_results": {"technical_analysis_agent": {
            "display": "Không có dữ liệu trong khoảng thời gian được chỉ định.",
            "signal": "NO_DATA",
            "score": 0,
            "max_score": 9,
            "signals": [],
            "trend_info": {},
            "price_position": "unknown",
            "current_price": None,
        }}}

    output = _format_technical_output(symbol, interval, records, current_price, current_price_time)

    print("[Technical Analysis Agent] Output:", output["display"])
    print(f"[Technical Analysis Agent] Signal: {output['signal']} ({output['score']}/{output['max_score']})")

    return {
        "agent_results": {
            "technical_analysis_agent": output,
        },
    }
