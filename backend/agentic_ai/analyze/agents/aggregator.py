"""
aggregator.py — Aggregator Agent (REFACTORED: Confidence = mức độ ủng hộ, độc lập với chiều tín hiệu)

- Tổng hợp dữ liệu từ:
    + article_agent
    + fundamental_analysis_agent
    + technical_analysis_agent

- Nếu mode = "auto"  → trả structured output (dict)
- Nếu mode = "chat"  → trả plain text thân thiện

────────────────────────────────────────────────────────
THIẾT KẾ CONFIDENCE (Hướng 1):

  Confidence = f(signal_strength, signal_consistency, data_quality)

  Hoàn toàn độc lập với chiều bullish/bearish của recommendation.
  Câu hỏi confidence trả lời:
    "Các nguồn thông tin có đủ bằng chứng rõ ràng và đồng thuận
     với recommendation được đưa ra không?"

  Công thức:
    confidence = signal_strength  * 0.40
               + signal_consistency * 0.40
               + data_quality       * 0.20

  Mỗi thành phần đã được chuẩn hóa về [0, 1] trước khi nhân trọng số.
────────────────────────────────────────────────────────
"""

import json
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage

from agentic_ai.service.openai_service import _get_openai_client
from agentic_ai.analyze.state import AgentState


# ─────────────────────────────────────────────────────────────
# 📦 Structured Output Schema
# ─────────────────────────────────────────────────────────────

class ConfidenceScores(BaseModel):
    """
    Ba chiều đánh giá độ tin cậy — hoàn toàn độc lập với chiều Mua/Bán.

    LLM chấm điểm nguyên (0/1/2/3).
    Code chuẩn hóa và tổng hợp thành confidence ∈ [0.0, 1.0].
    """

    signal_strength: Literal[0, 1, 2, 3] = Field(
        description=(
            "Số nguồn có tín hiệu RÕ RÀNG — tín hiệu không mơ hồ, không thiếu dữ liệu quan trọng.\n"
            "Đếm độc lập với chiều bullish/bearish:\n"
            "  3 = Tất cả các nguồn đều có tín hiệu rõ ràng\n"
            "  2 = Phần lớn các nguồn có tín hiệu rõ ràng\n"
            "  1 = Chỉ có ít nguồn có tín hiệu rõ ràng\n"
            "  0 = Không nguồn nào có tín hiệu rõ ràng (thiếu dữ liệu, mâu thuẫn nội bộ)\n"
            "\n"
            "Tiêu chí 'rõ ràng' cho từng nguồn:\n"
            "  Technical: ≥50% chỉ báo đồng thuận một chiều (bullish hoặc bearish)\n"
            "  Fundamental: ≥50% chỉ số đánh giá được ở mức tốt hoặc xấu rõ ràng\n"
            "  News: sentiment tin tức rõ ràng tích cực hoặc tiêu cực (không trung lập)"
        )
    )

    signal_consistency: Literal[0, 1, 2] = Field(
        description=(
            "Mức độ đồng thuận của các nguồn VỚI recommendation đã chọn.\n"
            "Không phải đồng thuận với nhau, mà đồng thuận với kết quả cuối cùng:\n"
            "  2 = Tất cả nguồn có dữ liệu đều ủng hộ recommendation\n"
            "  1 = Phần lớn nguồn ủng hộ, một nguồn trái chiều hoặc trung lập\n"
            "  0 = Các nguồn mâu thuẫn nhau, recommendation là phán đoán chủ quan\n"
            "\n"
            "Ví dụ:\n"
            "  Recommendation = 'Mua': technical bullish + fundamental tốt + news tích cực → 2\n"
            "  Recommendation = 'Bán': technical bearish + fundamental xấu + news tiêu cực → 2\n"
            "  Recommendation = 'Chờ': tín hiệu mixed, không bên nào áp đảo → 1 hoặc 0"
        )
    )

    data_quality: Literal[0, 1, 2] = Field(
        description=(
            "Chất lượng và độ đầy đủ của dữ liệu đầu vào:\n"
            "  2 = Đầy đủ: có dữ liệu từ ≥2 nguồn, mỗi nguồn có đủ chỉ số quan trọng\n"
            "  1 = Cơ bản: có dữ liệu nhưng thiếu một số chỉ số quan trọng\n"
            "  0 = Thiếu: chỉ có 1 nguồn dữ liệu hoặc dữ liệu quá sơ sài\n"
            "\n"
            "Chỉ số quan trọng tối thiểu:\n"
            "  Technical: cần ít nhất RSI + MACD hoặc giá vs MA\n"
            "  Fundamental: cần ít nhất PE + ROE hoặc D/E\n"
            "  News: cần ít nhất 1 tin tức gần đây liên quan trực tiếp"
        )
    )


