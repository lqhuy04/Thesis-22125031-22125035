"""
aggregator.py — Aggregator Agent (FINAL VERSION)

- Tổng hợp dữ liệu từ:
    + article_agent
    + fundamental_analysis_agent
    + technical_analysis_agent

- Gọi OpenAI để tạo structured output:
    + summary
    + recommendation (enum)
    + reasoning
    + confidence (0 → 1)

- Có xét thêm khẩu vị rủi ro (risk_appetite)
"""

import json
from typing import Literal
from pydantic import BaseModel, Field

from service.openai_service import _get_openai_client
from state import AgentState


# ─────────────────────────────────────────────────────────────
# 📦 Structured Output Schema
# ─────────────────────────────────────────────────────────────

class InvestmentRecommendation(BaseModel):
    summary: str = Field(description="Phân tích tổng thể đầy đủ về tình hình cổ phiếu từ 3 nguồn tin tức, phân tích cơ bản, kỹ thuật")

    recommendation: Literal["mua", "giữ", "chờ", "bán"] = Field(
        description="Hành động đề xuất"
    )

    reasoning: str = Field(description="Giải thích cho recommendation từ khẩu vị rủi ro của user kết hợp dẫn chứng từ số liệu, tài liệu của các nguồn dựa trên dữ liệu phân tích")

    confidence: float = Field(
        description="Độ tin cậy từ 0 đến 1",
        ge=0,
        le=1
    )


# ─────────────────────────────────────────────────────────────
# 🧠 Prompt
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
  + recommendation: ["mua", "giữ", "chờ", "bán"]
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
  + Khối ngoại bán ròng
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
- Cắt lên signal → tín hiệu mua sớm
- Cắt xuống signal → tín hiệu bán

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

Khoảng cách:
- Giá cách xa MA → có thể quá mua / quá bán

────────────────────────
5. KDJ (Stochastic Oscillator nâng cao):

- K, D, J đều < 20 → oversold → có thể hồi
- K, D, J > 80 → overbought → dễ điều chỉnh

Tín hiệu:
- K cắt lên D → bullish (mua)
- K cắt xuống D → bearish (bán)

Đặc biệt:
- J rất cao (>100) → quá mua mạnh
- J rất thấp (<0) → quá bán mạnh

────────────────────────
6. Price Action:
- Higher highs + higher lows → uptrend
- Lower highs + lower lows → downtrend
- Sideway → chưa rõ xu hướng
- Breakout → bullish mạnh
- Breakdown → bearish mạnh

────────────────────────
7. Volume:
- Giá tăng + volume tăng → xác nhận xu hướng
- Giá tăng + volume giảm → yếu
- Giá giảm + volume tăng → bán mạnh
- Volume thấp → thiếu xác nhận

────────────────────────
👉 KẾT LUẬN TECHNICAL (BẮT BUỘC):

Model phải tổng hợp các tín hiệu trên và phân loại:

- Strong bullish
- Weak bullish
- Neutral
- Weak bearish
- Strong bearish

────────────────────────
III. PHÂN TÍCH CƠ BẢN (FUNDAMENTAL)

1. Định giá:
- PE < 10 → rẻ
- PE 10–18 → hợp lý
- PE > 20 → đắt

2. Chất lượng:
- ROE > 20% → rất tốt
- ROE 15–20% → tốt
- ROE < 10% → yếu

3. Đòn bẩy:
- Debt/Equity < 0.5 → an toàn
- 0.5–1 → trung bình
- > 1 → rủi ro

4. Tăng trưởng:
- Doanh thu & lợi nhuận tăng → tích cực
- Chậm / giảm → tiêu cực

👉 Kết luận fundamental:
- Strong / Stable / Weak

────────────────────────
IV. KẾT HỢP TÍN HIỆU (SIGNAL FUSION)

Ưu tiên:
- Ngắn hạn → Technical
- Trung & dài hạn → Fundamental

Logic:
- Technical bullish + Fundamental tốt → "mua"
- Technical yếu + Fundamental tốt → "chờ" hoặc "giữ"
- Technical xấu + News xấu → "bán"
- Mixed signals → "chờ"

────────────────────────
V. KHẨU VỊ RỦI RO (RISK ADAPTATION)

Dựa vào risk_appetite:

1. Rủi ro thấp:
- Tránh "mua" khi chưa rõ xu hướng
- Ưu tiên "giữ" hoặc "chờ"

2. Kỳ vọng thu nhập thụ động:
- Ưu tiên cổ phiếu:
  + ổn định
  + ROE cao
  + nợ thấp

3. Ngắn hạn:
- Ưu tiên technical hơn fundamental

────────────────────────
VI. QUY TẮC RA QUYẾT ĐỊNH (FINAL DECISION)

- "mua":
  + Technical bullish
  + Không có tin xấu lớn
  + Fundamental ổn

- "giữ":
  + Đang có vị thế
  + Xu hướng chưa rõ
  + Không xấu

- "chờ":
  + Tín hiệu mâu thuẫn
  + Sideway / chưa rõ xu hướng
  + Risk cao

- "bán":
  + Technical bearish rõ
  + Tin tức xấu
  + Breakdown

────────────────────────
VII. CONFIDENCE SCORING

Base = 0.5

+0.1 nếu:
- Technical rõ ràng

+0.1 nếu:
- Fundamental tốt

+0.1 nếu:
- Tin tức tích cực

-0.1 nếu:
- Tin tiêu cực

-0.1 nếu:
- Tín hiệu mâu thuẫn

Clamp:
- Min: 0
- Max: 1

────────────────────────
VIII. QUY TẮC QUAN TRỌNG

- Không suy đoán ngoài dữ liệu
- Không nói chung chung
- Phải giải thích rõ logic
- recommendation bắt buộc thuộc enum:
  ["mua", "giữ", "chờ", "bán"]

- Output CHỈ JSON, không thêm text
"""

# ─────────────────────────────────────────────────────────────
# 🚀 Aggregator Agent
# ─────────────────────────────────────────────────────────────

def aggregator_agent(state: AgentState) -> AgentState:
    print("[Aggregator] Tổng hợp kết quả...")

    client = _get_openai_client()

    results = state.get("agent_results", {})
    risk_appetite = state.get("risk_appetite", {})
    user_input = state.get("user_input", "")

    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": AGGREGATOR_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"""
DỮ LIỆU PHÂN TÍCH:

{json.dumps(results, ensure_ascii=False, indent=2)}

────────────────────────
KHẨU VỊ RỦI RO:

{json.dumps(risk_appetite, ensure_ascii=False, indent=2)}

────────────────────────
YÊU CẦU:

{user_input}
"""
                }
            ],
            response_format=InvestmentRecommendation
        )

        parsed: InvestmentRecommendation = response.choices[0].message.parsed
        output = parsed.model_dump()

        print("[Aggregator] Output:")
        print(json.dumps(output, ensure_ascii=False, indent=2))

        return {
            "final_output": output
        }

    except Exception as e:
        print(f"[Aggregator] Error: {str(e)}")

        return {
            "error": str(e),
            "final_output": {
                "summary": "Không thể phân tích dữ liệu",
                "recommendation": "chờ",
                "reasoning": "Lỗi hệ thống khi xử lý dữ liệu",
                "confidence": 0.0
            }
        }