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

class InvestmentRecommendation(BaseModel):
    summary: str = Field(description="Phân tích tổng thể đầy đủ về tình hình cổ phiếu từ 3 nguồn tin tức, phân tích cơ bản, kỹ thuật")

    recommendation: Literal["Mua", "Giữ", "Chờ", "Bán"] = Field(
        description="Hành động đề xuất"
    )

    reasoning: str = Field(description="Giải thích cho recommendation từ khẩu vị rủi ro của user kết hợp dẫn chứng từ số liệu, tài liệu của các nguồn dựa trên dữ liệu phân tích")

    confidence: float = Field(
        description="Độ tin cậy từ 0 đến 1",
        ge=0,
        le=1
    )


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
  + confidence: từ 0 → 1

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

Base = 0.5
+0.1 nếu technical rõ ràng
+0.1 nếu fundamental tốt
+0.1 nếu tin tức tích cực
-0.1 nếu tin tiêu cực
-0.1 nếu tín hiệu mâu thuẫn
Clamp: 0 → 1

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
            output = parsed.model_dump()

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