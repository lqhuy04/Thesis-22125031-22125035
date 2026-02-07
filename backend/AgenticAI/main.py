
from langgraph.graph import StateGraph, START, END
from state import AgentState
from agents import FundamentalAnalysis, TechnicalAnalysis, News, RiskAppetite, Summary


def create_workflow():
    # Khởi tạo graph
    workflow = StateGraph(AgentState)

    # Thêm các agent nodes
    workflow.add_node("fundamental_analysis", FundamentalAnalysis.fundamental_analysis_agent)
    workflow.add_node("technical_analysis", TechnicalAnalysis.technical_analysis_agent)
    workflow.add_node("news_analysis", News.news_analysis_agent)
    workflow.add_node("risk_appetite_analysis", RiskAppetite.risk_appetite_agent)
    workflow.add_node("summary", Summary.summary_agent)

    # Định nghĩa luồng
    workflow.add_edge(START, "fundamental_analysis")
    workflow.add_edge(START, "technical_analysis")
    workflow.add_edge(START, "news_analysis")
    workflow.add_edge(START, "risk_appetite_analysis")

    workflow.add_edge("fundamental_analysis", "summary")
    workflow.add_edge("technical_analysis", "summary")
    workflow.add_edge("news_analysis", "summary")
    workflow.add_edge("risk_appetite_analysis", "summary")

    workflow.add_edge("summary", END)

    return workflow.compile()


def run():
    app = create_workflow()
    
    # Initial state
    initial_state = {}
    
    # Chạy
    result = app.invoke(initial_state)
    print(app.get_graph().draw_ascii())

if __name__ == "__main__":
    run()

