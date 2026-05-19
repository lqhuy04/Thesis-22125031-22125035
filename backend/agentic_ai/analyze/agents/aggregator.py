"""
aggregator.py — Aggregator Agent

Tổng hợp dữ liệu đã PRE-COMPUTED từ:
    + article_agent              → {sentiment, summary, key_events}
    + fundamental_analysis_agent → {signal, score, signals, weaknesses, is_bank_or_finance}
    + technical_analysis_agent   → {signal, score, signals, trend_info, price_position,
                                    current_price, bb_*, sma_*}

Pre-computed bởi CODE (LLM không can thiệp):
    + signal_strength : float 0–3, weight theo SCORE RATIO của từng nguồn
    + data_quality    : int 0–3, số nguồn có dữ liệu
    + target_prices   : tp1_min, tp2_min, sl_max theo PERIOD
    + min_rr_required : tỷ lệ Reward:Risk tối thiểu theo period

LLM chỉ làm:
    + Chọn recommendation theo rule deterministic dựa trên signal + price_position
    + Chấm signal_consistency (0–3)
    + Sinh entry/exit_price_hint thỏa mãn target_prices + min_rr
    + Sinh tactical_suggestion với rủi ro phù hợp context recommendation
    + Trích key_evidence từ pre-computed signals (không bịa)

CONFIDENCE = 0.40 * signal_strength/3 + 0.35 * signal_consistency/3 + 0.25 * data_quality/3
"""

import json
from typing import Literal
from pydantic import BaseModel, Field

from agentic_ai.service.openai_service import _get_openai_client
from agentic_ai.analyze.state import AgentState


# ─────────────────────────────────────────────────────────────
# 🎯 Period-based profit targets — đảm bảo TP/SL realistic
# ─────────────────────────────────────────────────────────────

# Default theo period dùng KHI user không nhập target/max_loss
# (median VN-Index benchmark, không phải best case)
DEFAULT_TARGETS_BY_PERIOD = {
    "short_term": {"target_profit_pct": 10.0, "max_loss_pct": 5.0},
    "mid_term":   {"target_profit_pct": 20.0, "max_loss_pct": 10.0},
    "long_term":  {"target_profit_pct": 40.0, "max_loss_pct": 15.0},
}

# Floor / ceiling để chặn input vô lý từ user
TARGET_BOUNDS = {
    "target_profit_pct": (3.0, 200.0),   # tối thiểu 3%, tối đa 200%
    "max_loss_pct":      (2.0, 30.0),    # tối thiểu 2%, tối đa 30%
}

# RR sàn — kể cả user chấp nhận trade tệ, system không khuyến nghị
# Mua nếu reward < 1× risk (lỗ kỳ vọng > lời kỳ vọng)
MIN_RR_FLOOR = 1.0


def _normalize_period(risk_appetite: dict) -> str:
    """Chuẩn hóa period về short_term / mid_term / long_term."""
    raw = (risk_appetite.get("period") or risk_appetite.get("investment_horizon") or "")
    raw = str(raw).lower()
    if "short" in raw or "ngắn" in raw or "ngan" in raw:
        return "short_term"
    if "long" in raw or "dài" in raw or "dai" in raw:
        return "long_term"
    return "mid_term"


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _resolve_targets(risk_appetite: dict, period: str) -> dict:
    """
    Lấy target_profit_pct / max_loss_pct từ user, fallback theo period nếu thiếu.
    Clamp vào bounds hợp lệ. Trả về %.
    """
    defaults = DEFAULT_TARGETS_BY_PERIOD[period]

    try:
        target_profit_pct = float(risk_appetite.get("target_profit_pct"))
    except (TypeError, ValueError):
        target_profit_pct = defaults["target_profit_pct"]

    try:
        max_loss_pct = float(risk_appetite.get("max_loss_pct"))
    except (TypeError, ValueError):
        max_loss_pct = defaults["max_loss_pct"]

    target_profit_pct = _clamp(target_profit_pct, *TARGET_BOUNDS["target_profit_pct"])
    max_loss_pct      = _clamp(max_loss_pct,      *TARGET_BOUNDS["max_loss_pct"])

    return {
        "target_profit_pct": target_profit_pct,
        "max_loss_pct":      max_loss_pct,
    }


