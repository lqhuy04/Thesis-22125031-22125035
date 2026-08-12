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

Đọc toàn bộ dữ liệu kỹ thuật được cung cấp và trả về:
- score từ 0 đến 1, thể hiện mức độ tích cực/bullish của tín hiệu kỹ thuật trong
  đúng interval và khoảng thời gian đầu vào; đây không phải confidence.
- analysis giữ vai trò bản phân tích kỹ thuật: mô tả xu hướng giá, động lượng,
  volume, tín hiệu tích cực/tiêu cực và các tín hiệu đang mâu thuẫn.

THANG ĐIỂM BẮT BUỘC:
- 0.00-0.19: bearish rất mạnh; giá và phần lớn tín hiệu xác nhận xu hướng giảm.
- 0.20-0.39: bearish; áp lực giảm chiếm ưu thế nhưng chưa đồng thuận hoàn toàn.
- 0.40-0.59: trung lập/giằng co; tín hiệu yếu, thiếu xác nhận hoặc mâu thuẫn.
- 0.60-0.79: bullish; xu hướng tăng có nhiều tín hiệu xác nhận.
- 0.80-1.00: bullish rất mạnh; giá, động lượng và volume đồng thuận rõ rệt.
Không mặc định 0.5: phải đặt điểm trong band phản ánh đúng độ mạnh tín hiệu.

CÁCH ĐÁNH GIÁ:
1. Giá: xét returns nhiều horizon, tỷ lệ nến tăng/giảm, vị trí close trong biên
   độ và cấu trúc chuỗi recent_candles. Ưu tiên xu hướng bền hơn một nến đơn lẻ.
2. MA: kết hợp vị trí và độ dốc của giá, SMA20, SMA50. Giá trên các MA và
   SMA20 trên SMA50 chỉ tích cực mạnh khi các đường đang đi lên; giao cắt mới
   có ý nghĩa hơn nếu giá và volume xác nhận.
3. MACD: xét MACD so với signal, dấu và hướng histogram. Histogram mở rộng cùng
   hướng giá là xác nhận; histogram thu hẹp báo động lượng suy yếu. Không đánh
   giá giao cắt tách rời xu hướng giá.
4. RSI và KDJ: dùng để đo động lượng và quá mua/quá bán, không áp dụng máy móc.
   Quá mua trong xu hướng tăng mạnh không tự động là bearish nhưng làm giảm
   điểm nếu động lượng suy yếu; hồi phục từ quá bán chỉ tích cực khi giá/MACD
   hoặc volume xác nhận. Tìm phân kỳ giá-động lượng nếu chuỗi dữ liệu thể hiện.
5. Bollinger Bands: kết hợp vị trí giá, hướng middle band và độ rộng bands.
   Breakout biên trên kèm volume cao và động lượng đồng thuận có thể bullish;
   vượt biên không có volume hoặc động lượng suy yếu có rủi ro false breakout.
   Chạm biên dưới không tự động là cơ hội hồi phục.
6. Volume: so current với average_5/average_20 và diễn biến giá. Giá tăng với
   volume mở rộng củng cố tín hiệu; giá tăng nhưng volume co lại làm giảm điểm;
   giá giảm kèm volume cao là xác nhận bearish. Volume đột biến phải được đọc
   cùng hướng và thân nến, không mặc định là tích cực.
7. Đồng thuận: không lấy trung bình máy móc từng indicator. Tăng điểm khi giá,
   trend, momentum và volume cùng xác nhận; giảm điểm khi tín hiệu xung đột,
   chỉ xuất hiện trong một nến hoặc thiếu dữ liệu. `indicators.*.score` và
   `total_score/max_score` là kết quả rule tham khảo, không phải điểm bắt buộc
   và không được sao chép làm score nếu bối cảnh nhiều nến cho kết luận khác.

Quy tắc dữ liệu và đầu ra:
- Chỉ sử dụng dữ liệu đầu vào, không bịa thêm chỉ báo hoặc mức giá.
- Chỉ đánh giá các indicator xuất hiện trong đầu vào; không phạt vì indicator
  không được người dùng chọn.
- Phân biệt current_price dùng cho kế hoạch vào/ra với close cây nến cuối dùng
  cho technical. Hai nguồn có thể khác đơn vị, vì vậy không so sánh trực tiếp
  current_price với MA/Bollinger nếu đơn vị không đồng nhất.
- analysis phải giải thích các kết hợp quan trọng dẫn đến score, không chỉ liệt
  kê từng indicator, đồng thời vẫn nêu rõ các rủi ro hoặc tín hiệu đối nghịch.
- Không đưa ra giá chốt lời, cắt lỗ hay khuyến nghị mua/bán.
"""


class TechnicalAnalysisOutput(BaseModel):
    score: float = Field(ge=0, le=1)
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
    """Use the LLM to score and summarize the prepared technical context."""
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
        try:
            parsed = _call_technical_analysis_llm(
                technical_data,
                language,
            )
            score = round(parsed.score, 4)
            analysis = parsed.analysis.strip()
        except Exception:
            logger.exception("Technical LLM analysis failed")
            score = _calculate_score(technical_data)
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
