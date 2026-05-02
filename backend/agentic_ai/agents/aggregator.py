"""
aggregator.py — Aggregator Agent (FINAL VERSION)

- Tổng hợp dữ liệu từ:
    + article_agent
    + fundamental_analysis_agent
    + technical_analysis_agent

- Nếu mode = "api"     → trả structured output (dict)
- Nếu mode = "chatbot" → trả plain text thân thiện
"""

import json
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage

from agentic_ai.service.openai_service import _get_openai_client
from agentic_ai.state import AgentState


# ─────────────────────────────────────────────────────────────
# 📦 Structured Output Schema
# ─────────────────────────────────────────────────────────────

class ConfidenceScores(BaseModel):
    """
    LLM chấm điểm từng thành phần dưới dạng số nguyên (đã nhân 100).
    Code convert về float rồi tính confidence = base + sum(scores) / 100.
    """
    technical_score: Literal[-20, -10, 0, 10, 20] = Field(
        description=(
            "Mức độ đồng thuận các chỉ báo kỹ thuật (đơn vị: phần trăm điểm):\n"
            "+20 = Strong bullish/bearish: ≥4/6 chỉ báo đồng thuận một chiều\n"
            "+10 = Weak bullish/bearish: 2–3 chỉ báo đồng thuận\n"
            "  0 = Neutral/Mixed: chỉ báo mâu thuẫn hoặc sideway\n"
            "-10 = Weak bearish\n"
            "-20 = Strong bearish"
        )
    )
    fundamental_score: Literal[-10, 0, 8, 15] = Field(
        description=(
            "Chất lượng nền tảng tài chính (đơn vị: phần trăm điểm):\n"
            "+15 = Strong: PE<18 AND ROE≥15% AND D/E<1.0\n"
            " +8 = Stable: đạt 2/3 điều kiện trên\n"
            "  0 = Weak: đạt 0–1 điều kiện\n"
            "-10 = Rủi ro cao: D/E>1.5 hoặc ROE<5%"
        )
    )
    news_score: Literal[-15, -5, 5, 15] = Field(
        description=(
            "Sentiment tin tức (đơn vị: phần trăm điểm):\n"
            "+15 = Tích cực rõ ràng: tăng trưởng, cổ tức, khuyến nghị mua\n"
            " +5 = Tích cực nhẹ hoặc trung lập\n"
            " -5 = Tiêu cực nhẹ: áp lực ngành, vĩ mô bất lợi\n"
            "-15 = Tiêu cực rõ ràng: thua lỗ, bán ròng mạnh, tin xấu trực tiếp"
        )
    )
    consistency_score: Literal[-10, 0, 10] = Field(
        description=(
            "Mức độ đồng thuận giữa 3 nguồn tín hiệu (đơn vị: phần trăm điểm):\n"
            "+10 = Cả 3 nguồn (technical + fundamental + news) cùng chiều\n"
            "  0 = 2/3 nguồn cùng chiều\n"
            "-10 = 3 nguồn mâu thuẫn nhau"
        )
    )


class InvestmentRecommendation(BaseModel):
    summary: str = Field(
        description="Phân tích tổng thể đầy đủ về tình hình cổ phiếu từ 3 nguồn tin tức, phân tích cơ bản, kỹ thuật"
    )
    recommendation: Literal["Mua", "Giữ", "Chờ", "Bán"] = Field(
        description="Hành động đề xuất"
    )
    reasoning: str = Field(
        description="Giải thích cho recommendation từ khẩu vị rủi ro của user kết hợp dẫn chứng từ số liệu, tài liệu của các nguồn dựa trên dữ liệu phân tích"
    )
    scores: ConfidenceScores = Field(
        description="Điểm thành phần để tính confidence — LLM chấm, code tính tổng"
    )


# ─────────────────────────────────────────────────────────────
# 🧮 Tính confidence từ các điểm thành phần
# ─────────────────────────────────────────────────────────────

BASE_SCORE = 0.5

def calculate_confidence(scores: ConfidenceScores) -> float:
    total = (
        BASE_SCORE
        + scores.technical_score / 100
        + scores.fundamental_score / 100
        + scores.news_score / 100
        + scores.consistency_score / 100
    )
    return round(max(0.0, min(1.0, total)), 2)


