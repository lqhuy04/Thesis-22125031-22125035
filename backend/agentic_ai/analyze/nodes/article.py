from agentic_ai.analyze.state import AgentState
from agentic_ai.analyze.selection import get_selection
from app.services.articles_service import ArticlesService
from agentic_ai.service.openai_service import _get_openai_client
from datetime import datetime

ARTICLE_SUMMARY_PROMPT = """Bạn là chuyên gia phân tích tài chính. 
Dựa trên các bài viết tin tức về cổ phiếu dưới đây, hãy lọc ra những bài có thông tin hữu ích và liên quan, 
sau đó tóm tắt những thông tin quan trọng nhất.

Nếu không có bài viết nào hữu ích hoặc liên quan, hãy trả lời đúng một câu: "Không có tin tức hữu ích."

Nếu có tin tức hữu ích, trả lời theo cấu trúc:
1. Tóm tắt tin tức chính
2. Điểm tích cực
3. Điểm tiêu cực / rủi ro"""

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


def article_agent(state: AgentState) -> AgentState:
    # Người dùng tắt nguồn tin tức → bỏ qua
    if not get_selection(state)["news"]:
        return {
            "agent_results": {
                "article_agent": "Người dùng đã tắt phân tích tin tức.",
            },
        }

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
                "article_agent": "Không có bài viết nào trong khoảng thời gian được chỉ định.",
            },
        }

    client = _get_openai_client()
    analysis_message = _build_articles_message(symbol, filtered)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[
            {"role": "system", "content": ARTICLE_SUMMARY_PROMPT},
            {"role": "user",   "content": analysis_message},
        ],
    )

    summary = response.choices[0].message.content

    print("[Article Analysis Agent] Output:", summary)

    return {
        "agent_results": {
            "article_agent": summary,
        },
    }