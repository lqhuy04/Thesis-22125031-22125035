import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

# 1. Setup Environment & Model
load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GEMINI_API_KEY"))

# 2. Define the Agent State
class AgentState(TypedDict):
    raw_data: dict
    fundamental_analysis: str
    technical_analysis: str
    final_report: str
    revision_count: int

# 3. Define the Nodes (The Agent's "Steps")
def analyzer_node(state: AgentState):
    """Phân tích dữ liệu tài chính cơ bản (Fundamental Analysis)."""
    data = state['raw_data']
    prompt = f"""Phân tích các chỉ số tài chính cơ bản cho cổ phiếu {data['symbol']}:
    {data['metrics']}
    
    Hãy đánh giá:
    - Định giá (P/E, P/B, EV/EBITDA)
    - Khả năng sinh lời (ROE, ROA, các margin)
    - Tăng trưởng (revenue YoY, EPS YoY)
    - Tình hình tài chính (debt to equity, current ratio)
    - Dòng tiền tự do (FCF)
    
    Đưa ra nhận định tổng quan về sức khỏe tài chính của công ty."""
    response = llm.invoke(prompt)
    return {"fundamental_analysis": response.content}

def technical_analyzer_node(state: AgentState):
    """Phân tích kỹ thuật (Technical Analysis) dựa trên dữ liệu giá."""
    data = state['raw_data']
    prompt = f"""Phân tích kỹ thuật cho cổ phiếu {data['symbol']} dựa trên dữ liệu giá gần đây:
    {data['price_data']}
    
    Hãy phân tích:
    - Xu hướng giá (trend) trong giai đoạn này
    - Mức hỗ trợ và kháng cự
    - Khối lượng giao dịch và thanh khoản
    - Biên độ dao động giá
    - Các tín hiệu mua/bán tiềm năng
    
    Đưa ra nhận định về xu hướng ngắn hạn và trung hạn."""
    response = llm.invoke(prompt)
    return {"technical_analysis": response.content}

def final_report_node(state: AgentState):
    """Tổng hợp báo cáo hoàn chỉnh từ phân tích cơ bản và kỹ thuật."""
    data = state['raw_data']
    prompt = f"""Dựa trên hai phân tích sau đây cho cổ phiếu {data['symbol']}, hãy tổng hợp thành một báo cáo đầu tư hoàn chỉnh:

    PHÂN TÍCH CƠ BẢN:
    {state['fundamental_analysis']}
    
    PHÂN TÍCH KỸ THUẬT:
    {state['technical_analysis']}
    
    Hãy:
    1. Tóm tắt các điểm mạnh và điểm yếu chính
    2. Đánh giá rủi ro và cơ hội
    3. Đưa ra khuyến nghị đầu tư (Mua/Giữ/Bán) với lý do rõ ràng
    4. Đề xuất mức giá mục tiêu (nếu có thể)
    5. Các lưu ý quan trọng cho nhà đầu tư
    
    Định dạng báo cáo chuyên nghiệp, rõ ràng và dễ hiểu."""
    response = llm.invoke(prompt)
    report = f"### BÁO CÁO PHÂN TÍCH CỔ PHIẾU {data['symbol']}\n\n{response.content}"
    return {"final_report": report}

# 4. Build the Graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("fundamental_analysis", analyzer_node)
workflow.add_node("technical_analysis", technical_analyzer_node)
workflow.add_node("final_report", final_report_node)

# Set the flow - both analyses run in parallel, then combine in final report
workflow.set_entry_point("fundamental_analysis")
workflow.add_edge("fundamental_analysis", "technical_analysis")
workflow.add_edge("technical_analysis", "final_report")
workflow.add_edge("final_report", END)

# Compile the graph
app = workflow.compile()

