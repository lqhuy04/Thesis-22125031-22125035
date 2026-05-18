"""
aggregator.py — Aggregator Agent

Tổng hợp dữ liệu từ:
    + article_agent
    + fundamental_analysis_agent
    + technical_analysis_agent

Chỉ trả về "Mua" hoặc "Chờ" — không hỗ trợ short/bán khống.

────────────────────────────────────────────────────────
THIẾT KẾ CONFIDENCE:

  Confidence = f(signal_strength, signal_consistency, data_quality)

  Hoàn toàn độc lập với chiều Mua/Chờ của recommendation.
  Câu hỏi confidence trả lời:
    "Các nguồn thông tin có đủ bằng chứng rõ ràng và đồng thuận
     với recommendation được đưa ra không?"

  Công thức:
    confidence = signal_strength   * 0.35
               + signal_consistency * 0.35
               + data_quality       * 0.30

  Lý do tăng trọng số data_quality lên 0.30:
    Nếu dữ liệu rỗng/sơ sài, confidence không nên cao dù LLM
    chấm signal_strength và signal_consistency cao.

  Mỗi thành phần chuẩn hóa về [0, 1] trước khi nhân trọng số.

  data_quality được tính từ CODE (đếm khách quan số nguồn có dữ liệu),
  không để LLM tự chấm — tránh circular reasoning.
────────────────────────────────────────────────────────
"""

import json
from typing import Literal
from pydantic import BaseModel, Field

from agentic_ai.service.openai_service import _get_openai_client
from agentic_ai.analyze.state import AgentState


# ─────────────────────────────────────────────────────────────
# 📦 Structured Output Schema
# ─────────────────────────────────────────────────────────────

class ConfidenceScores(BaseModel):
    """
    Hai chiều đánh giá do LLM chấm.
    data_quality do CODE tính khách quan — không có trong schema này.
    """

    signal_strength: Literal[0, 1, 2, 3] = Field(
        description=(
            "Số nguồn có tín hiệu RÕ RÀNG — tín hiệu không mơ hồ, không thiếu dữ liệu quan trọng.\n"
            "Đếm độc lập với chiều Mua/Chờ:\n"
            "  3 = Tất cả các nguồn đều có tín hiệu rõ ràng\n"
            "  2 = Phần lớn các nguồn có tín hiệu rõ ràng\n"
            "  1 = Chỉ một nguồn có tín hiệu rõ ràng\n"
            "  0 = Không nguồn nào có tín hiệu rõ ràng\n"
            "\n"
            "Tiêu chí 'rõ ràng' cho từng nguồn:\n"
            "  Technical: ≥50% chỉ báo đồng thuận một chiều (bullish hoặc bearish)\n"
            "  Fundamental: ≥50% chỉ số đánh giá được ở mức tốt hoặc xấu rõ ràng\n"
            "  News: sentiment rõ ràng tích cực hoặc tiêu cực (không trung lập)"
        )
    )

    signal_consistency: Literal[0, 1, 2, 3] = Field(
    description=(
        "Mức độ đồng thuận của các nguồn CÓ DỮ LIỆU với recommendation.\n"
        "  3 = Tất cả nguồn có dữ liệu đều ủng hộ\n"
        "  2 = Phần lớn ủng hộ, một nguồn trung lập\n"
        "  1 = Phần lớn ủng hộ, một nguồn trái chiều\n"
        "  0 = Các nguồn mâu thuẫn nhau\n"
    )
)


