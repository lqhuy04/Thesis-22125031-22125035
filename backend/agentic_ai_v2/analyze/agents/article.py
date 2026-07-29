"""News analysis node for the v2 analysis graph."""

import logging
from datetime import date, datetime
from typing import Any

from agentic_ai_v2.analyze.state import AgentState
from agentic_ai_v2.service.openai_service import _get_openai_client
from app.services.articles_service import ArticlesService

logger = logging.getLogger(__name__)

_MODEL = "gpt-4o-mini"
_MAX_ARTICLES = 50
_MAX_DESCRIPTION_LENGTH = 1_200

_SYSTEM_PROMPT = """Bạn là chuyên gia phân tích tin tức tài chính Việt Nam.

Hãy tổng hợp các bài viết được cung cấp thành báo cáo Markdown ngắn gọn theo cấu trúc:

## Phân tích tin tức
### Tóm tắt chính
### Tín hiệu tích cực
### Rủi ro
### Đánh giá chung

Quy tắc:
- Chỉ sử dụng thông tin có trong danh sách bài viết.
- Ưu tiên sự kiện có ảnh hưởng trực tiếp đến doanh nghiệp và giá cổ phiếu.
- Gộp các bài trùng nội dung, không liệt kê lại từng bài.
- Nêu rõ khi thông tin chưa đủ để kết luận.
- Không đưa ra khuyến nghị mua hoặc bán.
- Trả lời bằng tiếng Việt.
"""


def _parse_plan_date(value: Any, field_name: str) -> date:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Missing article plan field: {field_name}")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"Invalid article plan field {field_name}: {value}"
        ) from exc


def _publication_date(article: Any) -> date | None:
    published_at = getattr(article, "time", None)
    if isinstance(published_at, datetime):
        return published_at.date()
    if isinstance(published_at, date):
        return published_at
    if isinstance(published_at, str):
        try:
            return datetime.fromisoformat(
                published_at.replace("Z", "+00:00")
            ).date()
        except ValueError:
            return None
    return None


def _filter_articles(
    articles: list[Any],
    from_date: date,
    to_date: date,
) -> list[Any]:
    filtered = [
        article
        for article in articles
        if (
            (published_date := _publication_date(article)) is not None
            and from_date <= published_date <= to_date
        )
    ]
    filtered.sort(
        key=lambda article: _publication_date(article) or date.min,
        reverse=True,
    )
    return filtered[:_MAX_ARTICLES]


def _first_text(article: Any, *fields: str) -> str:
    for field in fields:
        value = getattr(article, field, None)
        if value:
            return str(value).strip()
    return ""


def _build_articles_message(
    symbol: str,
    from_date: date,
    to_date: date,
    articles: list[Any],
) -> str:
    lines = [
        f"Mã cổ phiếu: {symbol}",
        f"Khoảng tin tức: {from_date.isoformat()} đến {to_date.isoformat()}",
        f"Số bài viết: {len(articles)}",
        "",
    ]

    for index, article in enumerate(articles, start=1):
        published_date = _publication_date(article)
        title = _first_text(article, "title") or "Không có tiêu đề"
        description = _first_text(article, "summary", "description")
        sentiment = _first_text(article, "sentiment")

        lines.append(
            f"{index}. [{published_date.isoformat()}] {title}"
        )
        if description:
            lines.append(
                f"   Nội dung: {description[:_MAX_DESCRIPTION_LENGTH]}"
            )
        if sentiment:
            lines.append(f"   Sentiment có sẵn: {sentiment}")
        lines.append("")

    return "\n".join(lines)


def _analyze_articles(
    symbol: str,
    from_date: date,
    to_date: date,
    articles: list[Any],
) -> str:
    client = _get_openai_client()
    response = client.chat.completions.create(
        model=_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _build_articles_message(
                    symbol=symbol,
                    from_date=from_date,
                    to_date=to_date,
                    articles=articles,
                ),
            },
        ],
    )
    content = response.choices[0].message.content
    if not content or not content.strip():
        raise ValueError("OpenAI returned an empty article analysis")
    return content.strip()


def article_agent(state: AgentState) -> dict:
    """Analyze stock news within the date range created by the orchestrator."""
    symbol = state.get("symbol", "").strip().upper()
    article_plan = (state.get("plan") or {}).get("article") or {}

    try:
        from_date = _parse_plan_date(
            article_plan.get("from_date"),
            "from_date",
        )
        to_date = _parse_plan_date(
            article_plan.get("to_date"),
            "to_date",
        )
        if from_date > to_date:
            raise ValueError("Article plan from_date is after to_date")

        articles = ArticlesService.get_articles_by_stock_symbol(
            stock_symbol=symbol
        )
        filtered_articles = _filter_articles(
            articles=articles,
            from_date=from_date,
            to_date=to_date,
        )

        if not filtered_articles:
            output = (
                "Không có bài viết nào trong khoảng thời gian "
                f"{from_date.isoformat()} đến {to_date.isoformat()}."
            )
        else:
            output = _analyze_articles(
                symbol=symbol,
                from_date=from_date,
                to_date=to_date,
                articles=filtered_articles,
            )
    except Exception:
        logger.exception("Article analysis failed for %s", symbol)
        output = "Không có dữ liệu phân tích tin tức."

    print(f"Article analysis output for {symbol}:\n{output}")

    return {
        "agent_results": {
            "article_agent": output,
        },
    }
