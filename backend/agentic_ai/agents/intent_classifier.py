"""
intent_classifier.py — Intent Classifier Agent

Phân loại input thành LIST các intent.
Mỗi intent sẽ được xử lý song song bởi một agent riêng.
"""

from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage

from agentic_ai.service.openai_service import _get_openai_client
from agentic_ai.state import AgentState


# ─────────────────────────────────────────────────────────────
# 📦 Constants
# ─────────────────────────────────────────────────────────────

MARKET_INDICES = ["VNINDEX", "VN30", "VN100", "HNXIndex", "HNXUpcomIndex"]

CATEGORIES = [
    "Hàng Tiêu dùng", "Internet", "Nước đóng chai", "Dịch vụ Bất động sản thương mại",
    "Công nghệ Thông tin", "Dịch vụ kho bãi", "Nước", "Vận tải Thủy", "Bảo hiểm nhân thọ",
    "Đồ gia dụng một lần", "Trồng Cà phê, trà, ca cao", "Sản xuất gạch", "Bất động sản dân cư",
    "Lâm nghiệp và Giấy", "Vận tải nội địa", "Đào tạo & Việc làm", "Chuyển phát nhanh",
    "Thiết bị y tế", "Bao bì, đóng gói bằng nhựa", "Đồ chơi", "Sản xuất ô tô", "Nguyên vật liệu",
    "Sản phẩm từ sữa", "Cửa hàng tiện dụng", "Xây dựng", "Sản xuất, chế biến thép",
    "Phân phối dược phẩm", "Ngân hàng", "Vận tải hành khách & Du lịch", "Kim loại",
    "Thực phẩm chế biến", "Nước & Khí đốt", "Hàng May mặc", "Vận tải quốc tế",
    "Sản xuất Dầu khí", "Containers & Đóng gói", "Hóa chất hàng hóa khác", "Hỗ trợ vận tải",
    "Thiết bị gia dụng", "Vật liệu xây dựng & Nội thất", "Thùng chứa và bao bì khác", "Lốp xe",
    "Hàng cá nhân & Gia dụng", "Nhựa, cao su & sợi", "Dịch vụ Bất động sản Công nghiệp",
    "Phụ tùng ô tô", "Bán lẻ phức hợp", "Nhôm", "Bán lẻ", "Thức ăn gia súc",
    "Công nghiệp phức hợp", "Y tế", "Tiện ích khác", "Công nghệ sinh học", "Điện tử tiêu dùng",
    "Thiết bị và Phần cứng", "Du lịch & Giải trí", "Động vật giết mổ và chế biến",
    "Chất thải & Môi trường", "Dịch vụ Bất động sản khác", "Vận tải hành khách đường bộ",
    "Dược phẩm và Y tế", "Đồ uống & giải khát", "Đồ gia dụng lâu bền",
    "Thiết bị và Dịch vụ Dầu khí", "Siêu thị", "Nhựa", "Dịch vụ Bất động sản bán lẻ",
    "Tư vấn & Hỗ trợ Kinh doanh", "Nhà hàng và quán bar", "Hải sản chế biến và đóng gói",
    "Quản lý tài sản", "Dịch vụ Sân bay", "Quỹ đầu tư", "Khai thác Than",
    "Phát triển & vận hành Bất động sản khác", "Xi măng", "Dịch vụ tiêu dùng chuyên ngành",
    "Hàng hóa giải trí", "Hàng gia dụng", "Tư Vấn, Định giá, Môi giới Bất động sản",
    "Phân bón", "Dịch vụ giải trí", "Thương mại (Bán buôn) sắt thép", "Văn phòng cho thuê",
    "Dịch vụ truyền thông", "Phần mềm & Dịch vụ Máy tính", "Lâm sản và Chế biến gỗ",
    "Phân phối thực phẩm", "Điện, nước & xăng dầu khí đốt", "Thiết bị điện",
    "Đồ uống không cồn khác", "Sách, ấn bản & sản phẩm văn hóa", "Bất động sản công nghiệp",
    "Sản xuất giấy", "Tài chính cá nhân", "Dịch vụ Bất động sản dân cư", "Hóa chất",
    "Công nghiệp", "Tài chính đặc biệt", "Nước trái cây", "Hàng công nghiệp",
    "Dịch vụ Tiêu dùng", "Dịch vụ tài chính", "Các dịch vụ kinh doanh bán lẻ khác",
    "Đại siêu thị", "Dược phẩm", "Nhà cung cấp thiết bị", "Bảo hiểm phi nhân thọ",
    "Viễn thông cố định", "Hàng cá nhân", "Nuôi trồng thủy hải sản", "Đường sắt",
    "Sản xuất & Phân phối Điện", "Khai thác đá", "Vật liệu xây dựng bán buôn",
    "Môi giới chứng khoán", "Thiết bị và Dịch vụ Y tế", "Hàng & Dịch vụ Công nghiệp",
    "Bến xe khách", "Dịch vụ hàng không", "Sản xuất thực phẩm", "Dầu khí",
    "Chăn nuôi gia súc, gia cầm", "Ngân hàng thương mại truyền thống", "Tài chính",
    "Tinh bột, rau có chất béo", "Khách sạn, resort", "Phân phối thực phẩm & dược phẩm",
    "Nguyên liệu chế biến, dầu ăn, gia vị (bột nở, hương liệu, etc)", "Hạt, cây giống thương mại",
    "Vật liệu bao bì, đóng gói bán buôn", "Xây dựng và Vật liệu",
    "Sản phẩm hóa dầu, Nông dược & Hóa chất khác", "Trồng ngũ cốc, rau, trái cây & hạt",
    "Trà", "Nuôi trồng nông & hải sản", "Bất động sản", "Đường", "Thiết bị văn phòng",
    "Cao su", "Thuốc trừ sâu", "Sô cô la, Bánh kẹo, bánh mỳ",
    "Hóa chất nông nghiệp Bán buôn", "Sản xuất bê tông", "Xe tải & Đóng tàu", "Khách sạn",
    "Truyền thông", "Thuốc lá", "Ô tô và phụ tùng", "Bao bì, đóng gói kim loại",
    "Công nghiệp nặng", "Điện tử & Thiết bị điện", "Sản xuất gạch ốp lát & Vật liệu lát",
    "Phần mềm", "Giầy dép", "Cảng hàng không", "Khai thác vàng", "Viễn thông",
    "Phần cứng", "Vận tải hành khách đường thủy", "Hàng điện & điện tử",
    "Vật liệu xây dựng khác", "Sản xuất và Khai thác dầu khí", "Sản xuất bia", "Cafe",
    "Máy công nghiệp", "Tiện ích Cộng đồng", "Du lịch và Giải trí",
    "Trái cây và rau quả chế biến", "Bao bì, đóng gói thủy tinh",
    "Kho bãi, hậu cần và bảo dưỡng", "Phân phối xăng dầu & khí đốt", "Tài nguyên Cơ bản",
    "Dụng cụ y tế", "Công ty du lịch", "Tư vấn & Hỗ trợ KD", "Vang & Rượu mạnh",
    "Sơn và chất phủ", "Thép và sản phẩm thép", "Dịch vụ Máy tính", "Khai khoáng",
    "Thiết bị, Dịch vụ và Phân phối Dầu khí", "Bảo hiểm", "Dịch vụ vận tải",
    "Bia và đồ uống", "Kim Loại màu", "Online", "Vận tải", "Viễn thông di động",
    "Chăm sóc y tế", "Vận tải hàng khô", "Giải trí & Truyền thông",
    "Dịch vụ cảng biển, cảng sông", "Thiết bị viễn thông", "Phân phối hàng chuyên dụng",
    "Tái bảo hiểm", "Thực phẩm và đồ uống", "Thực phẩm", "Bao bì, đóng gói từ giấy",
]