def _compute_target_prices(
    current_price: float | None,
    target_profit_pct: float,
    max_loss_pct: float,
) -> dict:
    """
    Tính TP1/TP2/SL từ kỳ vọng của user.
      TP2 = current * (1 + target_profit)  ← target user nhập, full exit
      TP1 = current * (1 + target_profit * 0.5)  ← partial exit ở giữa đường
      SL  = current * (1 - max_loss)
      min_rr = max(MIN_RR_FLOOR, target_profit / max_loss) — user tự quyết RR
    """
    if current_price is None or current_price <= 0:
        return {}

    tp1_pct = target_profit_pct * 0.5
    tp2_pct = target_profit_pct
    sl_pct  = max_loss_pct

    raw_rr = tp2_pct / sl_pct if sl_pct > 0 else MIN_RR_FLOOR
    min_rr = round(max(MIN_RR_FLOOR, raw_rr), 2)

    return {
        "tp1_min": round(current_price * (1 + tp1_pct / 100), 2),
        "tp2_min": round(current_price * (1 + tp2_pct / 100), 2),
        "sl_max":  round(current_price * (1 - sl_pct  / 100), 2),
        "min_rr":  min_rr,
        "tp1_pct": round(tp1_pct, 2),
        "tp2_pct": round(tp2_pct, 2),
        "sl_pct":  round(sl_pct, 2),
    }


# ─────────────────────────────────────────────────────────────
# 📦 Structured Output Schema
# ─────────────────────────────────────────────────────────────

class ConfidenceScores(BaseModel):
    signal_consistency: Literal[0, 1, 2, 3] = Field(
        description=(
            "Mức độ đồng thuận của các nguồn CÓ DỮ LIỆU với recommendation.\n"
            "  3 = Tất cả nguồn có dữ liệu đều ủng hộ\n"
            "  2 = Phần lớn ủng hộ, một nguồn trung lập\n"
            "  1 = Phần lớn ủng hộ, một nguồn trái chiều\n"
            "  0 = Các nguồn mâu thuẫn\n"
            "\n"
            "NGOẠI LỆ ngắn hạn: nếu recommendation dựa chủ yếu vào Technical,\n"
            "Fundamental trái chiều KHÔNG bị coi là 'trái chiều' — tính như trung lập."
        )
    )


