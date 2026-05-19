from typing import Literal
from datetime import datetime
from pydantic import BaseModel, Field

from agentic_ai.analyze.state import AgentState
from app.services.articles_service import ArticlesService
from agentic_ai.service.openai_service import _get_openai_client


# ─────────────────────────────────────────────────────────────
# Structured output schema
# ─────────────────────────────────────────────────────────────

SentimentLiteral = Literal[
    "TÍCH CỰC RÕ RÀNG",
    "TÍCH CỰC NHẸ",
    "TRUNG LẬP",
    "TIÊU CỰC NHẸ",
    "TIÊU CỰC RÕ RÀNG",
    "KHÔNG CÓ TIN",
]


class ArticleAnalysis(BaseModel):
    sentiment: SentimentLiteral = Field(
        description=(
            "Phân loại sentiment tổng hợp từ TẤT CẢ tin có liên quan đến cổ phiếu:\n"
            "  TÍCH CỰC RÕ RÀNG = thua/lỗ, tăng trưởng mạnh, cổ tức tốt, insider mua, hợp đồng lớn\n"
            "  TÍCH CỰC NHẸ    = tin ngành tốt, vĩ mô ổn định\n"
            "  TRUNG LẬP        = tin chung, không ảnh hưởng trực tiếp\n"
            "  TIÊU CỰC NHẸ    = áp lực ngành, vĩ mô bất lợi\n"
            "  TIÊU CỰC RÕ RÀNG = thua lỗ, vi phạm, bán ròng mạnh, kiện tụng\n"
            "  KHÔNG CÓ TIN     = không có bài viết liên quan/hữu ích nào"
        )
    )
    summary: str = Field(
        description=(
            "Tóm tắt 2–4 câu các thông tin quan trọng nhất. "
            "Nếu sentiment = KHÔNG CÓ TIN → để chuỗi rỗng."
        )
    )
    key_events: list[str] = Field(
        description=(
            "Danh sách 0–5 sự kiện chính ảnh hưởng tới cổ phiếu (mỗi item 1 câu ngắn). "
            "Chỉ điền sự kiện CÓ TRONG bài viết, không suy đoán. "
            "Để [] nếu không có gì đáng kể."
        )
    )


ARTICLE_SUMMARY_PROMPT = """Bạn là chuyên gia phân tích tài chính.
Dựa trên các bài viết tin tức về cổ phiếu dưới đây, hãy lọc ra những bài có thông tin hữu ích và liên quan,
sau đó phân loại sentiment và tóm tắt.

Quy tắc phân loại sentiment:
- TÍCH CỰC RÕ RÀNG: tin có tác động mạnh và rõ ràng theo hướng tốt (lợi nhuận tăng đột biến,
  hợp đồng lớn, insider mua vào, cổ tức cao, mở rộng kinh doanh).
- TÍCH CỰC NHẸ: tin ngành/vĩ mô ổn định nghiêng về phía thuận lợi.
- TRUNG LẬP: tin chung không tác động trực tiếp lên cổ phiếu.
- TIÊU CỰC NHẸ: áp lực ngành, biến động vĩ mô bất lợi nhưng chưa nghiêm trọng.
- TIÊU CỰC RÕ RÀNG: thua lỗ, vi phạm pháp luật, bán ròng mạnh, kiện tụng nghiêm trọng.
- KHÔNG CÓ TIN: không có bài viết liên quan hoặc hữu ích.

Quy tắc tóm tắt:
- Không bịa thông tin ngoài dữ liệu.
- Không liệt kê hết tất cả tin — chọn lọc 2–3 điểm nổi bật nhất.
- key_events phải dẫn được về bài cụ thể (1 sự kiện = 1 câu)."""


def _build_articles_message(symbol: str, articles: list) -> str:
    lines = [f"Cổ phiếu: {symbol}\n"]
    for article in articles:
        lines.append(f"- [{article.time.date()}] {article.title}")
        if article.summary:
            lines.append(f"  Tóm tắt: {article.summary}")
        if article.sentiment:
            lines.append(f"  Sentiment: {article.sentiment}")
        lines.append("")
    return "\n".join(lines)


def _format_article_display(symbol: str, parsed: ArticleAnalysis, article_count: int) -> str:
    if parsed.sentiment == "KHÔNG CÓ TIN":
        return f"## Phân tích tin tức — {symbol}\nKhông có tin tức hữu ích."

    events_lines = "\n".join(f"- {e}" for e in parsed.key_events) or "- (không có sự kiện nổi bật)"

    return f"""
## Phân tích tin tức — {symbol}
- Sentiment: **{parsed.sentiment}**
- Số bài viết phân tích: {article_count}

### Tóm tắt
{parsed.summary}

### Sự kiện chính
{events_lines}
""".strip()


def article_agent(state: AgentState) -> AgentState:
    myTask = state.get("plan", {}).get("article_agent", {})
    symbol = state.get("symbol", "")
    from_date = myTask.get("from_date", "")
    to_date = myTask.get("to_date", "")

    result = ArticlesService.get_articles_by_stock_symbol(stock_symbol=symbol)

    filtered = result
    if from_date or to_date:
        start = datetime.fromisoformat(from_date) if from_date else None
        if to_date:
            end = datetime.fromisoformat(to_date)
            if end.hour == 0 and end.minute == 0 and end.second == 0:
                end = end.replace(hour=23, minute=59, second=59)
        else:
            end = None

        filtered = [
            article for article in result
            if (start is None or article.time >= start)
            and (end is None or article.time <= end)
        ]

    if not filtered:
        return {
            "agent_results": {
                "article_agent": {
                    "display": "Không có bài viết nào trong khoảng thời gian được chỉ định.",
                    "sentiment": "KHÔNG CÓ TIN",
                    "summary": "",
                    "key_events": [],
                    "article_count": 0,
                },
            },
        }

    client = _get_openai_client()
    analysis_message = _build_articles_message(symbol, filtered)

    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": ARTICLE_SUMMARY_PROMPT},
                {"role": "user",   "content": analysis_message},
            ],
            response_format=ArticleAnalysis,
        )

        parsed: ArticleAnalysis = response.choices[0].message.parsed

        display = _format_article_display(symbol, parsed, len(filtered))
        print("[Article Analysis Agent] Output:", display)
        print(f"[Article Analysis Agent] Sentiment: {parsed.sentiment}")

        return {
            "agent_results": {
                "article_agent": {
                    "display": display,
                    "sentiment": parsed.sentiment,
                    "summary": parsed.summary,
                    "key_events": parsed.key_events,
                    "article_count": len(filtered),
                },
            },
        }

    except Exception as e:
        print(f"[Article Analysis Agent] Error: {str(e)}")
        return {
            "agent_results": {
                "article_agent": {
                    "display": "Lỗi khi phân tích tin tức.",
                    "sentiment": "KHÔNG CÓ TIN",
                    "summary": "",
                    "key_events": [],
                    "article_count": len(filtered),
                    "error": str(e),
                },
            },
        }