# ─────────────────────────────────────────────────────────────
# 📦 Structured Output Schema
# ─────────────────────────────────────────────────────────────

class SingleIntent(BaseModel):
    """Một intent đơn lẻ trong câu input của user."""

    intent_type: Literal[
        "stock_analysis",
        "market_index_analysis",
        "category_analysis",
        "general_question",
        "clarification",
        "out_of_scope"
    ] = Field(description=(
        "Loại intent:\n"
        "- stock_analysis: phân tích một mã cổ phiếu cụ thể\n"
        "- market_index_analysis: hỏi về chỉ số thị trường\n"
        "- category_analysis: hỏi về nhóm ngành / lĩnh vực\n"
        "- general_question: câu hỏi kiến thức, không cần dữ liệu thực\n"
        "- clarification: yêu cầu quá mơ hồ, cần hỏi lại\n"
        "- out_of_scope: ngoài phạm vi chứng khoán / tài chính"
    ))

    sub_query: str = Field(description=(
        "Câu hỏi con tương ứng với intent này, trích từ input gốc hoặc diễn đạt lại ngắn gọn. "
        "Ví dụ: 'VNM có nên mua không?', 'RSI là gì?'"
    ))

    symbol: str | None = Field(
        default=None,
        description="Mã cổ phiếu. Chỉ điền khi intent_type = 'stock_analysis'. Viết HOA."
    )

    market_index: Literal[
        "VNINDEX", "VN30", "VN100", "HNXIndex", "HNXUpcomIndex"
    ] | None = Field(
        default=None,
        description=(
            "Chỉ số thị trường. Chỉ điền khi intent_type = 'market_index_analysis'. "
            f"Chọn trong: {', '.join(MARKET_INDICES)}. Mặc định VNINDEX nếu không rõ."
        )
    )

    category: Literal[tuple(CATEGORIES)] | None = Field(  # type: ignore[valid-type]
        default=None,
        description=(
            "Nhóm ngành. Chỉ điền khi intent_type = 'category_analysis'. "
            "Chọn đúng tên trong danh sách CATEGORIES."
        )
    )