class InvestmentRecommendation(BaseModel):
    summary: str = Field(
        description=(
            "Phân tích tổng thể CHI TIẾT — 7–12 câu, viết liền mạch như 1 đoạn văn\n"
            "(KHÔNG heading, KHÔNG bullet). BẮT BUỘC đủ 4 phần theo thứ tự:\n"
            "\n"
            "  [1] BỐI CẢNH CƠ BẢN — 2 câu (≥ 3 con số):\n"
            "      Câu 1: 2–3 chỉ số định giá/sinh lời có SỐ\n"
            "             (PE, ROE, P/B, EPS).\n"
            "      Câu 2: 1–2 chỉ số tăng trưởng/dòng tiền (revenue YoY, profit YoY, CFO)\n"
            "             KÈM sự kiện news quan trọng từ article.key_events\n"
            "             (insider mua/bán, target giá tổ chức, kết quả KD).\n"
            "             Nếu article.sentiment = 'KHÔNG CÓ TIN' → viết:\n"
            "             'không có tin tức đáng chú ý trong kỳ'.\n"
            "\n"
            "  [2] TÌNH HÌNH KỸ THUẬT — 3 câu (≥ 5 con số):\n"
            "      Câu 1: phân loại technical (BULLISH/BEARISH/TRUNG TÍNH) kèm\n"
            "             score X/9 và price_position.\n"
            "      Câu 2: 3 chỉ báo có SỐ — RSI=X, MACD state (so với Signal kèm số),\n"
            "             MACD Histogram. Thêm cross gần đây trong trend_info\n"
            "             (Golden/Death cross cách N nến) nếu có.\n"
            "      Câu 3: vị trí giá hiện tại so với SMA20, SMA50, upper/lower BB.\n"
            "\n"
            "  [3] LÝ DO RECOMMENDATION — 1–2 câu:\n"
            "      Giải thích tại sao 'Mua' / 'Chờ' dựa trên rule period.\n"
            "      Nếu period = short_term: BẮT BUỘC chứa cụm\n"
            "      'ưu tiên tín hiệu kỹ thuật, fundamental chỉ tham khảo'.\n"
            "\n"
            "  [4] HÀNH ĐỘNG TIẾP THEO — 1 câu:\n"
            "      Điều kiện CỤ THỂ cần theo dõi, có SỐ — đồng bộ entry_price_hint.\n"
            "\n"
            "TUYỆT ĐỐI KHÔNG bịa số ngoài input. Mọi con số phải lấy từ\n"
            "technical.{current_price, bb_*, sma_*, signals, trend_info},\n"
            "fundamental.signals/weaknesses, hoặc article.key_events."
        )
    )

    recommendation: Literal["Mua", "Chờ"] = Field(
        description="Hành động đề xuất. Chỉ có 'Mua' hoặc 'Chờ'."
    )

    key_evidence: list[str] = Field(
        description=(
            "3–5 bullet ngắn (mỗi bullet ≤ 25 từ).\n"
            "PHÂN BỔ BẮT BUỘC theo nguồn (nếu có data):\n"
            "  • ÍT NHẤT 1 bullet từ technical.signals/trend_info — luôn có nếu\n"
            "    technical.signal != NO_DATA\n"
            "  • ÍT NHẤT 1 bullet từ fundamental.signals/weaknesses — luôn có nếu\n"
            "    fundamental.signal != NO_DATA\n"
            "  • ÍT NHẤT 1 bullet từ article.key_events — BẮT BUỘC nếu\n"
            "    article.sentiment != 'KHÔNG CÓ TIN' VÀ key_events không rỗng\n"
            "CẤM bịa số liệu/sự kiện ngoài input."
        )
    )

    scores: ConfidenceScores

    entry_price_hint: str | None = Field(
        description=(
            "Vùng giá CỤ THỂ — BẮT BUỘC có SỐ thực (2 chữ số thập phân).\n"
            "CẤM viết chung chung như 'vùng hỗ trợ' / 'vùng kháng cự' /\n"
            "'theo dõi diễn biến giá' mà không có số.\n"
            "\n"
            "Dữ liệu cần dùng từ technical_analysis_agent:\n"
            "  current_price, bb_upper, bb_lower, sma_20, sma_50\n"
            "\n"
            "Format BẮT BUỘC: 'theo dõi vùng X.XX – Y.YY (<lý do kỹ thuật>)'\n"
            "                  hoặc 'có thể mua quanh X.XX – Y.YY (<lý do>)'\n"
            "\n"
            "Logic chọn vùng theo recommendation + price_position:\n"
            "  • 'Mua' + price_position ∈ {mid, near_support}:\n"
            "      vùng = [current_price × 0.98, current_price × 1.02]\n"
            "      lý do: 'gần giá hiện tại, hỗ trợ tại SMA20=<sma_20>'\n"
            "  • 'Chờ' + price_position = near_resistance (pullback):\n"
            "      vùng = [min(SMA20, lower_BB), max(SMA20, lower_BB)]\n"
            "      lý do: 'chờ pullback về SMA20=<sma_20> / lower BB=<bb_lower>'\n"
            "  • 'Chờ' + technical = BEARISH (chờ đảo chiều):\n"
            "      vùng = [lower_BB, SMA20]\n"
            "      lý do: 'chờ tín hiệu đảo chiều quanh lower BB=<bb_lower>\n"
            "             và xác nhận trên SMA20=<sma_20>'\n"
            "  • 'Chờ' + technical = TRUNG TÍNH:\n"
            "      vùng = [SMA20 × 0.98, SMA20 × 1.02]\n"
            "      lý do: 'theo dõi quanh SMA20=<sma_20>'\n"
            "\n"
            "Ví dụ ĐÚNG : 'Theo dõi vùng 26.40 – 26.80 (chờ tín hiệu đảo chiều\n"
            "              quanh lower BB=26.40 và xác nhận trên SMA20=26.80)'\n"
            "Ví dụ SAI  : 'Theo dõi nếu giá điều chỉnh về vùng hỗ trợ.'\n"
            "\n"
            "Trả None CHỈ KHI cả bb_lower, sma_20, current_price đều null."
        )
    )

    exit_price_hint: str | None = Field(
        description=(
            "TP/SL dạng chuỗi tự nhiên — chỉ khi 'Mua'.\n"
            "QUY TẮC BẮT BUỘC:\n"
            "  - TP1 PHẢI ≥ target_prices.tp1_min (system đã tính theo period)\n"
            "  - TP2 PHẢI ≥ target_prices.tp2_min nếu khoảng cách kỹ thuật cho phép\n"
            "  - SL KHÔNG được thấp hơn target_prices.sl_max\n"
            "  - (TP2 - entry) / (entry - SL) PHẢI ≥ target_prices.min_rr (RR ≥ 1:2)\n"
            "Nếu BB upper / đỉnh swing CAO HƠN tp1_min → dùng giá đó.\n"
            "Nếu CAO HƠN không có → vẫn dùng tp1_min với chú thích "
            "'target +X% theo period'.\n"
            "Format: 'TP1: <X> (<lý do kỹ thuật>) | TP2: <Y> (...) | SL: đóng cửa dưới <Z>'.\n"
            "None khi 'Chờ'."
        )
    )