class InvestmentRecommendation(BaseModel):
    summary: str = Field(
        description=(
            "Phân tích tổng thể đầy đủ về tình hình cổ phiếu từ 3 nguồn: "
            "tin tức, phân tích cơ bản, kỹ thuật"
            "Giải thích cho recommendation dựa trên:\n"
            "  1. Dẫn chứng từ số liệu và phân tích của các nguồn\n"
            "  2. Khẩu vị rủi ro của user\n"
            "  3. Lý do chấm điểm confidence (signal_strength, signal_consistency, data_quality)"
        )
    )
    recommendation: Literal["Mua", "Chờ", "Bán"] = Field(
        description="Hành động đề xuất"
    )
    reasoning: str = Field(
        description=(
            "Giải thích cho recommendation dựa trên:\n"
            "  1. Dẫn chứng từ số liệu và phân tích của các nguồn\n"
            "  2. Khẩu vị rủi ro của user\n"
            "  3. Lý do chấm điểm confidence (signal_strength, signal_consistency, data_quality)"
        )
    )
    scores: ConfidenceScores = Field(
        description=(
            "Điểm 3 chiều để tính confidence — LLM chấm, code tính tổng.\n"
            "Nhớ: confidence đo mức độ TIN CẬY vào recommendation, "
            "không phải mức độ bullish/bearish."
        )
    )
    tactical_suggestion: str = Field(
        description=(
            "Gợi ý vùng/thời điểm mua vào bằng ngôn ngữ tự nhiên. "
            "Dựa trên support/resistance, MA, Bollinger Bands từ dữ liệu kỹ thuật. "
            "Không bịa số — nếu thiếu dữ liệu kỹ thuật thì nói rõ 'chưa đủ dữ liệu để xác định vùng giá'."

            "Gợi ý vùng chốt lời và mức cắt lỗ tham khảo. "
            "Nêu rõ điều kiện kỹ thuật hoặc fundamental để re-evaluate."

            "Khung thời gian phù hợp dựa trên khẩu vị rủi ro của user "
            "và chất lượng tín hiệu (ngắn hạn / trung hạn / dài hạn)."

            "1–2 rủi ro chính cần theo dõi, rút ra từ dữ liệu fundamental và news."

            "Thêm disclaimer: Đây là gợi ý tham khảo, không phải lời khuyên đầu tư. Quyết định cuối cùng thuộc về nhà đầu tư."
        )
    )


# ─────────────────────────────────────────────────────────────
# 🧮 Tính confidence từ các điểm thành phần
# ─────────────────────────────────────────────────────────────

# Trọng số: signal_strength và signal_consistency quan trọng hơn data_quality
WEIGHTS = {
    "signal_strength": 0.40,
    "signal_consistency": 0.40,
    "data_quality": 0.20,
}

# Max value của từng chiều (để chuẩn hóa về [0, 1])
MAX_VALUES = {
    "signal_strength": 3,
    "signal_consistency": 2,
    "data_quality": 2,
}


