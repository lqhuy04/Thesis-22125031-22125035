import json
from langchain_core.messages import HumanMessage, AIMessage

from agentic_ai.service.openai_service import _get_openai_client
from agentic_ai.chatbot.state import ChatbotSystemState, IntentJob


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

def aggregator_agent(state: ChatbotSystemState, job: IntentJob) -> dict:
    client = _get_openai_client()

    results = job.get("agent_results", {})
    risk_appetite = state.get("risk_appetite", {})
    user_input = job.get("user_input", "")

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
      }

    except Exception as e:
        print(f"[Aggregator] Error: {str(e)}")

        fallback =  "Xin lỗi, mình gặp sự cố khi phân tích. Bạn thử lại sau nhé!"

        return {"error": str(e), "final_output": fallback}