class InvestmentRecommendation(BaseModel):
    summary: str = Field(
        description=(
            "Phân tích tổng thể tình hình cổ phiếu từ các nguồn có dữ liệu: "
            "tin tức, phân tích cơ bản, kỹ thuật. "
            "Nêu các điểm nổi bật, không liệt kê lại toàn bộ số liệu."
        )
    )

    recommendation: Literal["Mua", "Chờ"] = Field(
        description=(
            "Hành động đề xuất. Chỉ có 2 lựa chọn:\n"
            "  'Mua'  = Tín hiệu đủ rõ ràng và tích cực để xem xét vào lệnh\n"
            "  'Chờ' = Tín hiệu mixed, yếu, hoặc tiêu cực — không nên vào lệnh lúc này"
        )
    )

    reasoning: str = Field(
        description=(
            "Giải thích logic rõ ràng cho recommendation, có dẫn chứng số liệu cụ thể. "
            "Giải thích tại sao chấm signal_strength và signal_consistency như vậy."
        )
    )

    scores: ConfidenceScores

    entry_price_hint: str | None = Field(
        description=(
            "Vùng giá vào lệnh hoặc vùng theo dõi, dạng chuỗi tự nhiên.\n"
            "Nếu recommendation = 'Mua': vùng giá xem xét mua vào ngay.\n"
            "  Ví dụ: 'Có thể xem xét mua ở vùng 45,000–47,000 (gần MA20 và lower BB)'\n"
            "Nếu recommendation = 'Chờ': vùng giá cần về để xem xét vào lệnh (nếu đủ dữ liệu kỹ thuật).\n"
            "  Ví dụ: 'Theo dõi nếu giá điều chỉnh về vùng 43,000–45,000 (support MA50)'\n"
            "None nếu không đủ dữ liệu kỹ thuật để xác định vùng hỗ trợ."
        )
    )

    exit_price_hint: str | None = Field(
        description=(
            "Vùng chốt lời và mức cắt lỗ tham khảo, dạng chuỗi tự nhiên.\n"
            "Chỉ điền nếu recommendation = 'Mua' VÀ đã có entry_price_hint.\n"
            "Ví dụ: 'TP1: 52,000 (upper BB) | TP2: 56,000 (đỉnh swing) | SL: đóng cửa dưới 43,000'\n"
            "None nếu recommendation = 'Chờ' — chưa vào lệnh thì chưa cần exit."
        )
    )

    tactical_suggestion: str = Field(
    description=(
        "Gợi ý chiến thuật bổ sung. PHẢI bao gồm đủ 4 phần theo thứ tự:\n"
        "  1. Khung thời gian phù hợp với khẩu vị rủi ro của user\n"
        "  2. 1–2 rủi ro CỤ THỂ từ data (không nói chung chung, phải dẫn số liệu)\n"
        "  3. Điều kiện re-evaluate:\n"
        "     - Nếu recommendation = 'Chờ': PHẢI dùng ĐÚNG vùng giá trong entry_price_hint.\n"
        "       Ví dụ: nếu entry_price_hint = 'theo dõi vùng 25.00–26.00' thì\n"
        "       điều kiện re-evaluate là 'nếu giá về vùng 25.00–26.00 VÀ ...'\n"
        "     - Nếu recommendation = 'Mua': PHẢI dùng ĐÚNG mức TP/SL trong exit_price_hint.\n"
        "       Ví dụ: nếu exit_price_hint = 'TP1: 30.00 | TP2: 32.00 | SL: đóng cửa dưới 27.00' thì\n"
        "       tactical_suggestion phải nhắc lại đúng các mức này, không được tự đặt số khác.\n"
        "     KHÔNG được tự đặt mức giá khác với entry_price_hint hoặc exit_price_hint.\n"
        "  4. Disclaimer: 'Đây là gợi ý tham khảo, không phải lời khuyên đầu tư. "
        "Quyết định cuối cùng thuộc về nhà đầu tư.'"
    )
)


# ─────────────────────────────────────────────────────────────
# 🧮 Tính data_quality từ code (khách quan, không để LLM tự chấm)
# ─────────────────────────────────────────────────────────────

def _compute_data_quality(results: dict) -> int:
    """
    Đếm số nguồn có dữ liệu thực sự (không rỗng/None/lỗi).
    Trả về 0, 1, hoặc 2 — chuẩn hóa thành [0, 1] khi tính confidence.

    2 = ≥2 nguồn có dữ liệu
    1 = đúng 1 nguồn có dữ liệu
    0 = không nguồn nào có dữ liệu
    """
    sources = ["article_agent", "fundamental_analysis_agent", "technical_analysis_agent"]
    count = 0
    for src in sources:
        data = results.get(src)
        if data and data not in ({}, [], "", None):
            count += 1
    return min(count, 2)  # cap ở 2


