"""LLM-based article scoring and summarization for the v2 analysis graph."""

import logging

from pydantic import BaseModel, Field

from agentic_ai_v2.analyze.language import (
    localized_text,
    normalize_language,
    output_language_instruction,
)
from agentic_ai_v2.analyze.state import AgentState
from agentic_ai_v2.service.openai_service import _get_openai_client

logger = logging.getLogger(__name__)

_MODEL = "gpt-4o-mini"
_MAX_OUTPUT_TOKENS = 1_500
_NO_DATA_PREFIXES = (
    "Không có bài viết",
    "Không có dữ liệu tin tức",
)

_SYSTEM_PROMPT = """Bạn là chuyên gia phân tích tin tức chứng khoán Việt Nam.

Đọc duy nhất dữ liệu bài viết được cung cấp và trả về:
- score trong khoảng 0 đến 1, thể hiện mức độ tích cực của tin tức đối với cổ
  phiếu: 0 = rất tiêu cực, 0.5 = trung lập/không rõ, 1 = rất tích cực.
- analysis là bản tóm tắt ngắn gọn, nêu các động lực tích cực, rủi ro
  và tác động dự kiến đến doanh nghiệp/cổ phiếu.

Quy tắc:
- Không sử dụng kiến thức hoặc số liệu ngoài nội dung đầu vào.
- Gộp tin trùng lặp và ưu tiên sự kiện tác động trực tiếp.
- Không đưa ra giá mua, giá bán hoặc khuyến nghị giao dịch.
- Nếu thông tin mâu thuẫn hoặc chưa đủ, phải nói rõ và chấm gần mức trung lập.
"""


class ArticleAnalysisOutput(BaseModel):
    score: float = Field(ge=0, le=1)
    analysis: str = Field(min_length=1)


def _call_article_analysis_llm(
    article_text: str,
    language: str = "vi",
) -> ArticleAnalysisOutput:
    client = _get_openai_client()
    response = client.beta.chat.completions.parse(
        model=_MODEL,
        temperature=0.1,
        max_tokens=_MAX_OUTPUT_TOKENS,
        messages=[
            {
                "role": "system",
                "content": (
                    f"{_SYSTEM_PROMPT}\n\n"
                    f"{output_language_instruction(language)}"
                ),
            },
            {"role": "user", "content": article_text},
        ],
        response_format=ArticleAnalysisOutput,
    )
    parsed = response.choices[0].message.parsed
    if parsed is None:
        raise ValueError("OpenAI returned an empty article analysis")
    return parsed


def article_analysis_agent(state: AgentState) -> dict:
    """Score and summarize text prepared by article_agent."""
    language = normalize_language(state.get("language"))
    article_text = (state.get("agent_results") or {}).get("article_agent")

    if not isinstance(article_text, str) or not article_text.strip():
        output = {
            "score": 0.0,
            "analysis": localized_text(
                language,
                vi="Không có dữ liệu tin tức.",
                en="No news data is available.",
            ),
        }
    elif article_text.strip().startswith(_NO_DATA_PREFIXES):
        output = {
            "score": 0.0,
            "analysis": localized_text(
                language,
                vi="Không có dữ liệu tin tức.",
                en="No news data is available.",
            ),
        }
    else:
        try:
            parsed = _call_article_analysis_llm(
                article_text,
                language,
            )
            output = {
                "score": round(parsed.score, 4),
                "analysis": parsed.analysis.strip(),
            }
        except Exception:
            logger.exception("Article LLM analysis failed")
            output = {
                "score": 0.0,
                "analysis": localized_text(
                    language,
                    vi="Không thể phân tích dữ liệu tin tức.",
                    en="Unable to analyze the news data.",
                ),
            }

    print(f"Article Analysis output:\n{output}")

    return {
        "agent_results": {
            "article_analysis_agent": output,
        },
    }