# ─────────────────────────────────────────────────────────────
# 🧮 Pre-computed metrics
# ─────────────────────────────────────────────────────────────

def _has_data(src_data) -> bool:
    if not isinstance(src_data, dict):
        return bool(src_data)
    if src_data.get("signal") == "NO_DATA":
        return False
    if src_data.get("sentiment") == "KHÔNG CÓ TIN":
        return False
    return True


def _compute_data_quality(results: dict) -> int:
    sources = ["article_agent", "fundamental_analysis_agent", "technical_analysis_agent"]
    return sum(1 for src in sources if _has_data(results.get(src)))


# Sentiment → strength contribution (0–1)
_SENTIMENT_STRENGTH = {
    "TÍCH CỰC RÕ RÀNG": 1.0,
    "TIÊU CỰC RÕ RÀNG": 1.0,
    "TÍCH CỰC NHẸ":     0.4,
    "TIÊU CỰC NHẸ":     0.4,
    "TRUNG LẬP":        0.0,
    "KHÔNG CÓ TIN":     0.0,
}


def _compute_signal_strength(results: dict) -> float:
    """
    Weighted signal_strength ∈ [0.0, 3.0]:
    Mỗi nguồn đóng góp 0–1 theo MỨC ĐỘ mạnh của signal, không phải chỉ "có rõ ràng hay không".

      Technical BULLISH/BEARISH → tech.score / 9         (5/9 = 0.56)
      Fundamental TỐT          → fund.score / 5
      Fundamental YẾU          → (max - score) / 5       (đo độ "yếu" rõ ràng)
      News                     → mapping bảng _SENTIMENT_STRENGTH

    Tổng = tech + fund + article, max 3.0.
    """
    total = 0.0

    tech = results.get("technical_analysis_agent") or {}
    if isinstance(tech, dict):
        signal = tech.get("signal")
        score = tech.get("score") or 0
        mx = tech.get("max_score") or 9
        if mx > 0:
            if signal == "BULLISH":
                total += score / mx
            elif signal == "BEARISH":
                total += (mx - score) / mx

    fund = results.get("fundamental_analysis_agent") or {}
    if isinstance(fund, dict):
        signal = fund.get("signal")
        score = fund.get("score") or 0
        mx = fund.get("max_score") or 5
        if mx > 0:
            if signal == "TỐT":
                total += score / mx
            elif signal == "YẾU":
                total += (mx - score) / mx

    article = results.get("article_agent") or {}
    if isinstance(article, dict):
        total += _SENTIMENT_STRENGTH.get(article.get("sentiment"), 0.0)

    return round(min(3.0, total), 3)


# ─────────────────────────────────────────────────────────────
# 🧮 Confidence
# ─────────────────────────────────────────────────────────────

WEIGHTS = {
    "signal_strength":    0.40,
    "signal_consistency": 0.35,
    "data_quality":       0.25,
}

MAX_VALUES = {
    "signal_strength":    3,
    "signal_consistency": 3,
    "data_quality":       3,
}


def calculate_confidence(signal_strength: float, signal_consistency: int, data_quality: int) -> float:
    confidence = (
        (signal_strength    / MAX_VALUES["signal_strength"])    * WEIGHTS["signal_strength"]
        + (signal_consistency / MAX_VALUES["signal_consistency"]) * WEIGHTS["signal_consistency"]
        + (data_quality       / MAX_VALUES["data_quality"])       * WEIGHTS["data_quality"]
    )
    return round(min(1.0, confidence), 2)


# ─────────────────────────────────────────────────────────────
# 🧠 System Prompt
# ─────────────────────────────────────────────────────────────