input_data = {
    "raw_data": {
        "symbol": "VNM",
        "total_records": 15,
        "metrics": [
            {
                "pe_ratio": 14.54,
                "pb_ratio": 3.38,
                "eps": 4022.0,
                "market_cap_billion": 122239.4,
                "shares_outstanding_million": 2089.96,
                "roe": 25.96,
                "gross_margin": 41.42,
                "net_margin": None,
                "roa": None,
                "revenue_yoy": 2.34,
                "eps_yoy": 5.95,
                "profit_yoy": None,
                "debt_to_equity": 0.52,
                "current_ratio": 2.03,
                "ev_ebitda": 11.11,
                "bvps": None,
                "fcf": 5946.85,
                "beta": None
            }
        ],
        "price_data": [
            {
                "TradingDate": "29/12/2025",
                "Time": None,
                "Open": "61500",
                "High": "62200",
                "Low": "61400",
                "Close": "62100",
                "Volume": "1943000",
                "Value": "120157180000"
            },
            {
                "TradingDate": "30/12/2025",
                "Time": None,
                "Open": "62100",
                "High": "62300",
                "Low": "61700",
                "Close": "61800",
                "Volume": "1581000",
                "Value": "97858410000"
            },
            {
                "TradingDate": "31/12/2025",
                "Time": None,
                "Open": "61900",
                "High": "62000",
                "Low": "61200",
                "Close": "61200",
                "Volume": "1879600",
                "Value": "115569960000"
            },
            {
                "TradingDate": "05/01/2026",
                "Time": None,
                "Open": "61300",
                "High": "61500",
                "Low": "60000",
                "Close": "60300",
                "Volume": "2814700",
                "Value": "170865710000"
            },
            {
                "TradingDate": "06/01/2026",
                "Time": None,
                "Open": "60500",
                "High": "60900",
                "Low": "60300",
                "Close": "60800",
                "Volume": "2963300",
                "Value": "179693170000"
            },
            {
                "TradingDate": "07/01/2026",
                "Time": None,
                "Open": "60800",
                "High": "61500",
                "Low": "60500",
                "Close": "60900",
                "Volume": "3228100",
                "Value": "196941770000"
            },
            {
                "TradingDate": "08/01/2026",
                "Time": None,
                "Open": "61100",
                "High": "63400",
                "Low": "61100",
                "Close": "62200",
                "Volume": "5636400",
                "Value": "351659430000"
            },
            {
                "TradingDate": "09/01/2026",
                "Time": None,
                "Open": "62400",
                "High": "62500",
                "Low": "61000",
                "Close": "61000",
                "Volume": "4184100",
                "Value": "258465510000"
            },
            {
                "TradingDate": "12/01/2026",
                "Time": None,
                "Open": "61100",
                "High": "62700",
                "Low": "61100",
                "Close": "62700",
                "Volume": "4146300",
                "Value": "257857700000"
            },
            {
                "TradingDate": "13/01/2026",
                "Time": None,
                "Open": "62900",
                "High": "64900",
                "Low": "62800",
                "Close": "63300",
                "Volume": "6761300",
                "Value": "430840390000"
            },
            {
                "TradingDate": "14/01/2026",
                "Time": None,
                "Open": "63600",
                "High": "67700",
                "Low": "63400",
                "Close": "67700",
                "Volume": "24838300",
                "Value": "1662222120000"
            },
            {
                "TradingDate": "15/01/2026",
                "Time": None,
                "Open": "70000",
                "High": "72400",
                "Low": "69500",
                "Close": "71000",
                "Volume": "19260600",
                "Value": "1377961380000"
            },
            {
                "TradingDate": "16/01/2026",
                "Time": None,
                "Open": "71100",
                "High": "73000",
                "Low": "69100",
                "Close": "69600",
                "Volume": "13372500",
                "Value": "944442320000"
            },
            {
                "TradingDate": "19/01/2026",
                "Time": None,
                "Open": "69800",
                "High": "71000",
                "Low": "68300",
                "Close": "70600",
                "Volume": "10385300",
                "Value": "722125070000"
            },
            {
                "TradingDate": "20/01/2026",
                "Time": None,
                "Open": "71500",
                "High": "75500",
                "Low": "71100",
                "Close": "73400",
                "Volume": "21521900",
                "Value": "1596348490000"
            },
            {
                "TradingDate": "21/01/2026",
                "Time": None,
                "Open": "73000",
                "High": "73000",
                "Low": "70000",
                "Close": "70300",
                "Volume": "11234100",
                "Value": "800042790000"
            },
            {
                "TradingDate": "22/01/2026",
                "Time": None,
                "Open": "71100",
                "High": "72800",
                "Low": "70000",
                "Close": "70900",
                "Volume": "8055200",
                "Value": "573373780000"
            },
            {
                "TradingDate": "23/01/2026",
                "Time": None,
                "Open": "69400",
                "High": "70100",
                "Low": "67200",
                "Close": "67200",
                "Volume": "16050400",
                "Value": "1097314610000"
            },
            {
                "TradingDate": "26/01/2026",
                "Time": None,
                "Open": "67400",
                "High": "69300",
                "Low": "67400",
                "Close": "68900",
                "Volume": "8864800",
                "Value": "607858160000"
            },
            {
                "TradingDate": "27/01/2026",
                "Time": None,
                "Open": "68400",
                "High": "68600",
                "Low": "66100",
                "Close": "67700",
                "Volume": "8357800",
                "Value": "562221360000"
            },
            {
                "TradingDate": "28/01/2026",
                "Time": None,
                "Open": "67700",
                "High": "69500",
                "Low": "67200",
                "Close": "68000",
                "Volume": "6303300",
                "Value": "429824490000"
            }
        ]
    },
    "revision_count": 0
}

result = app.invoke(input_data)
print(result["final_report"])