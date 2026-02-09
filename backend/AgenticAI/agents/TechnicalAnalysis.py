from backend.AgenticAI.agents.service.gemini import generate_content
from state import AgentState

mock_data = [
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
            

def technical_analysis_agent(state: AgentState) -> AgentState:
    """Agent phân tích kĩ thuật"""
    
    print("Agent phân tích kĩ thuật - START")
    print("Agent phân tích kĩ thuật - RUNNING")

    prompt = f"""Phân tích kỹ thuật cho cổ phiếu {state['symbol']} dựa trên dữ liệu giá gần đây:
    {mock_data}
    
    Hãy phân tích:
    - Xu hướng giá (trend) trong giai đoạn này
    - Mức hỗ trợ và kháng cự
    - Khối lượng giao dịch và thanh khoản
    - Biên độ dao động giá
    - Các tín hiệu mua/bán tiềm năng
    
    Đưa ra nhận định về xu hướng ngắn hạn và trung hạn."""

    result = generate_content(prompt);

    print("Agent phân tích kĩ thuật - END")
    
    return {
        "technical_analysis": result,
        "completed_agents": ["technical_analysis_agent"]
    }
