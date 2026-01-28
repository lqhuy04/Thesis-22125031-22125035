"""
Agentic AI Service for stock analysis
Integrates fundamental and technical analysis using LangGraph
"""
import os
from typing import TypedDict, Dict, Any
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

# Load environment variables
load_dotenv()

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=os.getenv("GEMINI_API_KEY")
)


# Define Agent State
class AgentState(TypedDict):
    raw_data: dict
    fundamental_analysis: str
    technical_analysis: str
    final_report: str
    revision_count: int


# Node: Start Node (để trigger parallel execution)
def start_node(state: AgentState):
    """Node khởi đầu để trigger parallel analysis."""
    return {}


# Node: Fundamental Analysis
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


# Node: Technical Analysis
def technical_analyzer_node(state: AgentState):
    """Phân tích kỹ thuật (Technical Analysis) dựa trên dữ liệu giá."""
    data = state['raw_data']
    
    # Only analyze if price_data is available
    if not data.get('price_data'):
        return {"technical_analysis": "Không có dữ liệu giá để phân tích kỹ thuật."}
    
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


# Node: Final Report
def final_report_node(state: AgentState):
    """Tổng hợp báo cáo ngắn gọn từ phân tích cơ bản và kỹ thuật."""
    data = state['raw_data']
    prompt = f"""Dựa trên hai phân tích sau đây cho cổ phiếu {data['symbol']}, hãy tổng hợp thành một đoạn văn ngắn gọn (khoảng 150-200 từ):

    PHÂN TÍCH CƠ BẢN:
    {state['fundamental_analysis']}
    
    PHÂN TÍCH KỸ THUẬT:
    {state['technical_analysis']}
    
    Hãy viết một đoạn văn ngắn gọn bao gồm:
    1. Đánh giá tổng quan về cổ phiếu
    2. Khuyến nghị đầu tư (Mua/Giữ/Bán) với lý do chính
    3. Mức giá mục tiêu (nếu có)
    
    LƯU Ý: Chỉ viết một đoạn văn ngắn, súc tích, dễ hiểu. KHÔNG viết dài dòng."""
    response = llm.invoke(prompt)
    return {"final_report": response.content}


# Build the workflow graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("start", start_node)
workflow.add_node("fundamental_analysis", analyzer_node)
workflow.add_node("technical_analysis", technical_analyzer_node)
workflow.add_node("final_report", final_report_node)

# Set the flow - Parallel execution
# Start node triggers both fundamental and technical analysis in parallel
workflow.set_entry_point("start")
workflow.add_edge("start", "fundamental_analysis")
workflow.add_edge("start", "technical_analysis")

# Both fundamental and technical must complete before final report
workflow.add_edge("fundamental_analysis", "final_report")
workflow.add_edge("technical_analysis", "final_report")

workflow.add_edge("final_report", END)

# Compile the graph
app = workflow.compile()


class AgenticAIService:
    """Service for AI-powered stock analysis"""
    
    @staticmethod
    async def analyze_stock(symbol: str, metrics: list, price_data: list = None) -> Dict[str, Any]:
        """
        Analyze stock using agentic AI
        
        Args:
            symbol: Stock symbol
            metrics: List of financial metrics
            price_data: Optional list of price data for technical analysis
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Prepare input data
            input_data = {
                "raw_data": {
                    "symbol": symbol,
                    "metrics": metrics,
                    "price_data": price_data or []
                },
                "revision_count": 0
            }
            
            # Run the agentic AI workflow
            result = app.invoke(input_data)
            
            return {
                "symbol": symbol,
                "fundamental_analysis": result.get("fundamental_analysis", ""),
                "technical_analysis": result.get("technical_analysis", ""),
                "final_report": result.get("final_report", ""),
                "analysis_timestamp": None  # You can add timestamp if needed
            }
            
        except Exception as e:
            raise Exception(f"Error in agentic AI analysis: {str(e)}")
