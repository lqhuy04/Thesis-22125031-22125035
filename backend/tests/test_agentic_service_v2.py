import unittest
from unittest.mock import patch

from app.services.agentic_service import (
    _run_stock_analysis_with_graph,
    run_admin_analysis,
)


class AdminAnalysisV2Tests(unittest.TestCase):
    def test_public_analysis_propagates_english_to_graph_state(self):
        class GraphStub:
            state = None

            def invoke(self, state):
                self.state = state
                return {
                    "error": None,
                    "final_output": {"buy": False},
                }

        graph = GraphStub()
        result = _run_stock_analysis_with_graph(
            graph=graph,
            symbol="FPT",
            risk_appetite={"period": "mid_term"},
            mode="auto",
            language="en",
        )

        self.assertEqual(result, {"buy": False})
        self.assertEqual(graph.state["language"], "en")
        self.assertTrue(
            graph.state["user_input"].startswith("Summarize FPT")
        )

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
