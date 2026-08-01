"""LLM-based technical summarization for the v2 analysis graph."""

import json
import logging
import math
from typing import Any

from pydantic import BaseModel, Field

from agentic_ai_v2.analyze.language import (
    localized_text,
    normalize_language,
    output_language_instruction,
)
from agentic_ai_v2.analyze.state import AgentState
from agentic_ai_v2.service.deepseek_service import create_structured_completion

logger = logging.getLogger(__name__)

_MAX_OUTPUT_TOKENS = 1_500

_SYSTEM_PROMPT = """Bạn là chuyên gia phân tích kỹ thuật cổ phiếu Việt Nam.

Hãy tóm tắt dữ liệu kỹ thuật được cung cấp thành trường analysis.
Phân tích giá hiện tại, khung thời gian và từng chỉ báo hiện diện trong đầu vào;
nêu tín hiệu tích cực, tiêu cực và trạng thái xu hướng.

Quy tắc:
- Chỉ sử dụng dữ liệu đầu vào, không bịa thêm chỉ báo hoặc mức giá.
- Phân biệt current_price dùng cho kế hoạch vào/ra với close của cây nến cuối
  đang được dùng để chấm các chỉ báo.
- Không tự chấm hoặc thay đổi score; score được hệ thống tính bằng Python.
- Không đưa ra giá chốt lời, cắt lỗ hay khuyến nghị mua/bán.
"""


class TechnicalAnalysisOutput(BaseModel):
    analysis: str = Field(min_length=1)


def _to_finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _calculate_score(technical_data: dict[str, Any]) -> float:
    total_score = _to_finite_float(technical_data.get("total_score"))
    max_score = _to_finite_float(technical_data.get("max_score"))
    if total_score is None or max_score is None or max_score <= 0:
        return 0.0
    return round(min(max(total_score / max_score, 0.0), 1.0), 4)


def _call_technical_analysis_llm(
    technical_data: dict[str, Any],
    language: str = "vi",
) -> TechnicalAnalysisOutput:
    return create_structured_completion(
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
            {
                "role": "user",
                "content": json.dumps(
                    technical_data,
                    ensure_ascii=False,
                    indent=2,
                ),
            },
        ],
        output_model=TechnicalAnalysisOutput,
    )


def technical_analysis_agent(state: AgentState) -> dict:
    """Summarize technical data and attach its deterministic normalized score."""
    language = normalize_language(state.get("language"))
    technical_data = (state.get("agent_results") or {}).get("technical_agent")

    if not isinstance(technical_data, dict) or technical_data.get("error"):
        analysis = localized_text(
            language,
            vi="Không có dữ liệu phân tích kỹ thuật.",
            en="No technical analysis data is available.",
        )
        output = {
            "score": 0.0,
            "analysis": analysis,
        }
    else:
        score = _calculate_score(technical_data)
        try:
            parsed = _call_technical_analysis_llm(
                technical_data,
                language,
            )
            analysis = parsed.analysis.strip()
        except Exception:
            logger.exception("Technical LLM analysis failed")
            analysis = localized_text(
                language,
                vi="Không thể tóm tắt dữ liệu phân tích kỹ thuật.",
                en="Unable to summarize the technical analysis data.",
            )

        output = {
            "score": score,
            "analysis": analysis,
        }

    print(f"Technical Analysis output:\n{output}")

    return {
        "agent_results": {
            "technical_analysis_agent": output,
        },
    }
