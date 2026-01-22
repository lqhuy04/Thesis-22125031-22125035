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
    analysis: str
    revision_count: int

# 3. Define the Nodes (The Agent's "Steps")
def analyzer_node(state: AgentState):
    """Phân tích dữ liệu tài chính."""
    data = state['raw_data']
    prompt = f"Phân tích các chỉ số tài chính này cho mã {data['data']['data']['symbol']}: {data['data']['data']['metrics'][:5]}"
    response = llm.invoke(prompt)
    return {"analysis": response.content}

def final_report_node(state: AgentState):
    """Định dạng lại báo cáo thành bản tóm tắt chuyên nghiệp."""
    report = f"### BÁO CÁO PHÂN TÍCH CỔ PHIẾU\n{state['analysis']}"
    return {"analysis": report}

# 4. Build the Graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("analyze", analyzer_node)
workflow.add_node("format_report", final_report_node)

# Set the flow
workflow.set_entry_point("analyze")
workflow.add_edge("analyze", "format_report")
workflow.add_edge("format_report", END)

# Compile the graph
app = workflow.compile()

input_data = {
    "raw_data": {
        "data": {
    "data": {
        "symbol": "VNM",
        "total_records": 15,
        "metrics": [
            {
                "id": "d08621b3-31fb-43c1-a30c-83449f7a1aab",
                "symbol": "VNM",
                "company_name": "CTCP SUA VIET NAM",
                "year": "2024",
                "pe_ratio": 14.54,
                "pb_ratio": 3.38,
                "eps": 4022.0,
                "market_cap": 122239.4,
                "shares_outstanding": 2089.96,
                "roe": 25.96,
                "gross_margin": 41.42,
                "revenue_yoy": 2.34,
                "eps_yoy": 5.95,
                "debt_to_equity": 0.52,
                "current_ratio": 2.03,
                "fcf": 5946.85,
                "ev_ebitda": 11.11,
                "beta": 'null',
                "data_source": "SSI iBoard",
                "created_at": "2026-01-22T05:10:36.095939+00:00",
                "updated_at": "2026-01-22T05:10:36.095939+00:00"
            },
            {
                "id": "eec4f016-b000-496c-86dc-8333085ca002",
                "symbol": "VNM",
                "company_name": "CTCP SUA VIET NAM",
                "year": "2023",
                "pe_ratio": 15.55,
                "pb_ratio": 3.52,
                "eps": 3796.0,
                "market_cap": 123374.25,
                "shares_outstanding": 2089.96,
                "roe": 25.34,
                "gross_margin": 40.66,
                "revenue_yoy": 0.69,
                "eps_yoy": 4.52,
                "debt_to_equity": 0.5,
                "current_ratio": 2.1,
                "fcf": 4898.87,
                "ev_ebitda": 11.68,
                "beta": 'null',
                "data_source": "SSI iBoard",
                "created_at": "2026-01-22T05:10:36.095939+00:00",
                "updated_at": "2026-01-22T05:10:36.095939+00:00"
            },
            {
                "id": "58d329c8-51ec-4991-b51b-12bbf2e23d43",
                "symbol": "VNM",
                "company_name": "CTCP SUA VIET NAM",
                "year": "2022",
                "pe_ratio": 17.58,
                "pb_ratio": 4.07,
                "eps": 3632.0,
                "market_cap": 133420.67,
                "shares_outstanding": 2089.96,
                "roe": 25.95,
                "gross_margin": 39.86,
                "revenue_yoy": -1.58,
                "eps_yoy": -19.59,
                "debt_to_equity": 0.48,
                "current_ratio": 2.06,
                "fcf": 12300.04,
                "ev_ebitda": 12.39,
                "beta": 'null',
                "data_source": "SSI iBoard",
                "created_at": "2026-01-22T05:10:36.095939+00:00",
                "updated_at": "2026-01-22T05:10:36.095939+00:00"
            },
            {
                "id": "ae257170-44dd-484b-b45f-c46079af105b",
                "symbol": "VNM",
                "company_name": "CTCP SUA VIET NAM",
                "year": "2021",
                "pe_ratio": 14.99,
                "pb_ratio": 3.95,
                "eps": 4517.0,
                "market_cap": 141469.08,
                "shares_outstanding": 2089.96,
                "roe": 29.38,
                "gross_margin": 43.14,
                "revenue_yoy": 2.15,
                "eps_yoy": -5.3,
                "debt_to_equity": 0.49,
                "current_ratio": 2.12,
                "fcf": 5498.72,
                "ev_ebitda": 11.28,
                "beta": 'null',
                "data_source": "SSI iBoard",
                "created_at": "2026-01-22T05:10:36.095939+00:00",
                "updated_at": "2026-01-22T05:10:36.095939+00:00"
            },
            {
                "id": "8c0db07a-7730-41ef-bae2-0a9688c135bb",
                "symbol": "VNM",
                "company_name": "CTCP SUA VIET NAM",
                "year": "2020",
                "pe_ratio": 17.19,
                "pb_ratio": 5.09,
                "eps": 4770.0,
                "market_cap": 171390.98,
                "shares_outstanding": 2089.96,
                "roe": 32.99,
                "gross_margin": 46.4,
                "revenue_yoy": 5.89,
                "eps_yoy": -12.92,
                "debt_to_equity": 0.44,
                "current_ratio": 2.09,
                "fcf": 5378.16,
                "ev_ebitda": 12.72,
                "beta": 'null',
                "data_source": "SSI iBoard",
                "created_at": "2026-01-22T05:10:36.095939+00:00",
                "updated_at": "2026-01-22T05:10:36.095939+00:00"
            },
            {
                "id": "c629d2ca-4c4c-4f61-bd04-0571c8f7c5db",
                "symbol": "VNM",
                "company_name": "CTCP SUA VIET NAM",
                "year": "2019",
                "pe_ratio": 12.98,
                "pb_ratio": 5.0,
                "eps": 5478.0,
                "market_cap": 148600.01,
                "shares_outstanding": 2089.96,
                "roe": 35.59,
                "gross_margin": 47.18,
                "revenue_yoy": 7.15,
                "eps_yoy": 3.46,
                "debt_to_equity": 0.5,
                "current_ratio": 1.71,
                "fcf": 4662.06,
                "ev_ebitda": 11.39,
                "beta": 'null',
                "data_source": "SSI iBoard",
                "created_at": "2026-01-22T05:10:36.095939+00:00",
                "updated_at": "2026-01-22T05:10:36.095939+00:00"
            },
            {
                "id": "177b4c8b-7885-4043-ad56-b37bd9eb2c5e",
                "symbol": "VNM",
                "company_name": "CTCP SUA VIET NAM",
                "year": "2018",
                "pe_ratio": 13.33,
                "pb_ratio": 5.62,
                "eps": 5295.0,
                "market_cap": 147527.86,
                "shares_outstanding": 2089.96,
                "roe": 38.93,
                "gross_margin": 46.82,
                "revenue_yoy": 2.98,
                "eps_yoy": -16.68,
                "debt_to_equity": 0.42,
                "current_ratio": 1.93,
                "fcf": 7095.1,
                "ev_ebitda": 12.24,
                "beta": 'null',
                "data_source": "SSI iBoard",
                "created_at": "2026-01-22T05:10:36.095939+00:00",
                "updated_at": "2026-01-22T05:10:36.095939+00:00"
            },
            {
                "id": "72fab3a3-f417-475c-a135-06dd24b8db0d",
                "symbol": "VNM",
                "company_name": "CTCP SUA VIET NAM",
                "year": "2017",
                "pe_ratio": 15.62,
                "pb_ratio": 8.69,
                "eps": 6355.0,
                "market_cap": 207474.06,
                "shares_outstanding": 2089.96,
                "roe": 43.13,
                "gross_margin": 47.48,
                "revenue_yoy": 9.08,
                "eps_yoy": 8.99,
                "debt_to_equity": 0.45,
                "current_ratio": 1.99,
                "fcf": 7830.6,
                "ev_ebitda": 17.07,
                "beta": 'null',
                "data_source": "SSI iBoard",
                "created_at": "2026-01-22T05:10:36.095939+00:00",
                "updated_at": "2026-01-22T05:10:36.095939+00:00"
            },
            {
                "id": "62a5e5c5-ca0b-4807-9ee7-ea40dd4385f6",
                "symbol": "VNM",
                "company_name": "CTCP SUA VIET NAM",
                "year": "2016",
                "pe_ratio": 9.91,
                "pb_ratio": 5.39,
                "eps": 5831.0,
                "market_cap": 120720.01,
                "shares_outstanding": 2089.96,
                "roe": 41.73,
                "gross_margin": 47.73,
                "revenue_yoy": 16.75,
                "eps_yoy": -0.1,
                "debt_to_equity": 0.31,
                "current_ratio": 2.89,
                "fcf": 6443.99,
                "ev_ebitda": 10.84,
                "beta": 'null',
                "data_source": "SSI iBoard",
                "created_at": "2026-01-22T05:10:36.095939+00:00",
                "updated_at": "2026-01-22T05:10:36.095939+00:00"
            },
            {
                "id": "c22e63aa-4c7e-4009-9746-43ede151da0d",
                "symbol": "VNM",
                "company_name": "CTCP SUA VIET NAM",
                "year": "2015",
                "pe_ratio": 8.09,
                "pb_ratio": 4.72,
                "eps": 5837.0,
                "market_cap": 98746.21,
                "shares_outstanding": 2089.96,
                "roe": 37.15,
                "gross_margin": 40.57,
                "revenue_yoy": 14.28,
                "eps_yoy": 28.12,
                "debt_to_equity": 0.31,
                "current_ratio": 2.79,
                "fcf": 5532.47,
                "ev_ebitda": 10.53,
                "beta": 'null',
                "data_source": "SSI iBoard",
                "created_at": "2026-01-22T05:10:36.095939+00:00",
                "updated_at": "2026-01-22T05:10:36.095939+00:00"
            },
            {
                "id": "792c9d6b-471d-4150-924e-2327d035dfea",
                "symbol": "VNM",
                "company_name": "CTCP SUA VIET NAM",
                "year": "2014",
                "pe_ratio": 6.11,
                "pb_ratio": 2.96,
                "eps": 4556.0,
                "market_cap": 58196.9,
                "shares_outstanding": 2089.96,
                "roe": 30.84,
                "gross_margin": 32.48,
                "revenue_yoy": 13.32,
                "eps_yoy": -41.88,
                "debt_to_equity": 0.3,
                "current_ratio": 2.83,
                "fcf": 1455.6,
                "ev_ebitda": 7.88,
                "beta": 'null',
                "data_source": "SSI iBoard",
                "created_at": "2026-01-22T05:10:36.095939+00:00",
                "updated_at": "2026-01-22T05:10:36.095939+00:00"
            },
            {
                "id": "e6eb2f2c-77ad-4a95-ae72-e4dfef28219a",
                "symbol": "VNM",
                "company_name": "CTCP SUA VIET NAM",
                "year": "2013",
                "pe_ratio": 4.06,
                "pb_ratio": 3.79,
                "eps": 7839.0,
                "market_cap": 66468.94,
                "shares_outstanding": 2089.96,
                "roe": 37.24,
                "gross_margin": 36.13,
                "revenue_yoy": 16.52,
                "eps_yoy": 12.29,
                "debt_to_equity": 0.3,
                "current_ratio": 2.63,
                "fcf": 4661.95,
                "ev_ebitda": 8.54,
                "beta": 'null',
                "data_source": "SSI iBoard",
                "created_at": "2026-01-22T05:10:36.095939+00:00",
                "updated_at": "2026-01-22T05:10:36.095939+00:00"
            },
            {
                "id": "1cdbe124-bf97-4ebc-bae2-778a5f6f50a5",
                "symbol": "VNM",
                "company_name": "CTCP SUA VIET NAM",
                "year": "2012",
                "pe_ratio": 2.88,
                "pb_ratio": 2.71,
                "eps": 6981.0,
                "market_cap": 41955.86,
                "shares_outstanding": 2089.96,
                "roe": 37.56,
                "gross_margin": 34.17,
                "revenue_yoy": 22.81,
                "eps_yoy": -9.54,
                "debt_to_equity": 0.27,
                "current_ratio": 2.68,
                "fcf": 320.91,
                "ev_ebitda": 6.66,
                "beta": 'null',
                "data_source": "SSI iBoard",
                "created_at": "2026-01-22T05:10:36.095939+00:00",
                "updated_at": "2026-01-22T05:10:36.095939+00:00"
            },
            {
                "id": "faef8b17-5f4e-469a-8a38-901c2ee61b29",
                "symbol": "VNM",
                "company_name": "CTCP SUA VIET NAM",
                "year": "2011",
                "pe_ratio": 1.64,
                "pb_ratio": 2.12,
                "eps": 7717.0,
                "market_cap": 26423.31,
                "shares_outstanding": 2089.96,
                "roe": 33.81,
                "gross_margin": 30.46,
                "revenue_yoy": 37.29,
                "eps_yoy": 12.92,
                "debt_to_equity": 0.25,
                "current_ratio": 3.21,
                "fcf": 2417.18,
                "ev_ebitda": 5.57,
                "beta": 'null',
                "data_source": "SSI iBoard",
                "created_at": "2026-01-22T05:10:36.095939+00:00",
                "updated_at": "2026-01-22T05:10:36.095939+00:00"
            },
            {
                "id": "2f0b1fb8-6c6b-4078-978c-9d9b4bebd209",
                "symbol": "VNM",
                "company_name": "CTCP SUA VIET NAM",
                "year": "2010",
                "pe_ratio": 1.21,
                "pb_ratio": 2.17,
                "eps": 6834.0,
                "market_cap": 17250.49,
                "shares_outstanding": 2089.96,
                "roe": 45.4,
                "gross_margin": 32.84,
                "revenue_yoy": 'null',
                "eps_yoy": 'null',
                "debt_to_equity": 0.35,
                "current_ratio": 2.24,
                "fcf": 1375.72,
                "ev_ebitda": 5.35,
                "beta": 'null',
                "data_source": "SSI iBoard",
                "created_at": "2026-01-22T05:10:36.095939+00:00",
                "updated_at": "2026-01-22T05:10:36.095939+00:00"
            }
        ]
    },
    "errorCode": 0,
    "errorDesc": "",
    "requestId": "759fd190-3a7e-4f95-b0b5-ccb1f892dc5e",
    "result": 'true'
}

    },
    "revision_count": 0
}

result = app.invoke(input_data)
print(result["analysis"])