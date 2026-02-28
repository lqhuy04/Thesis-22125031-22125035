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

mock_price_data = [
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

mock_news_data = [
    {
        "title": 'Doanh thu năm 2025 của Vinamilk (VNM) đạt 63.724 tỷ đồng, cao nhất lịch sử Công ty',
        "content": '''
                        Đẩy mạnh các hoạt động xúc tiến thương mại giúp Vinamilk nâng cao hình ảnh và vị thế thương hiệu trên thị trường quốc tế. Ảnh: Vi Nam
            (ĐTCK)Tổng doanh thu hợp nhất quý IV/2025 của Công ty cổ phần Sữa Việt Nam (Vinamilk - mã VNM) đạt 17.045 tỷ đồng, tiếp tục lập đỉnh mới, tăng 10,1% so với cùng kỳ.
            Kết quả này giúp tổng doanh thu hợp nhất năm 2025 của Vinamilk đạt 63.724 tỷ đồng, tăng 3,1% so với cùng kỳ, cao nhất lịch sử Công ty.
            Hoạt động kinh doanh quốc tế tiếp tục đóng vai trò là nhân tố chủ đạo thúc đẩy tăng trưởng, trong khi kinh doanh nội địa đã dần phục hồi và lấy lại đà phát triển. Doanh thu thuần hợp nhất trong nước của Vinamilk tăng 7,8% so với cùng kỳ, đạt 13.846 tỷ đồng. Lũy kế cả năm đạt 50.964 tỷ đồng.
            Thị trường trong nước đóng góp 81,3% doanh thu thuần hợp nhất quý IV, trở lại đà tăng trưởng. Trong khi đó, ở mảng kinh doanh quốc tế, doanh thu thuần hợp nhất nước ngoài tăng 21% so với cùng kỳ và đạt 3.188 tỷ đồng. Lũy kế cả năm đạt 12.682 tỷ đồng, tăng 15,5% so với năm trước.
            Xuất khẩu vẫn là động lực tăng trưởng chính, với doanh thu thuần quý IV đạt 1.579 tỷ đồng, tăng 26% so với cùng kỳ, xác lập chuỗi tăng trưởng dương 10 quý liên tiếp. Trong năm 2025, xuất khẩu đạt 7.105 tỷ đồng, tăng 25,4% so với 2024. Lũy kế qua các năm, Vinamilk đã xuất khẩu đến 65 thị trường trên thế giới và đạt được 3,7 tỷ đô. Tăng trưởng của Vinamilk tại các thị trường xuất khẩu nhờ đẩy mạnh đổi mới sản phẩm, công nghệ và mô hình tiếp cận người tiêu dùng.
            Danh mục sản phẩm xuất khẩu được phát triển theo hướng linh hoạt, tinh chỉnh phù hợp với đặc thù từng thị trường, đồng thời gia tăng tỷ trọng các sản phẩm có giá trị cao. Song song đó là đẩy mạnh xúc tiến thương mại, nâng cao hình ảnh và vị thế thương hiệu của Vinamilk trên thị trường quốc tế. Biên lợi nhuận gộp hợp nhất quý IV/2025 tăng 30 điểm cơ bản so với cùng kỳ, ở mức 40,4%, chủ yếu nhờ quy mô doanh thu mở rộng và giá nguyên liệu đầu vào duy trì ổn định.
            Lũy kế năm 2025, biên lợi nhuận gộp hợp nhất của Vinamilk đạt 41,2%, chỉ thấp hơn 20 điểm cơ bản so với cùng kỳ năm trước, chủ yếu do tác động của quý I. Hiệu quả vận hành tiếp tục được nâng cao, góp phần tích cực vào kết quả kinh doanh của quý IV/2025.
            Doanh thu hợp nhất ghi nhận mức tăng trưởng 10,1% so với cùng kỳ năm trước, trong khi chi phí bán hàng giảm 4,9%. Lợi nhuận trước thuế (LNTT) hợp nhất và lợi nhuận sau thuế (LNST) hợp nhất quý IV của Vinamilk lần lượt đạt 3.477 tỷ đồng và 2.827 tỷ đồng, tăng 31,5% và 31,7% so với cùng kỳ.
            Lũy kế năm 2025, LNTT hợp nhất đạt 11.650 tỷ đồng, tăng trưởng nhẹ so với cùng kỳ. LNST hợp nhất năm 2025 đạt 9.414 tỷ đồng, giảm nhẹ so với năm 2024 do tác động từ quý I, tuy nhiên mức giảm này đã được thu hẹp đáng kể nhờ kết quả tích cực của các quý tiếp theo. Thu nhập mỗi cổ phần (EPS) năm 2025 đạt 4.028 đồng
            Trên thị trường chứng khoán, phiên giao dịch ngày 2/2, cổ phiếu VNM tăng hơn 2%, lên 72.300 đồng, thanh khoản hơn 9 triệu đơn vị.
        ''',
        "date": "2025-02-03"
    }
]

def run():
    app = create_workflow()
    
    # Initial state
    initial_state = {
        "symbol": "VNM",
        "company_name": "Công ty cổ phần Sữa Việt Nam",
        "price_data": mock_price_data,
        "news_data": mock_news_data,
    }
    
    # Chạy
    result = app.invoke(initial_state)
    # print(app.get_graph().draw_ascii())
    print('Kết quả', result)

if __name__ == "__main__":
    run()