# ─────────────────────────────────────────────────────────────
# 🧠 Prompt — Structured (API mode)
# ─────────────────────────────────────────────────────────────

AGGREGATOR_SYSTEM_PROMPT = """
Bạn là chuyên gia phân tích chứng khoán Việt Nam với kinh nghiệm thực tế.

Nhiệm vụ:
- Tổng hợp dữ liệu từ:
  1. Tin tức (article_agent)
  2. Phân tích cơ bản (fundamental_analysis_agent)
  3. Phân tích kỹ thuật (technical_analysis_agent)

- Trả về:
  + summary: tóm tắt tình hình
  + recommendation: ["Mua", "Giữ", "Chờ", "Bán"]
  + reasoning: giải thích logic rõ ràng
  + scores: chấm điểm từng thành phần (technical, fundamental, news, consistency)
            → confidence sẽ do code tính từ scores, KHÔNG cần bạn tính

────────────────────────
I. PHÂN TÍCH TIN TỨC (NEWS SENTIMENT)

Đánh giá sentiment tổng thể:
- Tích cực:
  + Tin về tăng trưởng, mở rộng, lợi nhuận, cổ tức
- Trung lập:
  + Tin thị trường chung, không ảnh hưởng trực tiếp
- Tiêu cực:
  + VN-Index giảm mạnh
  + Khối ngoại Bán ròng
  + Áp lực ngành / vĩ mô

Ảnh hưởng:
- Positive → +0.05 ~ +0.1 confidence
- Neutral → 0
- Negative → -0.1 ~ -0.2 confidence

────────────────────────
II. PHÂN TÍCH KỸ THUẬT (TECHNICAL SIGNALS)

1. RSI (14):
- < 30 → oversold (có thể hồi) → bullish nhẹ
- 30–45 → yếu → bearish
- 45–55 → trung lập
- 55–70 → mạnh → bullish
- > 70 → overbought → risk điều chỉnh

────────────────────────
2. MACD:
- MACD > signal → bullish
- MACD < signal → bearish
- Histogram tăng → động lượng tăng
- Histogram giảm → động lượng yếu
- Cắt lên signal → tín hiệu Mua sớm
- Cắt xuống signal → tín hiệu Bán

────────────────────────
3. Bollinger Bands:
- Giá gần lower band → yếu / có thể hồi
- Giá dưới middle → xu hướng yếu
- Giá vượt middle → cải thiện
- Giá gần upper → mạnh

────────────────────────
4. Moving Average (MA20, MA50):

MA20 (ngắn hạn):
- Giá > MA20 → xu hướng ngắn hạn tích cực
- Giá < MA20 → xu hướng yếu

MA50 (trung hạn):
- Giá > MA50 → xu hướng trung hạn tốt
- Giá < MA50 → xu hướng trung hạn xấu

MA Cross:
- MA20 cắt lên MA50 → Golden Cross → bullish mạnh
- MA20 cắt xuống MA50 → Death Cross → bearish mạnh

────────────────────────
5. KDJ:
- K, D, J đều < 20 → oversold → có thể hồi
- K, D, J > 80 → overbought → dễ điều chỉnh
- K cắt lên D → bullish
- K cắt xuống D → bearish

────────────────────────
6. Price Action & Volume:
- Higher highs + higher lows → uptrend
- Giá tăng + volume tăng → xác nhận xu hướng
- Giá tăng + volume giảm → yếu

────────────────────────
III. PHÂN TÍCH CƠ BẢN (FUNDAMENTAL)

1. Định giá: PE < 10 rẻ / 10–18 hợp lý / > 20 đắt
2. Chất lượng: ROE > 20% rất tốt / 15–20% tốt / < 10% yếu
3. Đòn bẩy: Debt/Equity < 0.5 an toàn / 0.5–1 trung bình / > 1 rủi ro
4. Tăng trưởng: doanh thu & lợi nhuận tăng → tích cực

────────────────────────
IV. KẾT HỢP & QUYẾT ĐỊNH

- Technical bullish + Fundamental tốt → "Mua"
- Technical yếu + Fundamental tốt → "Chờ" hoặc "Giữ"
- Technical xấu + News xấu → "Bán"
- Mixed signals → "Chờ"

────────────────────────
V. KHẨU VỊ RỦI RO

- Rủi ro thấp → ưu tiên "Giữ" hoặc "Chờ"
- Ngắn hạn → ưu tiên technical hơn fundamental
- Thu nhập thụ động → ưu tiên ROE cao, nợ thấp

────────────────────────
VI. CONFIDENCE SCORING

Công thức: confidence = clamp(base + technical_score + fundamental_score + news_score + consistency_score, 0, 1)

Base = 0.5 (mặc định khi chưa có thông tin)

────────────────────────
1. TECHNICAL SCORE (trọng số: tối đa ±0.2)

Đánh giá mức độ đồng thuận của các chỉ báo kỹ thuật CÓ SẴN trong dữ liệu.
Chỉ xét các chỉ báo thực sự được cung cấp, không giả định chỉ báo không có.

Bước 1 — Đánh giá từng chỉ báo có sẵn:

| Chỉ báo            | Bullish                                      | Bearish                                       | Neutral              |
|--------------------|----------------------------------------------|-----------------------------------------------|----------------------|
| rsi_14             | 55–70                                        | 30–45                                         | 45–55                |
|                    | < 30 (oversold, có thể hồi — bullish nhẹ)   | > 70 (overbought, risk điều chỉnh — bearish)  |                      |
| macd + macd_signal | macd > macd_signal                           | macd < macd_signal                            |                      |
| macd_histogram     | histogram > 0 và tăng                        | histogram < 0 và giảm                         | gần 0                |
| bb_upper/lower     | giá gần bb_upper                             | giá gần bb_lower                              | giá gần bb_middle    |
| sma_20             | close > sma_20                               | close < sma_20                                |                      |
| sma_50             | close > sma_50                               | close < sma_50                                |                      |
| sma_20 + sma_50    | sma_20 > sma_50 (Golden Cross)               | sma_20 < sma_50 (Death Cross)                 |                      |
| kdj_k + kdj_d      | kdj_k cắt lên kdj_d                         | kdj_k cắt xuống kdj_d                         |                      |
|                    | kdj_k, kdj_d, kdj_j < 20 (oversold)         | kdj_k, kdj_d, kdj_j > 80 (overbought)        |                      |
| kdj_j              | kdj_j < 0 (oversold mạnh)                   | kdj_j > 100 (overbought mạnh)                 |                      |

Bước 2 — Tính tỷ lệ đồng thuận trên số chỉ báo thực sự có:

+20 = ≥ 70% chỉ báo có sẵn đồng thuận bullish hoặc bearish
+10 = 50–69% chỉ báo có sẵn đồng thuận một chiều
  0 = < 50% đồng thuận hoặc mâu thuẫn nhau
-10 = 50–69% chỉ báo có sẵn đồng thuận bearish
-20 = ≥ 70% chỉ báo có sẵn đồng thuận bearish

Ví dụ:
- Chỉ có rsi_14=60, macd>macd_signal → 2/2 bullish → 100% → +20
- Có rsi_14=60, macd<macd_signal, close>sma_20 → 2/3 bullish → 67% → +10
- Không có dữ liệu kỹ thuật → 0

────────────────────────
2. FUNDAMENTAL SCORE (trọng số: tối đa ±0.15)

Đánh giá chất lượng nền tảng tài chính dựa trên các chỉ số CÓ SẴN trong dữ liệu.
Chỉ xét các chỉ số thực sự được cung cấp.

Bước 1 — Đánh giá từng chỉ số có sẵn:

Định giá (Valuation):
- pe_ratio:   < 10 → tốt | 10–18 → trung lập | > 20 → xấu
- pb_ratio:   < 1.5 → tốt | 1.5–3 → trung lập | > 3 → xấu
- ps_ratio:   < 1 → tốt | 1–3 → trung lập | > 3 → xấu

Sinh lời (Profitability):
- roe:         > 20% → tốt | 10–20% → trung lập | < 10% → xấu
- roa:         > 10% → tốt | 5–10% → trung lập | < 5% → xấu
- net_margin:  > 15% → tốt | 5–15% → trung lập | < 5% → xấu
- gross_margin:> 30% → tốt | 15–30% → trung lập | < 15% → xấu
- ebit_margin: > 15% → tốt | 5–15% → trung lập | < 5% → xấu

Tăng trưởng (Growth):
- revenue_yoy: > 15% → tốt | 0–15% → trung lập | < 0% → xấu
- profit_yoy:  > 15% → tốt | 0–15% → trung lập | < 0% → xấu

Sức khỏe tài chính (Financial Health):
- debt_to_equity:    < 0.5 → tốt | 0.5–1.0 → trung lập | > 1.0 → xấu
- current_ratio:     > 2 → tốt | 1–2 → trung lập | < 1 → xấu
- quick_ratio:       > 1 → tốt | 0.5–1 → trung lập | < 0.5 → xấu
- interest_coverage: > 5 → tốt | 2–5 → trung lập | < 2 → xấu

Hiệu quả hoạt động (Efficiency):
- asset_turnover:     > 1 → tốt | 0.5–1 → trung lập | < 0.5 → xấu
- inventory_turnover: > 6 → tốt | 3–6 → trung lập | < 3 → xấu
- days_receivable:    < 30 → tốt | 30–60 → trung lập | > 60 → xấu
- days_payable:       < 45 → tốt | 45–90 → trung lập | > 90 → xấu

Core metrics:
- eps: tăng so với kỳ trước → tốt | ổn định → trung lập | giảm → xấu

Bước 2 — Tính tỷ lệ chỉ số tốt trên tổng số chỉ số có sẵn:

+15 = ≥ 70% chỉ số có sẵn ở mức tốt
 +8 = 50–69% chỉ số có sẵn ở mức tốt
  0 = < 50% chỉ số tốt (trung lập hoặc yếu)
-10 = ≥ 50% chỉ số có sẵn ở mức xấu, hoặc có chỉ số rủi ro cao
      (debt_to_equity > 1.5, roe < 5%, current_ratio < 1)

Ví dụ:
- Chỉ có pe_ratio=14, roe=25% → 2/2 tốt → 100% → +15
- Có pe_ratio=14, roe=8%, debt_to_equity=0.8 → 1/3 tốt → 33% → 0
- Không có dữ liệu cơ bản → 0

────────────────────────
3. NEWS SCORE (trọng số: tối đa ±0.15)

Đánh giá sentiment tin tức gần nhất:

+0.15 → Tích cực rõ ràng:
  - Tin tăng trưởng doanh thu / lợi nhuận
  - Công bố cổ tức, mở rộng kinh doanh
  - Khuyến nghị mua từ công ty chứng khoán uy tín

+0.05 → Tích cực nhẹ hoặc trung lập

-0.05 → Tiêu cực nhẹ:
  - Áp lực ngành, vĩ mô bất lợi

-0.15 → Tiêu cực rõ ràng:
  - VN-Index giảm mạnh + khối ngoại bán ròng
  - Tin xấu trực tiếp về công ty (thua lỗ, kiện tụng, vi phạm)

────────────────────────
4. CONSISTENCY SCORE (trọng số: ±0.1)

Đánh giá mức độ đồng thuận giữa 3 nguồn tín hiệu:

+0.1 → Cả 3 nguồn (technical + fundamental + news) cùng chiều
+0.0 → 2/3 nguồn cùng chiều
-0.1 → 3 nguồn mâu thuẫn nhau (mixed signals)

────────────────────────
QUY TẮC BẮT BUỘC:
- Luôn ghi rõ từng thành phần điểm trong reasoning để giải thích confidence
- Clamp kết quả về [0.0, 1.0]
- Không làm tròn thô (VD: không phải lúc nào cũng trả về 0.5 hoặc 0.8)

────────────────────────
Output CHỈ JSON, không thêm text.
"""