AGGREGATOR_SYSTEM_PROMPT = """
Bạn là chuyên gia phân tích chứng khoán Việt Nam với kinh nghiệm thực tế.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DỮ LIỆU ĐẦU VÀO — đã PRE-CLASSIFIED bởi hệ thống
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Bạn TUYỆT ĐỐI KHÔNG đếm/chấm lại tín hiệu thô — chỉ dùng các trường có sẵn:

▸ technical_analysis_agent:
    signal         : BULLISH | TRUNG TÍNH | BEARISH | NO_DATA
    score          : 0–9
    signals        : danh sách tín hiệu bullish đã detect
    trend_info     : {rsi_direction, macd_momentum, macd_cross, sma_cross, divergence}
    price_position : near_resistance | near_support | mid | unknown
    current_price, bb_upper, bb_lower, sma_20, sma_50

▸ fundamental_analysis_agent:
    signal         : TỐT | TRUNG BÌNH | YẾU | DỮ LIỆU THIẾU | NO_DATA
    score          : 0–5
    signals, weaknesses, is_bank_or_finance

▸ article_agent:
    sentiment      : TÍCH CỰC RÕ RÀNG | TÍCH CỰC NHẸ | TRUNG LẬP
                   | TIÊU CỰC NHẸ | TIÊU CỰC RÕ RÀNG | KHÔNG CÓ TIN
    summary, key_events

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUY TẮC QUYẾT ĐỊNH RECOMMENDATION (deterministic)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BƯỚC 1 — đọc period từ risk_appetite và áp rule TƯƠNG ỨNG.

━━━━ NGẮN HẠN (period = short_term / ngắn hạn) ━━━━
Technical là YẾU TỐ QUYẾT ĐỊNH. Fundamental chỉ tham khảo bối cảnh.

  technical.signal = BULLISH:
    + price_position = "mid" hoặc "near_support":
        → recommendation = "Mua"
        → entry quanh current_price ± 2%
    + price_position = "near_resistance":
        → recommendation = "Chờ"  ⚠️ BẮT BUỘC, KHÔNG ĐƯỢC Mua dù score cao
        → entry hint: vùng pullback về SMA20 / lower BB
        → Lý do: vào ở đỉnh sẽ vi phạm min_rr — chờ pullback để có RR đẹp hơn
    + price_position = "unknown":
        → recommendation = "Mua" với entry thận trọng (gần current_price)
    + NGOẠI LỆ: article.sentiment = "TIÊU CỰC RÕ RÀNG" → "Chờ" (bất kể technical)

  technical.signal = BEARISH:
    → "Chờ" (bất kể fundamental tốt đến đâu)

  technical.signal = TRUNG TÍNH:
    + price_position = "near_resistance":
      → "Chờ" (BẮT BUỘC — không mua đuổi dù momentum tốt,
       vì RR sau khi vào sẽ kém do giá đã sát đỉnh range)
    + Có Golden Cross MACD ≤ 3 nến HOẶC macd_momentum = "tăng mạnh dần",
      VÀ price_position ∈ {mid, near_support}:
      → "Mua" (entry thận trọng quanh current_price)
    + Ngược lại → "Chờ"

  technical.signal = NO_DATA:
    → "Chờ"

━━━━ TRUNG/DÀI HẠN (period = mid_term / long_term) ━━━━
Cân bằng cả 3 nguồn:

  "Mua" = technical BULLISH + fundamental TỐT/TRUNG BÌNH + news ≥ TRUNG LẬP
  "Mua" = technical BULLISH + fundamental TỐT (kể cả news TIÊU CỰC NHẸ)
  "Chờ" = technical BEARISH (bất kể nguồn khác)
  "Chờ" = technical TRUNG TÍNH + fundamental YẾU + news TIÊU CỰC
  "Chờ" = news TIÊU CỰC RÕ RÀNG

━━━━ ĐIỀU CHỈNH THEO risk_tolerance ━━━━
  cautious   → technical.signal = BULLISH chỉ khi score ≥ 6/9 (siết chặt). Score 5/9
               vẫn coi là TRUNG TÍNH.
  balanced   → giữ ngưỡng mặc định 5/9 cho BULLISH.
  aggressive → chấp nhận score ≥ 4/9 coi như BULLISH (mở rộng).

━━━━ ĐIỀU CHỈNH THEO preference ━━━━
  growth   → khi cân nhắc "Mua" trung/dài hạn, ưu tiên fundamental signal = TỐT.
             Nếu fundamental = YẾU mà period > short_term → nghiêng "Chờ".
  income   → ưu tiên ROE cao (>15%), CFO dương, cổ tức ổn định trong
             fundamental.signals. Nếu thiếu các yếu tố này → nghiêng "Chờ".
  balanced → không điều chỉnh.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUY TẮC ENTRY / EXIT PRICE — bắt buộc theo target_prices
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hệ thống cung cấp `target_prices` (đã tính theo period):
    tp1_min  = current_price * (1 + tp1_pct)
    tp2_min  = current_price * (1 + tp2_pct)
    sl_max   = current_price * (1 - sl_pct)
    min_rr   = tỷ lệ Reward:Risk tối thiểu

Khi recommendation = "Mua":
  entry:
    - price_position = "mid" / "near_support": entry quanh current_price (vùng ±1–2%)
    - price_position = "unknown": entry hẹp quanh current_price
  TP1:
    - Lấy max(tp1_min, upper BB nếu CAO HƠN tp1_min)
    - Nếu BB upper THẤP HƠN tp1_min → vẫn dùng tp1_min và chú thích
      "(target +X% theo khẩu vị, vượt qua upper BB)"
  TP2:
    - Lấy max(tp2_min, đỉnh swing/MA kháng cự lớn hơn)
    - Nếu không có cơ sở kỹ thuật → chỉ điền tp2_min với chú thích
  SL:
    - Dùng dạng ĐIỀU KIỆN: "đóng cửa dưới <giá>"
    - <giá> = max(sl_max, SMA50 / lower BB / đáy swing gần nhất)
    - KHÔNG được < sl_max

  KIỂM TRA RR cuối cùng (dùng TP2 vì TP1 thường là partial exit):
    rr = (TP2 - entry) / (entry - SL)
    Nếu rr < target_prices.min_rr → ĐỔI recommendation thành "Chờ" và
    để exit_price_hint = None

Khi recommendation = "Chờ":
  entry: vùng pullback ("theo dõi nếu giá điều chỉnh về …")
  exit_price_hint: None (chưa vào lệnh thì chưa có exit)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SIGNAL_CONSISTENCY (0–3) — chỉ chấm phần này
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Dựa trên recommendation đã chọn:
  3 = Tất cả nguồn có dữ liệu ủng hộ recommendation
  2 = Phần lớn ủng hộ, một nguồn trung lập
  1 = Phần lớn ủng hộ, một nguồn trái chiều
  0 = Mâu thuẫn

NGOẠI LỆ ngắn hạn: Fundamental trái chiều với Technical → coi như TRUNG LẬP.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KEY_EVIDENCE — 3–5 bullet trích từ pre-computed
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CẤM:
  - Bịa số liệu (PE, ROE, %, mức giá không có trong input)
  - Cường điệu hóa (RSI=54 → KHÔNG nói "đà tăng mạnh")
  - Trích từ news ngoài key_events

ĐƯỢC:
  - Trích nguyên văn từ technical.signals[], trend_info{}, fundamental.signals[],
    fundamental.weaknesses[], article.key_events[]
  - Diễn giải ngắn các số đã có trong input

Reasoning PHẢI dựa trên các bullet này — không tự thêm thông tin.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUMMARY — gộp bối cảnh + lý do recommendation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary là field DUY NHẤT chứa giải thích cho user. Phải gồm:
  • Bối cảnh cổ phiếu (fundamental nổi bật, news quan trọng)
  • Tình hình kỹ thuật (signal, price_position)
  • Lý do recommendation — trích từ key_evidence
  • Với khẩu vị ngắn hạn: PHẢI nói rõ "ưu tiên tín hiệu kỹ thuật"

Viết liền mạch như 1 đoạn văn 3–5 câu. KHÔNG dùng heading, KHÔNG bullet.
KHÔNG trùng lặp với key_evidence (key_evidence là dữ kiện rời, summary là diễn giải).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


# ─────────────────────────────────────────────────────────────
# 🚀 Aggregator Agent
# ─────────────────────────────────────────────────────────────

def aggregator_agent(state: AgentState) -> AgentState:
    mode = state.get("mode", "auto")
    print(f"[Aggregator] Tổng hợp kết quả (mode={mode})...")

    client = _get_openai_client()

    results       = state.get("agent_results", {})
    risk_appetite = state.get("risk_appetite", {})
    user_input    = state.get("user_input", "")

    # ─── Pre-compute objective scores + targets ───
    period          = _normalize_period(risk_appetite)
    data_quality    = _compute_data_quality(results)
    signal_strength = _compute_signal_strength(results)

    tech = results.get("technical_analysis_agent") or {}
    current_price = tech.get("current_price") if isinstance(tech, dict) else None
    price_position = tech.get("price_position", "unknown") if isinstance(tech, dict) else "unknown"

    # Targets từ user (fallback theo period nếu thiếu)
    user_targets = _resolve_targets(risk_appetite, period)
    target_prices = _compute_target_prices(
        current_price,
        user_targets["target_profit_pct"],
        user_targets["max_loss_pct"],
    )

    # Khẩu vị bổ sung — đưa vào prompt nếu user cung cấp
    risk_tolerance = str(risk_appetite.get("risk_tolerance") or "balanced").lower()
    preference     = str(risk_appetite.get("preference")     or "balanced").lower()

    analysis_message = f"""