# ─────────────────────────────────────────────────────────────
# 🧮 Tính confidence tổng hợp
# ─────────────────────────────────────────────────────────────

WEIGHTS = {
    "signal_strength":    0.40,  # tăng — đây là chỉ số quan trọng nhất
    "signal_consistency": 0.35,  # giữ
    "data_quality":       0.25,  # giảm nhẹ — data_quality giờ granular hơn
}

MAX_VALUES = {
    "signal_strength":    3,
    "signal_consistency": 3,
    "data_quality":       3,  # 3 nguồn tối đa
}


def calculate_confidence(scores: ConfidenceScores, data_quality: int) -> float:
    """
    Tính confidence ∈ [0.0, 1.0].

    signal_strength và signal_consistency do LLM chấm.
    data_quality do code tính khách quan.
    """
    confidence = (
        (scores.signal_strength    / MAX_VALUES["signal_strength"])    * WEIGHTS["signal_strength"]
        + (scores.signal_consistency / MAX_VALUES["signal_consistency"]) * WEIGHTS["signal_consistency"]
        + (data_quality              / MAX_VALUES["data_quality"])       * WEIGHTS["data_quality"]
    )
    return round(min(1.0, confidence), 2)


# ─────────────────────────────────────────────────────────────
# 🧠 System Prompt
# ─────────────────────────────────────────────────────────────