# ─────────────────────────────────────────────────────────────
# 🧠 Prompt — Chatbot mode (plain text)
# ─────────────────────────────────────────────────────────────

AGGREGATOR_CHATBOT_SYSTEM_PROMPT = """
Bạn là chuyên gia phân tích chứng khoán Việt Nam, đang tư vấn trực tiếp cho nhà đầu tư qua chat.

Nhiệm vụ: Tổng hợp dữ liệu từ tin tức, phân tích cơ bản, phân tích kỹ thuật rồi trả lời bằng văn xuôi tự nhiên, thân thiện — như một chuyên gia đang nói chuyện trực tiếp với khách hàng.

Cấu trúc trả lời gợi ý (không cần dùng heading cứng nhắc):
1. Mở đầu ngắn gọn về tình hình chung của cổ phiếu
2. Điểm nổi bật từ tin tức / cơ bản / kỹ thuật (chọn lọc, không liệt kê hết)
3. Khuyến nghị rõ ràng (Mua / Giữ / Chờ / Bán) kèm lý do ngắn gọn phù hợp khẩu vị rủi ro
4. Lưu ý rủi ro nếu có

Quy tắc:
- Viết như đang nói chuyện, không dùng bullet point dày đặc
- Không dùng từ kỹ thuật mà không giải thích
- Không bịa số liệu ngoài dữ liệu được cung cấp
- Kết thúc bằng một câu thân thiện, khuyến khích nhà đầu tư hỏi thêm nếu cần
"""