DỮ LIỆU PHÂN TÍCH (đã pre-classified):

{json.dumps(results, ensure_ascii=False, indent=2)}

────────────────────────
PRE-COMPUTED SCORES (do hệ thống tính, KHÔNG đếm lại):

- period:           "{period}"
- signal_strength:  {signal_strength}/3.0 (weighted theo score ratio)
- data_quality:     {data_quality}/3
- price_position:   "{price_position}"
- risk_tolerance:   "{risk_tolerance}"  (cautious | balanced | aggressive)
- preference:       "{preference}"      (growth | income | balanced)

────────────────────────
TARGET PRICES — đã lấy từ kỳ vọng USER (hard constraint cho entry/exit):

User nhập:
  target_profit_pct: {user_targets["target_profit_pct"]}%
  max_loss_pct:      {user_targets["max_loss_pct"]}%

Tính ra:
{json.dumps(target_prices, ensure_ascii=False, indent=2) if target_prices else "(chưa có current_price — không tính được)"}

────────────────────────
KHẨU VỊ RỦI RO (RAW từ user, chỉ để tham chiếu):

{json.dumps(risk_appetite, ensure_ascii=False, indent=2)}

────────────────────────
YÊU CẦU:

{user_input}
"""

    try:
        response = client.beta.chat.completions.parse(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": AGGREGATOR_SYSTEM_PROMPT},
                {"role": "user",   "content": analysis_message},
            ],
            response_format=InvestmentRecommendation,
        )

        parsed: InvestmentRecommendation = response.choices[0].message.parsed

        signal_consistency = parsed.scores.signal_consistency
        confidence = calculate_confidence(signal_strength, signal_consistency, data_quality)

        output = {
            "summary":         parsed.summary,
            "recommendation":  parsed.recommendation,
            "key_evidence":    parsed.key_evidence,
            "confidence":      confidence,
            "confidence_breakdown": {
                "signal_strength":    signal_strength,
                "signal_consistency": signal_consistency,
                "data_quality":       data_quality,
                "signal_strength_contribution":    round(
                    signal_strength / MAX_VALUES["signal_strength"] * WEIGHTS["signal_strength"], 3
                ),
                "signal_consistency_contribution": round(
                    signal_consistency / MAX_VALUES["signal_consistency"] * WEIGHTS["signal_consistency"], 3
                ),
                "data_quality_contribution":       round(
                    data_quality / MAX_VALUES["data_quality"] * WEIGHTS["data_quality"], 3
                ),
            },
            "entry_price_hint":    parsed.entry_price_hint,
            "exit_price_hint":     parsed.exit_price_hint,
            "meta": {
                "period":         period,
                "price_position": price_position,
                "risk_tolerance": risk_tolerance,
                "preference":     preference,
                "user_targets":   user_targets,
                "target_prices":  target_prices,
            },
        }

        print("[Aggregator] Output:")
        print(json.dumps(output, ensure_ascii=False, indent=2))

        return {"final_output": output}

    except Exception as e:
        print(f"[Aggregator] Error: {str(e)}")

        fallback = {
            "summary":         "Lỗi hệ thống — không thể phân tích dữ liệu lúc này. Vui lòng thử lại sau.",
            "recommendation":  "Chờ",
            "key_evidence":    [],
            "confidence":      0.0,
            "entry_price_hint": None,
            "exit_price_hint":  None,
        }

        return {"error": str(e), "final_output": fallback}
