from state import AgentState
import time

def risk_appetite_agent(state: AgentState) -> AgentState:
    """Agent phân tích khẩu vị rủi ro"""
    
    # Fetch DB lấy ra khẩu vị rủi ro của user
    time.sleep(2)


    return {
        "risk_appetite": {
            "user_id": "USER_12345",
            "profile": {
                "age": 35,
                "occupation": "Kỹ sư phần mềm",
                "income_level": "trung bình khá",  # thấp, trung bình, trung bình khá, cao
                "investment_experience": "trung cấp",  # mới bắt đầu, trung cấp, có kinh nghiệm, chuyên nghiệp
                "investment_horizon": "dài hạn"  # ngắn hạn (<1 năm), trung hạn (1-5 năm), dài hạn (>5 năm)
            },
            "risk_tolerance": {
                "level": "moderate",  # conservative, moderate, aggressive, very_aggressive
                "score": 65,  # 0-100, càng cao càng chấp nhận rủi ro
                "max_acceptable_loss": 20,  # % tối đa có thể chấp nhận mất trong 1 năm
                "volatility_comfort": "medium"  # low, medium, high
            },
            "investment_goals": {
                "primary_goal": "tăng trưởng vốn",  # bảo toàn vốn, thu nhập thụ động, tăng trưởng vốn, đầu cơ
                "target_return": 15,  # % lợi nhuận mong muốn/năm
                "time_to_goal": 10,  # số năm để đạt mục tiêu
                "specific_goals": [
                    {
                        "name": "Mua nhà",
                        "target_amount": 3000000000,  # 3 tỷ VND
                        "deadline": "2030-12-31"
                    },
                    {
                        "name": "Quỹ hưu trí",
                        "target_amount": 10000000000,  # 10 tỷ VND
                        "deadline": "2050-12-31"
                    }
                ]
            },
            "portfolio_preferences": {
                "preferred_sectors": ["technology", "consumer_goods", "finance", "real_estate"],
                "avoided_sectors": ["tobacco", "gambling"],  # theo đạo đức/tôn giáo
                "diversification_preference": "medium",  # low (tập trung), medium, high (phân tán)
                "max_single_stock_allocation": 15,  # % tối đa cho 1 mã
                "cash_reserve_percentage": 10  # % tiền mặt giữ lại
            },
            "current_portfolio": {
                "total_value": 500000000,  # 500 triệu VND
                "stocks_percentage": 70,
                "bonds_percentage": 10,
                "cash_percentage": 20,
                "current_stocks": [
                    {"ticker": "VNM", "shares": 500, "avg_price": 85000},
                    {"ticker": "VIC", "shares": 200, "avg_price": 45000},
                    {"ticker": "HPG", "shares": 1000, "avg_price": 28000}
                ]
            },
            "behavioral_traits": {
                "loss_aversion": "medium",  # low, medium, high - sợ lỗ
                "regret_aversion": "high",  # sợ tiếc nuối khi bỏ lỡ cơ hội
                "overconfidence": "low",  # tự tin thái quá
                "herding_tendency": "medium",  # xu hướng đi theo đám đông
                "panic_selling_likelihood": "low"  # khả năng bán hoảng loạn khi thị trường giảm
            },
            "constraints": {
                "monthly_investment_budget": 10000000,  # 10 triệu VND/tháng
                "emergency_fund": 50000000,  # 50 triệu - quỹ dự phòng
                "debt_obligations": 5000000,  # 5 triệu/tháng - nợ cần trả
                "liquidity_needs": "medium",  # low, medium, high - nhu cầu thanh khoản
                "tax_considerations": True  # có quan tâm đến thuế không
            },
            "questionnaire_responses": {
                "q1_market_drop_reaction": "mua thêm",  # bán hết, bán bớt, giữ nguyên, mua thêm
                "q2_preferred_investment": "cổ phiếu tăng trưởng",  # tiết kiệm, trái phiếu, cổ phiếu blue-chip, cổ phiếu tăng trưởng
                "q3_sleep_loss_threshold": 15,  # % thua lỗ khiến mất ngủ
                "q4_recovery_time": "2-3 năm",  # thời gian chờ đợi để phục hồi
                "q5_knowledge_level": 7  # 1-10, tự đánh giá kiến thức về đầu tư
            },
            "updated_at": "2026-02-08T10:30:00Z",
            "created_at": "2025-01-15T08:00:00Z"
        },
        "completed_agents": ["risk_appetite_agent"]
    }