# ─────────────────────────────────────────────────────────────
# 🚀 Aggregator Agent
# ─────────────────────────────────────────────────────────────

def aggregator_agent(state: AgentState) -> AgentState:
    mode = state.get("mode", "api")
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
        # ── API mode: structured output (không cần history) ───
        if mode == "api":
            response = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                temperature=0.2,
                messages=[
                    {"role": "system", "content": AGGREGATOR_SYSTEM_PROMPT},
                    {"role": "user", "content": analysis_message},
                ],
                response_format=InvestmentRecommendation,
            )

            parsed: InvestmentRecommendation = response.choices[0].message.parsed

            # Tính confidence từ code, không dùng giá trị LLM tự tính
            confidence = calculate_confidence(parsed.scores)

            output = {
                "summary": parsed.summary,
                "recommendation": parsed.recommendation,
                "reasoning": parsed.reasoning,
                "confidence": confidence,
                "confidence_breakdown": {
                    "base": BASE_SCORE,
                    "technical_score": parsed.scores.technical_score / 100,
                    "fundamental_score": parsed.scores.fundamental_score / 100,
                    "news_score": parsed.scores.news_score / 100,
                    "consistency_score": parsed.scores.consistency_score / 100,
                },
            }

            print("[Aggregator] Output:")
            print(json.dumps(output, ensure_ascii=False, indent=2))

            return {"final_output": output}

        # ── Chatbot mode: plain text + inject history ─────────
        else:
            # Lấy lịch sử, trim xuống còn tối đa MAX_HISTORY_TURNS turn gần nhất
            # Mỗi turn = 1 HumanMessage + 1 AIMessage → MAX_HISTORY_TURNS * 2 message
            MAX_HISTORY_TURNS = 5
            history = state.get("messages", [])
            trimmed_history = history[-(MAX_HISTORY_TURNS * 2):]

            history_messages = [
                {"role": "assistant" if isinstance(m, AIMessage) else "user", "content": m.content}
                for m in trimmed_history
            ]

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.3,
                messages=[
                    {"role": "system", "content": AGGREGATOR_CHATBOT_SYSTEM_PROMPT},
                    *history_messages,          # lịch sử hội thoại
                    {"role": "user", "content": analysis_message},  # turn hiện tại
                ],
            )

            text = response.choices[0].message.content
            print(f"[Aggregator] Output (chatbot):\n{text}")

            return {
                "final_output": text,
                # Append cả HumanMessage (câu hỏi gốc) lẫn AIMessage (câu trả lời)
                # HumanMessage ở đây dùng user_input thô, không kèm data phân tích
                "messages": [
                    HumanMessage(content=user_input),
                    AIMessage(content=text),
                ],
            }

    except Exception as e:
        print(f"[Aggregator] Error: {str(e)}")

        fallback = (
            {"summary": "Không thể phân tích dữ liệu", "recommendation": "Chờ",
             "reasoning": "Lỗi hệ thống", "confidence": 0.0}
            if mode == "api"
            else "Xin lỗi, mình gặp sự cố khi phân tích. Bạn thử lại sau nhé!"
        )

        return {"error": str(e), "final_output": fallback}