class IntentList(BaseModel):
    """Danh sách tất cả các intent được phân loại từ input của user."""
    intents: list[SingleIntent] = Field(
        description=(
            "Danh sách các intent được tách ra từ câu input. "
            "Mỗi ý/câu hỏi riêng biệt → một SingleIntent. "
            "Nếu chỉ có một ý → list có 1 phần tử."
        )
    )


# ─────────────────────────────────────────────────────────────
# 🧠 Prompt
# ─────────────────────────────────────────────────────────────

INTENT_CLASSIFIER_SYSTEM_PROMPT = f"""
Bạn là bộ phân loại ý định (intent classifier) cho chatbot phân tích chứng khoán Việt Nam.

Nhiệm vụ: Tách input của user thành danh sách các intent riêng biệt.
Mỗi ý / câu hỏi khác nhau → một SingleIntent.
Nếu chỉ có một ý → trả về list 1 phần tử.

────────────────────────
PHÂN LOẠI INTENT:

1. stock_analysis
   - Phân tích / gợi ý về một mã cổ phiếu cụ thể
   - VD: "VNM có nên mua không?", "Phân tích HPG giúp tôi"
   - Điền symbol (viết HOA)

2. market_index_analysis
   - Hỏi về chỉ số thị trường
   - VD: "VNINDEX hôm nay thế nào?", "Thị trường đang ra sao?"
   - Điền market_index, mặc định VNINDEX nếu không rõ

3. category_analysis
   - Hỏi về nhóm ngành / lĩnh vực
   - VD: "Nhóm ngân hàng đang thế nào?", "Cổ phiếu thép có triển vọng không?"
   - Điền category từ danh sách CATEGORIES

4. general_question
   - Câu hỏi kiến thức, không cần dữ liệu thực
   - VD: "RSI là gì?", "Cách đọc MACD?"

5. clarification
   - Quá mơ hồ, không xác định được đối tượng
   - VD: "Mua gì bây giờ?", "Cổ phiếu nào tốt?"

6. out_of_scope
   - Không liên quan đến chứng khoán / tài chính
   - VD: "Thời tiết hôm nay?", "Viết thơ cho tôi"

────────────────────────
VÍ DỤ TÁCH INTENT:

Input: "RSI là gì và VNM có nên mua không?"
→ intents: [
    {{intent_type: "general_question", sub_query: "RSI là gì?"}},
    {{intent_type: "stock_analysis",   sub_query: "VNM có nên mua không?", symbol: "VNM"}}
  ]

Input: "Phân tích FPT và ngành ngân hàng đang ra sao?"
→ intents: [
    {{intent_type: "stock_analysis",    sub_query: "Phân tích FPT", symbol: "FPT"}},
    {{intent_type: "category_analysis", sub_query: "Ngành ngân hàng đang ra sao?", category: "Ngân hàng"}}
  ]

Input: "VNM có nên mua không?"
→ intents: [
    {{intent_type: "stock_analysis", sub_query: "VNM có nên mua không?", symbol: "VNM"}}
  ]

────────────────────────
DANH SÁCH CATEGORIES:
{chr(10).join(f"- {c}" for c in CATEGORIES)}

────────────────────────
QUY TẮC:
- Mỗi intent chỉ điền trường tương ứng, còn lại = None
- sub_query bắt buộc có giá trị với mọi intent
- Trả lời bằng tiếng Việt
"""


# ─────────────────────────────────────────────────────────────
# 🚀 Intent Classifier Agent
# ─────────────────────────────────────────────────────────────

def intent_classifier_agent(state: AgentState) -> dict:
    print("[Intent Classifier] Phân loại input...")

    client = _get_openai_client()
    user_input = state.get("user_input", "")

    history = state.get("messages", [])
    history_messages = [
        {"role": "assistant" if isinstance(m, AIMessage) else "user", "content": m.content}
        for m in history
    ]

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": INTENT_CLASSIFIER_SYSTEM_PROMPT},
            *history_messages,
            {"role": "user", "content": user_input},
        ],
        response_format=IntentList,
    )

    result: IntentList = response.choices[0].message.parsed

    # Gắn thêm order để Reply Merger sắp xếp đúng thứ tự
    intents = [
        {**intent.model_dump(), "order": i}
        for i, intent in enumerate(result.intents)
    ]

    print(f"[Intent Classifier] Tìm thấy {len(intents)} intent(s):")
    for item in intents:
        print(f"  [{item['order']}] {item['intent_type']} — {item['sub_query']}")

    return {
        "intents": intents,
        "messages": [HumanMessage(content=user_input)],
    }