def calculate_confidence(scores: ConfidenceScores) -> float:
    """
    Tính confidence ∈ [0.0, 1.0] từ 3 chiều độc lập.

    Công thức:
        confidence = Σ (score_i / max_i) * weight_i

    Không clamp âm vì tất cả thành phần đều >= 0.
    """
    confidence = (
        (scores.signal_strength  / MAX_VALUES["signal_strength"])  * WEIGHTS["signal_strength"]
        + (scores.signal_consistency / MAX_VALUES["signal_consistency"]) * WEIGHTS["signal_consistency"]
        + (scores.data_quality       / MAX_VALUES["data_quality"])       * WEIGHTS["data_quality"]
    )
    return round(min(1.0, confidence), 2)


# ─────────────────────────────────────────────────────────────
# 🧠 Prompt — Structured (API mode)
# ─────────────────────────────────────────────────────────────

AGGREGATOR_SYSTEM_PROMPT = """
Bạn là chuyên gia phân tích chứng khoán Việt Nam với kinh nghiệm thực tế.

Nhiệm vụ:
- Tổng hợp dữ liệu từ các nguồn sau nếu có:
  1. Tin tức (article_agent)
  2. Phân tích cơ bản (fundamental_analysis_agent)
  3. Phân tích kỹ thuật (technical_analysis_agent)

- Trả về:
  + summary    : tóm tắt tình hình từ cả 3 nguồn
  + recommendation: ["Mua", , "Chờ", "Bán"]
  + reasoning  : giải thích logic rõ ràng, có dẫn chứng số liệu
  + scores     : chấm 3 chiều confidence — code sẽ tính tổng

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHẦN I — PHÂN TÍCH TÍN HIỆU
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A. PHÂN TÍCH KỸ THUẬT

RSI (14):
  < 30           → oversold — bullish nhẹ (có thể hồi)
  30–45          → yếu → bearish
  45–55          → trung lập
  55–70          → mạnh → bullish
  > 70           → overbought → risk điều chỉnh

MACD:
  macd > signal  → bullish | macd < signal → bearish
  histogram tăng → động lượng tăng | giảm → yếu dần
  cắt lên signal → tín hiệu Mua | cắt xuống → tín hiệu Bán

Bollinger Bands:
  Giá gần upper  → mạnh | gần lower → yếu / có thể hồi

Moving Average:
  Giá > MA20     → ngắn hạn tích cực | < MA20 → yếu
  Giá > MA50     → trung hạn tốt    | < MA50 → xấu
  MA20 cắt lên MA50 (Golden Cross)  → bullish mạnh
  MA20 cắt xuống MA50 (Death Cross) → bearish mạnh

KDJ:
  K, D, J < 20   → oversold → có thể hồi
  K, D, J > 80   → overbought → dễ điều chỉnh
  K cắt lên D    → bullish | cắt xuống → bearish

Volume:
  Giá tăng + volume tăng → xác nhận xu hướng
  Giá tăng + volume giảm → tín hiệu yếu

────────────────────────
B. PHÂN TÍCH CƠ BẢN

Định giá    : PE < 10 rẻ / 10–18 hợp lý / > 20 đắt
Sinh lời    : ROE > 20% rất tốt / 15–20% tốt / < 10% yếu
Đòn bẩy     : D/E < 0.5 an toàn / 0.5–1 trung bình / > 1 rủi ro
Tăng trưởng : doanh thu & lợi nhuận tăng YoY → tích cực

────────────────────────
C. TIN TỨC (NEWS SENTIMENT)

Tích cực rõ ràng : tăng trưởng, cổ tức, mở rộng, khuyến nghị mua
Tích cực nhẹ    : tin ngành tích cực, vĩ mô ổn định
Trung lập        : tin thị trường chung, không ảnh hưởng trực tiếp
Tiêu cực nhẹ    : áp lực ngành, vĩ mô bất lợi
Tiêu cực rõ ràng: thua lỗ, bán ròng mạnh, kiện tụng, vi phạm

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHẦN II — QUYẾT ĐỊNH RECOMMENDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Kết hợp tín hiệu:
  Technical bullish + Fundamental tốt                → "Mua"
  Technical yếu     + Fundamental tốt                → "Chờ" hoặc 
  Technical xấu     + News xấu                       → "Bán"
  Mixed signals (không bên nào áp đảo)               → "Chờ"

Điều chỉnh theo khẩu vị rủi ro:
  Rủi ro thấp       → ưu tiên  hoặc "Chờ"
  Ngắn hạn          → ưu tiên technical hơn fundamental
  Thu nhập thụ động → ưu tiên ROE cao, nợ thấp

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHẦN III — CHẤM ĐIỂM CONFIDENCE (QUAN TRỌNG)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ NGUYÊN TẮC CỐT LÕI:
Confidence ĐO MỨC ĐỘ TIN CẬY vào recommendation, KHÔNG đo chiều bullish/bearish.
Recommendation "Bán" với đầy đủ bằng chứng → confidence CAO.
Recommendation "Mua" với dữ liệu mơ hồ    → confidence THẤP.

────────────────────────
1. SIGNAL_STRENGTH (0–3): Số nguồn có tín hiệu RÕ RÀNG

Đếm từng nguồn một cách độc lập:

  [Technical rõ ràng] khi: ≥50% chỉ báo có sẵn đồng thuận một chiều
    Ví dụ: RSI=65, MACD>signal, giá>MA20 → 3/3 bullish → rõ ràng bullish ✓
    Ví dụ: RSI=40, MACD>signal, giá<MA20 → 1/3 bullish → không rõ ✗

  [Fundamental rõ ràng] khi: ≥50% chỉ số đánh giá được ở mức tốt HOẶC xấu rõ ràng
    Ví dụ: PE=12(tốt), ROE=18%(tốt), D/E=0.4(tốt) → 3/3 tốt → rõ ràng tốt ✓
    Ví dụ: PE=15(trung lập), ROE=12%(trung lập) → không rõ ✗

  [News rõ ràng] khi: sentiment tích cực RÕ RÀNG hoặc tiêu cực RÕ RÀNG
    Không tính nếu tin trung lập hoặc không đủ thông tin

  Tổng hợp: signal_strength = số nguồn đạt tiêu chí "rõ ràng" (0, 1, 2, hoặc 3)

────────────────────────
2. SIGNAL_CONSISTENCY (0–2): Đồng thuận VỚI recommendation đã chọn

  Sau khi chọn recommendation, đếm có bao nhiêu nguồn ủng hộ nó:

  2 = Tất cả nguồn có dữ liệu đều ủng hộ recommendation
      Ví dụ Mua: technical bullish ✓ + fundamental tốt ✓ + news tích cực ✓
      Ví dụ Bán: technical bearish ✓ + fundamental xấu ✓ + news tiêu cực ✓

  1 = Phần lớn ủng hộ, một nguồn trái chiều hoặc trung lập
      Ví dụ Mua: technical bullish ✓ + fundamental tốt ✓ + news trung lập ~

  0 = Mâu thuẫn, recommendation là phán đoán trong uncertainty
      Ví dụ Chờ: technical bullish nhưng fundamental xấu, news tiêu cực

────────────────────────
3. DATA_QUALITY (0–2): Chất lượng dữ liệu đầu vào

  2 = Đầy đủ: ≥2 nguồn cung cấp đủ chỉ số quan trọng
      Technical: có RSI + MACD, hoặc giá vs MA + volume
      Fundamental: có PE + ROE, hoặc D/E + tăng trưởng
      News: có ≥1 tin gần đây liên quan trực tiếp

  1 = Cơ bản: có dữ liệu nhưng thiếu một số chỉ số quan trọng

  0 = Thiếu: chỉ có 1 nguồn, hoặc dữ liệu quá sơ sài để kết luận

────────────────────────
Ví dụ chấm điểm:

  Case A — Tín hiệu Bán rõ ràng:
    Technical: RSI=72(overbought), MACD<signal, giá<MA20 → 3/3 bearish → rõ ràng ✓
    Fundamental: D/E=2.1(xấu), ROE=4%(xấu), PE=25(xấu) → 3/3 xấu → rõ ràng ✓
    News: báo cáo thua lỗ 3 quý liên tiếp → tiêu cực rõ ràng ✓
    Recommendation: "Bán"
    → signal_strength=3, signal_consistency=2, data_quality=2
    → confidence = 3/3*0.4 + 2/2*0.4 + 2/2*0.2 = 1.0 (rất cao ✓)

  Case B — Tín hiệu Mua mơ hồ:
    Technical: RSI=52(neutral), MACD>signal → 1/2 bullish → không rõ ✗
    Fundamental: chỉ có PE=14(tốt), thiếu ROE và D/E → không rõ ✗
    News: không có tin gần đây → không rõ ✗
    Recommendation: "Chờ"
    → signal_strength=0, signal_consistency=1, data_quality=0
    → confidence = 0/3*0.4 + 1/2*0.4 + 0/2*0.2 = 0.2 (thấp ✓)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUY TẮC BẮT BUỘC:
- Output CHỈ JSON, không thêm text ngoài JSON
- Trong reasoning: giải thích rõ tại sao chấm từng điểm
- Không bịa số liệu ngoài dữ liệu được cung cấp
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHẦN IV — GỢI Ý CHIẾN THUẬT (tactical_suggestion)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sinh tactical_suggestion SAU KHI đã có recommendation và confidence.
Tất cả con số phải lấy từ dữ liệu kỹ thuật được cung cấp — KHÔNG bịa.

────────────────────────
1. ENTRY_HINT

Mục tiêu: gợi ý VÙNG (không phải điểm) và ĐIỀU KIỆN để xem xét vào lệnh.

Cách xác định vùng entry:
  - Tìm support gần nhất: lower Bollinger Band, MA20, MA50, hoặc đáy swing gần nhất
  - Vùng entry = [support - biên độ nhỏ, support + biên độ nhỏ]
  - Nếu RSI > 65 hoặc giá đang gần upper BB → cảnh báo "không mua đuổi"
  - Nếu thiếu dữ liệu kỹ thuật → viết: "Chưa đủ dữ liệu kỹ thuật để xác định vùng vào lệnh cụ thể"

Ngôn ngữ theo confidence:
  confidence ≥ 0.7 → "Có thể xem xét mua ở vùng X–Y..."
  confidence 0.4–0.7 → "Nếu giá điều chỉnh về vùng X–Y, có thể theo dõi..."
  confidence < 0.4  → "Tín hiệu chưa rõ ràng, nên chờ thêm xác nhận trước khi vào lệnh"

────────────────────────
2. EXIT_HINT

Mục tiêu: gợi ý VÙNG chốt lời và mức cắt lỗ tham khảo.

Cách xác định:
  Take profit:
    TP1 = kháng cự gần nhất (upper BB, đỉnh swing gần nhất, MA trên)
    TP2 = mục tiêu xa hơn nếu momentum mạnh (tùy dữ liệu)
  Stop loss:
    SL = phá vỡ support quan trọng (đáy swing, dưới MA20 một biên độ)
    Nên nêu điều KIỆN (đóng cửa dưới X) thay vì chỉ mức giá

  Nếu recommendation = "Chờ" → exit_hint mô tả điều kiện để re-evaluate,
    không cần nêu TP/SL cụ thể.
  Nếu recommendation = "Bán" → exit_hint tập trung vào bảo toàn vốn,
    gợi ý mức để cân nhắc mua lại nếu có.

────────────────────────
3. TIME_HORIZON

Gắn với khẩu vị rủi ro và chất lượng tín hiệu:

  Tín hiệu chủ yếu từ technical → ngắn hạn (1–4 tuần)
  Tín hiệu từ cả technical + fundamental → trung hạn (1–3 tháng)
  Fundamental dẫn dắt, technical yếu → dài hạn (3–12 tháng), cần kiên nhẫn

  Điều chỉnh theo khẩu vị:
    Ngắn hạn / giao dịch tích cực → ưu tiên khung tuần
    Thu nhập thụ động / an toàn   → trung-dài hạn, nhấn mạnh cổ tức và fundamental

────────────────────────
4. KEY_RISK

Nêu 1–2 rủi ro CỤ THỂ từ dữ liệu, không nói chung chung.

  Tốt: "D/E = 1.2 ở mức cao, nếu lãi suất tăng thêm sẽ ảnh hưởng chi phí vốn"
  Tốt: "RSI đang tiệm cận 70, nguy cơ điều chỉnh ngắn hạn nếu không có volume xác nhận"
  Tránh: "Thị trường có thể biến động" (quá chung, vô nghĩa)

────────────────────────
QUY TẮC BẮT BUỘC cho tactical_suggestion:
  ✓ Mọi con số phải có trong dữ liệu đầu vào — KHÔNG bịa giá, KHÔNG bịa chỉ số
  ✓ Ngôn ngữ phải khớp với confidence (thận trọng hơn khi confidence thấp)
  ✓ disclaimer luôn xuất hiện, không được bỏ qua
  ✓ Nếu recommendation = "Chờ" và confidence < 0.5 → entry_hint và exit_hint
     dùng ngôn ngữ quan sát, không đưa ra vùng giá cụ thể
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


# ─────────────────────────────────────────────────────────────
# 🚀 Aggregator Agent
# ─────────────────────────────────────────────────────────────

def aggregator_agent(state: AgentState) -> AgentState:
    mode = state.get("mode", "auto")
    print(f"[Aggregator] Tổng hợp kết quả (mode={mode})...")

    client = _get_openai_client()

    results = state.get("agent_results", {})
    risk_appetite = state.get("risk_appetite", {})
    user_input = state.get("user_input", "")

    # Nội dung phân tích — luôn là message cuối cùng gửi cho LLM
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

      # Confidence do code tính — không dùng giá trị LLM tự tính
      confidence = calculate_confidence(parsed.scores)

      output = {
          "summary": parsed.summary,
          "recommendation": parsed.recommendation,
          "reasoning": parsed.reasoning,
          "confidence": confidence,
          "confidence_breakdown": {
              # Giá trị gốc LLM chấm
              "signal_strength":    parsed.scores.signal_strength,       # 0–3
              "signal_consistency": parsed.scores.signal_consistency,    # 0–2
              "data_quality":       parsed.scores.data_quality,          # 0–2
              # Đóng góp vào confidence sau khi chuẩn hóa và nhân trọng số
              "signal_strength_contribution":    round(
                  parsed.scores.signal_strength / MAX_VALUES["signal_strength"] * WEIGHTS["signal_strength"], 3
              ),
              "signal_consistency_contribution": round(
                  parsed.scores.signal_consistency / MAX_VALUES["signal_consistency"] * WEIGHTS["signal_consistency"], 3
              ),
              "data_quality_contribution":       round(
                  parsed.scores.data_quality / MAX_VALUES["data_quality"] * WEIGHTS["data_quality"], 3
              ),
          },
          "tactical_suggestion": parsed.tactical_suggestion
      }

      print("[Aggregator] Output:")
      print(json.dumps(output, ensure_ascii=False, indent=2))

      return {"final_output": output}

    except Exception as e:
        print(f"[Aggregator] Error: {str(e)}")

        fallback = {
                "summary": "Không thể phân tích dữ liệu",
                "recommendation": "Chờ",
                "reasoning": "Lỗi hệ thống",
                "confidence": 0.0,
        }

        return {"error": str(e), "final_output": fallback}