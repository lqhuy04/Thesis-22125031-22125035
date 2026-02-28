"""
Agentic AI Service for stock analysis
Uses the AgenticAI workflow (agents: Fundamental, Technical, News, RiskAppetite, Summary)
"""
import sys
import os
import importlib.util
from typing import Dict, Any

# Add AgenticAI directory to sys.path so its internal imports work
_agentic_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'AgenticAI'))
if _agentic_dir not in sys.path:
    sys.path.insert(0, _agentic_dir)

# Import create_workflow via importlib to avoid name conflict with app.main
_spec = importlib.util.spec_from_file_location("agentic_ai_main", os.path.join(_agentic_dir, "main.py"))
_agentic_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_agentic_module)

create_workflow = _agentic_module.create_workflow

# Compile the workflow once at module level
workflow_app = create_workflow()


class AgenticAIService:
    """Service for AI-powered stock analysis using AgenticAI workflow"""

    @staticmethod
    async def analyze_stock(
        symbol: str,
        company_name: str = "",
        price_data: list = None,
        news_data: list = None,
        user_profile: dict = None,
    ) -> Dict[str, Any]:
        """
        Run the full AgenticAI workflow (Fundamental, Technical, News, RiskAppetite → Summary).

        Args:
            symbol: Stock symbol (e.g. VNM)
            company_name: Full company name
            price_data: List of price records for technical analysis
            news_data: List of news articles for sentiment analysis
            user_profile: User risk-appetite profile dict

        Returns:
            Dictionary containing all analysis results and recommendation
        """
        try:
            initial_state: Dict[str, Any] = {
                "symbol": symbol,
                "company_name": company_name,
                "price_data": price_data or [],
                "news_data": news_data or [],
            }

            if user_profile:
                initial_state["userProfile"] = user_profile

            # Run the LangGraph workflow (parallel agents → summary)
            result = workflow_app.invoke(initial_state)

            return {
                "symbol": symbol,
                "fundamental_analysis": result.get("fundamental_analysis", ""),
                "technical_analysis": result.get("technical_analysis", ""),
                "news_analysis": result.get("news_analysis", ""),
                "recommendation": result.get("recommendation", ""),
            }

        except Exception as e:
            raise Exception(f"Error in agentic AI analysis: {str(e)}")