AGGREGATOR_SYSTEM_PROMPT = """
Bạn là chuyên gia phân tích chứng khoán Việt Nam với kinh nghiệm thực tế.

Nhiệm vụ:
- Tổng hợp dữ liệu từ các nguồn được cung cấp (nếu có):
    1. Tin tức (article_agent)
    2. Phân tích cơ bản (fundamental_analysis_agent)
    3. Phân tích kỹ thuật (technical_analysis_agent)
- Đưa ra recommendation CHỈ gồm "Mua" hoặc "Chờ"
- Đánh giá KHÁCH QUAN, không thiên vị "Chờ" — nếu tín hiệu đủ rõ thì mạnh dạn khuyến nghị "Mua"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHẦN I — ĐỌC TÍN HIỆU
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A. KỸ THUẬT

RSI (14):
  < 30    → oversold, có thể hồi — bullish nhẹ
  30–45   → yếu — bearish
  45–55   → trung lập
  55–70   → mạnh — bullish
  > 70    → overbought — cảnh báo điều chỉnh

MACD:
  macd > signal và histogram > 0    → bullish, động lượng mạnh
  macd < signal và histogram < 0    → bearish, động lượng yếu
  giao cắt lên signal               → tín hiệu Mua
  giao cắt xuống signal             → tín hiệu thận trọng

Bollinger Bands:
  Giá gần upper BB → mạnh, nhưng cảnh báo không mua đuổi
  Giá gần lower BB → yếu, có thể tìm điểm hồi
  Giá trong vùng giữa BB + xu hướng tăng → tích cực, còn dư địa tăng

Moving Average:
  Giá > MA20 → ngắn hạn tích cực | < MA20 → yếu
  Giá > MA50 → trung hạn tốt    | < MA50 → xấu
  MA20 > MA50 (Golden Cross)  → bullish mạnh
  MA20 < MA50 (Death Cross)   → bearish mạnh

KDJ:
  K, D, J < 20 → oversold — bullish tiềm năng
  K, D, J > 80 → overbought — thận trọng
  K cắt lên D  → bullish  | cắt xuống → thận trọng

────────────────────────────────────────────────────────
ĐẾM ĐIỂM KỸ THUẬT (dùng để quyết định bullish/bearish):

Mỗi tín hiệu sau tính 1 điểm bullish:
  + RSI trong vùng 45–70
  + RSI < 30 (oversold, tiềm năng hồi)
  + MACD > Signal
  + Histogram > 0
  + Giá > SMA20
  + SMA20 > SMA50
  + Giá trong vùng giữa BB (không quá mua, còn dư địa)
  + KDJ K < 20 (oversold)
  + KDJ K cắt lên D

≥ 5/9 điểm bullish → Technical BULLISH
3–4/9 điểm         → Technical TRUNG TÍNH
< 3/9 điểm         → Technical BEARISH

────────────────────────────────────────────────────────
B. CƠ BẢN

Định giá  : PE < 10 rẻ (tốt) / 10–18 hợp lý (trung tính) / > 20 đắt (xấu)
Sinh lời  : ROE > 20% rất tốt / 15–20% tốt / 10–15% trung bình / < 10% yếu
Đòn bẩy   : D/E < 0.5 an toàn / 0.5–1.5 chấp nhận được / > 1.5 cần theo dõi
Tăng trưởng: doanh thu & lợi nhuận tăng YoY → tích cực

⚠️ Với ngành ngân hàng/bất động sản: D/E cao là đặc thù ngành,
   KHÔNG tự động coi là rủi ro nếu ROE và dòng tiền vẫn tốt.

ĐẾM ĐIỂM CƠ BẢN:
  + PE < 18 → tốt
  + ROE > 15% → tốt
  + Doanh thu tăng YoY → tốt
  + Lợi nhuận tăng YoY → tốt
  + CFO > 0 → tốt

≥ 3/5 điểm → Fundamental TỐT
2/5 điểm   → Fundamental TRUNG BÌNH
< 2/5 điểm → Fundamental YẾU

────────────────────────────────────────────────────────
C. TIN TỨC

Tích cực rõ ràng : tăng trưởng, cổ tức, mở rộng, mua vào của insider
Tích cực nhẹ    : tin ngành tốt, vĩ mô ổn định
Trung lập        : tin thị trường chung, không ảnh hưởng trực tiếp
Tiêu cực nhẹ    : áp lực ngành, vĩ mô bất lợi
Tiêu cực rõ ràng: thua lỗ, bán ròng mạnh, kiện tụng, vi phạm

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHẦN II — QUYẾT ĐỊNH RECOMMENDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Chỉ có 2 lựa chọn: "Mua" hoặc "Chờ"

NGUYÊN TẮC CHÍNH:
  "Mua"  = Technical BULLISH + (Fundamental TỐT hoặc News ít nhất trung lập)
  "Mua"  = Technical BULLISH + Fundamental TỐT (kể cả khi News tiêu cực nhẹ)
  "Chờ" = Technical BEARISH bất kể các nguồn khác
  "Chờ" = Technical TRUNG TÍNH + Fundamental YẾU + News tiêu cực
  "Chờ" = News tiêu cực RÕ RÀNG (thua lỗ, vi phạm, bán ròng mạnh)

⚠️ KHÔNG tự động chọn "Chờ" chỉ vì có một yếu tố rủi ro.
   Mọi cổ phiếu đều có rủi ro — nhiệm vụ là cân bằng tổng thể.

VÍ DỤ "MUA":
  RSI=54, MACD>Signal, histogram>0, SMA20>SMA50, giá trong BB
  → 5/9 điểm bullish → Technical BULLISH
  PE=9.79 (tốt), ROE=18% (tốt), doanh thu +50% (tốt), CFO>0 (tốt)
  → 4/5 điểm → Fundamental TỐT
  News: trung lập → không chặn
  → Recommendation: "Mua" ✓

VÍ DỤ "CHỜ":
  RSI=37, MACD<Signal, SMA20<SMA50
  → 1/9 điểm bullish → Technical BEARISH
  → Recommendation: "Chờ" dù Fundamental tốt ✓

Điều chỉnh theo khẩu vị rủi ro:
  Ngắn hạn          → ưu tiên Technical, chấp nhận Fundamental trung bình
  Rủi ro thấp       → cần thêm 1 điểm bullish so với ngưỡng thông thường
  Thu nhập thụ động → ưu tiên ROE cao, CFO dương, cổ tức ổn định

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHẦN III — CHẤM ĐIỂM CONFIDENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ NGUYÊN TẮC CỐT LÕI:
Confidence đo MỨC ĐỘ TIN CẬY vào recommendation, không đo chiều tích cực/tiêu cực.
"Chờ" với đủ bằng chứng rõ ràng → confidence CAO.
"Mua" với dữ liệu mơ hồ → confidence THẤP.

LƯU Ý: data_quality được hệ thống tính tự động từ code — bạn KHÔNG cần chấm điểm này.
Bạn chỉ chấm signal_strength và signal_consistency.

────────────────────────────────────────────────────────
1. SIGNAL_STRENGTH (0–3): Số nguồn có tín hiệu RÕ RÀNG

  [Technical rõ ràng]: ≥ 5/9 điểm bullish HOẶC < 3/9 điểm (bearish rõ)
  [Fundamental rõ ràng]: ≥ 3/5 điểm TỐT hoặc < 2/5 điểm YẾU rõ ràng
  [News rõ ràng]: sentiment tích cực hoặc tiêu cực RÕ RÀNG (trung lập không tính)

  → signal_strength = số nguồn đạt tiêu chí (0, 1, 2, hoặc 3)

────────────────────────────────────────────────────────
2. SIGNAL_CONSISTENCY (0–2): Đồng thuận với recommendation

  2 = Tất cả nguồn có dữ liệu đều ủng hộ recommendation
  1 = Phần lớn ủng hộ, một nguồn trái chiều hoặc trung lập
  0 = Các nguồn mâu thuẫn, recommendation là best guess trong uncertainty

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHẦN IV — ENTRY / EXIT PRICE HINT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

entry_price_hint — LUÔN CỐ GẮNG ĐIỀN nếu có đủ dữ liệu kỹ thuật:

  Nếu recommendation = "Mua":
    → Vùng giá xem xét vào lệnh ngay
    → Dựa trên: lower BB, MA20, MA50, đáy swing gần nhất
    → Ngôn ngữ theo confidence:
        ≥ 0.7 → "Có thể xem xét mua ở vùng X–Y (lý do kỹ thuật)"
        0.4–0.7 → "Nếu giá giữ trên vùng X–Y, có thể xem xét"
        < 0.4  → None
    → Nếu giá đang gần upper BB hoặc RSI > 65 → cảnh báo "không mua đuổi, chờ giá về vùng X–Y"

  Nếu recommendation = "Chờ":
    → Vùng giá cần về để có thể xem xét vào lệnh (điều kiện re-entry)
    → Dựa trên: support gần nhất (lower BB, MA50, đáy swing)
    → Ngôn ngữ rõ ràng là "theo dõi" chứ không phải "mua ngay"
    → None nếu không đủ dữ liệu kỹ thuật để xác định vùng hỗ trợ

exit_price_hint:
  - Chỉ điền nếu recommendation = "Mua" VÀ đã có entry_price_hint
  - Gồm: take profit (TP1, TP2 nếu có) và stop loss (SL)
  - TP dựa trên: upper BB, đỉnh swing, MA kháng cự gần nhất
  - SL dựa trên ĐIỀU KIỆN: "đóng cửa dưới X" thay vì chỉ nêu mức giá
  - Mọi con số phải có trong dữ liệu đầu vào — KHÔNG bịa
  - None nếu recommendation = "Chờ"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHẦN V — TACTICAL SUGGESTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

tactical_suggestion PHẢI bao gồm đủ 4 phần theo thứ tự:
  1. Khung thời gian phù hợp với khẩu vị rủi ro của user
  2. 1–2 rủi ro CỤ THỂ từ data (không nói chung chung, phải dẫn số liệu)
  3. Điều kiện cụ thể để re-evaluate (giá bao nhiêu, chỉ báo nào cần đổi chiều)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUY TẮC BẮT BUỘC:
  ✓ Không bịa số liệu ngoài dữ liệu được cung cấp
  ✓ Nếu nguồn nào không có dữ liệu → bỏ qua, không suy đoán
  ✓ exit_price_hint luôn = None khi recommendation = "Chờ"
  ✓ entry_price_hint khi "Chờ" dùng ngôn ngữ "theo dõi", không phải "mua"
  ✓ KHÔNG thiên vị "Chờ" — đánh giá khách quan theo điểm số
  ✓ Mức giá trong tactical_suggestion PHẢI nhất quán với entry_price_hint (khi Chờ) 
    và exit_price_hint (khi Mua) — không được tự đặt số khác
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


# ─────────────────────────────────────────────────────────────
# 🚀 Aggregator Agent
# ─────────────────────────────────────────────────────────────

def aggregator_agent(state: AgentState) -> AgentState:
    mode = state.get("mode", "auto")
    print(f"[Aggregator] Tổng hợp kết quả (mode={mode})...")

    client = _get_openai_client()

    results      = state.get("agent_results", {})
    risk_appetite = state.get("risk_appetite", {})
    user_input   = state.get("user_input", "")

    # Tính data_quality từ code — không để LLM tự chấm
    data_quality = _compute_data_quality(results)

    analysis_message = f"""
