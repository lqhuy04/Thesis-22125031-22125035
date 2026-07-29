import unittest
from unittest.mock import patch

from app.services.agentic_service import run_admin_analysis


class AdminAnalysisV2Tests(unittest.TestCase):
    @patch(
        "app.services.agentic_service.run_stock_analysis_v2",
        return_value={"buy": False, "confidence": 0.8},
    )
    def test_single_symbol_admin_analysis_uses_v2_runner(self, run_v2):
        result = run_admin_analysis(
            mode="manual",
            symbol="fpt",
            risk_appetite={"period": "mid_term"},
            data_selection={
                "news": False,
                "technical": {"rsi": True},
                "fundamental": False,
                "weight": {
                    "news": 0.0,
                    "technical": 1.0,
                    "fundamental": 0.0,
                },
            },
        )

        run_v2.assert_called_once_with(
            symbol="FPT",
            risk_appetite={"period": "mid_term"},
            mode="manual",
            data_selection={
                "news": False,
                "technical": {"rsi": True},
                "fundamental": False,
                "weight": {
                    "news": 0.0,
                    "technical": 1.0,
                    "fundamental": 0.0,
                },
            },
        )
        self.assertEqual(result["universe"], "single")
        self.assertEqual(
            result["results"][0]["recommendation"],
            {"buy": False, "confidence": 0.8},
        )


if __name__ == "__main__":
    unittest.main()
