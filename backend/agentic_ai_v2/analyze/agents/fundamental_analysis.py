"""LLM-based fundamental scoring and summarization for the v2 graph."""

import logging

from pydantic import BaseModel, Field

from agentic_ai_v2.analyze.state import AgentState
from agentic_ai_v2.service.openai_service import _get_openai_client

logger = logging.getLogger(__name__)

_MODEL = "gpt-4o-mini"
_MAX_OUTPUT_TOKENS = 1_800
_NO_DATA_PREFIX = "Không có dữ liệu phân tích cơ bản"

_SYSTEM_PROMPT = """Bạn là chuyên gia phân tích cơ bản cổ phiếu Việt Nam.

Đọc duy nhất báo cáo chỉ số cơ bản được cung cấp và trả về:
- score trong khoảng 0 đến 1, thể hiện sức khỏe và mức độ hấp dẫn cơ bản:
  0 = rất yếu/rủi ro cao, 0.5 = trung lập, 1 = rất khỏe/hấp dẫn.
- analysis là bản tóm tắt tiếng Việt, nêu xu hướng quan trọng, điểm mạnh, điểm
  yếu, rủi ro và so sánh ngành nếu đầu vào có dữ liệu ngành.

Quy tắc:
- Không bịa số liệu hoặc sử dụng dữ liệu ngoài đầu vào.
- Xem xét đồng thời thanh khoản, đòn bẩy, hiệu quả, sinh lời, tăng trưởng và
  định giá; với doanh nghiệp tài chính phải tôn trọng bộ chỉ số CAMEL/P-B.
- CAGR không tính được phải được mô tả là thiếu dữ liệu, không suy diễn.
- Không đưa ra giá mua, giá bán hoặc khuyến nghị giao dịch.
"""


class FundamentalAnalysisOutput(BaseModel):
    score: float = Field(ge=0, le=1)
    analysis: str = Field(min_length=1)


def _call_fundamental_analysis_llm(
    fundamental_text: str,
) -> FundamentalAnalysisOutput:
    client = _get_openai_client()
    response = client.beta.chat.completions.parse(
        model=_MODEL,
        temperature=0.1,
        max_tokens=_MAX_OUTPUT_TOKENS,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": fundamental_text},
        ],
        response_format=FundamentalAnalysisOutput,
    )
    parsed = response.choices[0].message.parsed
    if parsed is None:
        raise ValueError("OpenAI returned an empty fundamental analysis")
    return parsed


def fundamental_analysis_agent(state: AgentState) -> dict:
    """Score and summarize text prepared by fundamental_agent."""
    fundamental_text = (state.get("agent_results") or {}).get(
        "fundamental_agent"
    )

    if not isinstance(fundamental_text, str) or not fundamental_text.strip():
        output = {
            "score": 0.0,
            "analysis": "Không có dữ liệu phân tích cơ bản.",
        }
    elif fundamental_text.strip().startswith(_NO_DATA_PREFIX):
        output = {
            "score": 0.0,
            "analysis": fundamental_text.strip(),
        }
    else:
        try:
            parsed = _call_fundamental_analysis_llm(fundamental_text)
            output = {
                "score": round(parsed.score, 4),
                "analysis": parsed.analysis.strip(),
            }
        except Exception:
            logger.exception("Fundamental LLM analysis failed")
            output = {
                "score": 0.0,
                "analysis": "Không thể phân tích dữ liệu cơ bản.",
            }

    print(f"Fundamental Analysis output:\n{output}")

    return {
        "agent_results": {
            "fundamental_analysis_agent": output,
        },
    }