DỮ LIỆU PHÂN TÍCH:

{json.dumps(results, ensure_ascii=False, indent=2)}

────────────────────────
KHẨU VỊ RỦI RO:

{json.dumps(risk_appetite, ensure_ascii=False, indent=2)}

────────────────────────
YÊU CẦU:

{user_input}
"""

    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": AGGREGATOR_SYSTEM_PROMPT},
                {"role": "user",   "content": analysis_message},
            ],
            response_format=InvestmentRecommendation,
        )

        parsed: InvestmentRecommendation = response.choices[0].message.parsed

        # Confidence: signal_strength + signal_consistency từ LLM, data_quality từ code
        confidence = calculate_confidence(parsed.scores, data_quality)

        output = {
            "summary":         parsed.summary,
            "recommendation":  parsed.recommendation,
            "reasoning":       parsed.reasoning,
            "confidence":      confidence,
            "confidence_breakdown": {
                # Điểm gốc
                "signal_strength":    parsed.scores.signal_strength,     # 0–3 (LLM)
                "signal_consistency": parsed.scores.signal_consistency,  # 0–2 (LLM)
                "data_quality":       data_quality,                      # 0–2 (code)
                # Đóng góp sau chuẩn hóa và nhân trọng số
                "signal_strength_contribution":    round(
                    parsed.scores.signal_strength / MAX_VALUES["signal_strength"] * WEIGHTS["signal_strength"], 3
                ),
                "signal_consistency_contribution": round(
                    parsed.scores.signal_consistency / MAX_VALUES["signal_consistency"] * WEIGHTS["signal_consistency"], 3
                ),
                "data_quality_contribution":       round(
                    data_quality / MAX_VALUES["data_quality"] * WEIGHTS["data_quality"], 3
                ),
            },
            "entry_price_hint": parsed.entry_price_hint,
            "exit_price_hint":  parsed.exit_price_hint,
            "tactical_suggestion": parsed.tactical_suggestion,
        }

        print("[Aggregator] Output:")
        print(json.dumps(output, ensure_ascii=False, indent=2))

        return {"final_output": output}

    except Exception as e:
        print(f"[Aggregator] Error: {str(e)}")

        fallback = {
            "summary":         "Không thể phân tích dữ liệu",
            "recommendation":  "Chờ",
            "reasoning":       "Lỗi hệ thống",
            "confidence":      0.0,
            "entry_price_hint": None,
            "exit_price_hint":  None,
            "tactical_suggestion": "Vui lòng thử lại sau.",
        }

        return {"error": str(e), "final_output": fallback}