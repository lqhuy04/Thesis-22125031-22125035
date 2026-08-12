import unittest
from threading import Barrier
from unittest.mock import patch

import pandas as pd

from app.backtest.engine import SignalGenerator
from app.backtest.pipeline import BacktestPipeline


def _agent_result(name, value):
    return {"agent_results": {name: value}}


class V2BacktestPipelineTests(unittest.TestCase):
    def setUp(self):
        self.pipeline = BacktestPipeline(
            symbol="ACB",
            trade_config={"max_hold_candles": 20},
        )

    @patch("app.backtest.pipeline.aggregator_agent")
    @patch("app.backtest.pipeline.recommendation_agent")
    @patch("app.backtest.pipeline.fundamental_analysis_agent")
    @patch("app.backtest.pipeline.fundamental_agent")
    @patch("app.backtest.pipeline.article_analysis_agent")
    @patch("app.backtest.pipeline.article_agent")
    @patch("app.backtest.pipeline.technical_analysis_agent")
    @patch("app.backtest.pipeline.technical_agent")
    def test_runs_complete_v2_chain_with_historical_price_plan(
        self,
        technical,
        technical_analysis,
        article,
        article_analysis,
        fundamental,
        fundamental_analysis,
        recommendation,
        aggregator,
    ):
        technical.side_effect = lambda state: _agent_result(
            "technical_agent",
            {
                "current_price": {
                    "value": 21.28,
                    "source": "Stock_Price_1d",
                },
                "total_score": 4,
                "max_score": 5,
            },
        )
        technical_analysis.return_value = _agent_result(
            "technical_analysis_agent",
            {"score": 0.8, "analysis": "Kỹ thuật tích cực."},
        )
        article.return_value = _agent_result(
            "article_agent",
            "Tin tức tích cực.",
        )
        article_analysis.return_value = _agent_result(
            "article_analysis_agent",
            {"score": 0.7, "analysis": "Tin tức hỗ trợ."},
        )
        fundamental.return_value = _agent_result(
            "fundamental_agent",
            "ROE tốt.",
        )
        fundamental_analysis.return_value = _agent_result(
            "fundamental_analysis_agent",
            {"score": 0.65, "analysis": "Cơ bản khá."},
        )
        recommendation.return_value = _agent_result(
            "recommendation_agent",
            {
                "buy": True,
                "score": 0.735,
                "entry_price": 21.28,
                "take_profit": 25.0,
                "stop_loss": 19.5,
                "max_hold_candles": 30,
            },
        )
        aggregator.return_value = {
            "final_output": {
                "buy": True,
                "entry_price": 21.28,
                "take_profit_price": 25.0,
                "stop_loss_price": 19.5,
                "max_hold_candles": 30,
                "analysis": {
                    "technical": "Kỹ thuật tích cực.",
                    "fundamental": "Cơ bản khá.",
                    "news": "Tin tức hỗ trợ.",
                    "summary": "Các nguồn đồng thuận.",
                },
                "score": {
                    "technical": 0.8,
                    "fundamental": 0.65,
                    "news": 0.7,
                    "total": 0.735,
                },
                "confidence": 0.83,
            }
        }

        result = self.pipeline.run_pipeline_at(
            "2023-05-04",
            interval="1d",
        )

        state = technical.call_args.args[0]
        self.assertFalse(state["plan"]["technical"]["use_current_price"])
        self.assertEqual(
            state["plan"]["technical"]["from_date"],
            "2022-05-04",
        )
        self.assertEqual(
            state["plan"]["article"]["from_date"],
            "2023-02-03",
        )
        self.assertEqual(
            state["plan"]["fundamental"]["as_of_date"],
            "2023-05-04",
        )
        self.assertEqual(state["risk_appetite"]["period"], "mid_term")
        self.assertTrue(result["buy"])
        self.assertEqual(result["recommendation"], "Mua")
        self.assertEqual(result["total_score"], 0.735)
        self.assertEqual(result["technical_total_score"], 4)
        self.assertEqual(result["max_hold_candles"], 30)
        self.assertEqual(
            result["data_sources_used"],
            ["technical", "article", "fundamental"],
        )
        recommendation.assert_called_once()
        aggregator.assert_called_once()

    @patch("app.backtest.pipeline.aggregator_agent")
    @patch("app.backtest.pipeline.recommendation_agent")
    @patch("app.backtest.pipeline.fundamental_analysis_agent")
    @patch("app.backtest.pipeline.fundamental_agent")
    @patch("app.backtest.pipeline.article_analysis_agent")
    @patch("app.backtest.pipeline.article_agent")
    @patch("app.backtest.pipeline.technical_analysis_agent")
    @patch("app.backtest.pipeline.technical_agent")
    def test_manual_mode_skips_disabled_news_and_fundamental(
        self,
        technical,
        technical_analysis,
        article,
        article_analysis,
        fundamental,
        fundamental_analysis,
        recommendation,
        aggregator,
    ):
        pipeline = BacktestPipeline(
            symbol="ACB",
            trade_config={"max_hold_candles": 20},
            mode="manual",
            data_selection={
                "news": False,
                "fundamental": False,
                "technical": {
                    "rsi": True,
                    "ma": False,
                    "boll": False,
                    "macd": False,
                    "kdj": False,
                },
                "weight": {
                    "news": 0.0,
                    "technical": 1.0,
                    "fundamental": 0.0,
                },
            },
        )
        technical.return_value = _agent_result(
            "technical_agent",
            {
                "current_price": {
                    "value": 21.28,
                    "source": "Stock_Price_1d",
                },
                "total_score": 0,
                "max_score": 1,
            },
        )
        technical_analysis.return_value = _agent_result(
            "technical_analysis_agent",
            {"score": 0.0, "analysis": "Kỹ thuật yếu."},
        )
        recommendation.return_value = _agent_result(
            "recommendation_agent",
            {
                "buy": False,
                "score": 0.0,
                "entry_price": 0.0,
                "take_profit": 0.0,
                "stop_loss": 0.0,
                "max_hold_candles": 0,
            },
        )
        aggregator.return_value = {
            "final_output": {
                "buy": False,
                "entry_price": 0.0,
                "take_profit_price": 0.0,
                "stop_loss_price": 0.0,
                "max_hold_candles": 0,
                "analysis": {"summary": "Chờ."},
                "score": {"technical": 0.0, "total": 0.0},
                "confidence": 0.8,
            }
        }

        result = pipeline.run_pipeline_at(
            "2023-05-04",
            interval="1d",
        )

        article.assert_not_called()
        article_analysis.assert_not_called()
        fundamental.assert_not_called()
        fundamental_analysis.assert_not_called()
        self.assertFalse(result["buy"])
        self.assertEqual(result["recommendation"], "Chờ")
        self.assertEqual(result["data_sources_used"], ["technical"])

    def test_enabled_source_chains_run_concurrently_before_recommendation(self):
        source_barrier = Barrier(3)

        def source_result(name, value):
            def run(_state):
                source_barrier.wait(timeout=2)
                return _agent_result(name, value)

            return run

        def analysis_result(source_name, analysis_name):
            def run(state):
                self.assertIn(source_name, state["agent_results"])
                return _agent_result(
                    analysis_name,
                    {"score": 0.5, "analysis": analysis_name},
                )

            return run

        def recommend(state):
            self.assertTrue(
                {
                    "technical_analysis_agent",
                    "article_analysis_agent",
                    "fundamental_analysis_agent",
                }.issubset(state["agent_results"])
            )
            return _agent_result(
                "recommendation_agent",
                {"buy": False, "score": 0.5},
            )

        with (
            patch(
                "app.backtest.pipeline.technical_agent",
                side_effect=source_result(
                    "technical_agent",
                    {"total_score": 3, "max_score": 5},
                ),
            ),
            patch(
                "app.backtest.pipeline.technical_analysis_agent",
                side_effect=analysis_result(
                    "technical_agent",
                    "technical_analysis_agent",
                ),
            ),
            patch(
                "app.backtest.pipeline.article_agent",
                side_effect=source_result("article_agent", "article data"),
            ),
            patch(
                "app.backtest.pipeline.article_analysis_agent",
                side_effect=analysis_result(
                    "article_agent",
                    "article_analysis_agent",
                ),
            ),
            patch(
                "app.backtest.pipeline.fundamental_agent",
                side_effect=source_result(
                    "fundamental_agent",
                    "fundamental data",
                ),
            ),
            patch(
                "app.backtest.pipeline.fundamental_analysis_agent",
                side_effect=analysis_result(
                    "fundamental_agent",
                    "fundamental_analysis_agent",
                ),
            ),
            patch(
                "app.backtest.pipeline.recommendation_agent",
                side_effect=recommend,
            ),
            patch(
                "app.backtest.pipeline.aggregator_agent",
                return_value={
                    "final_output": {
                        "buy": False,
                        "score": {"total": 0.5},
                        "confidence": 0.5,
                    }
                },
            ),
        ):
            result = self.pipeline.run_pipeline_at(
                "2023-05-04",
                interval="1d",
            )

        self.assertFalse(result["buy"])
        self.assertEqual(
            result["data_sources_used"],
            ["technical", "article", "fundamental"],
        )

    def test_configuration_describes_full_pipeline(self):
        self.assertEqual(
            self.pipeline.configuration(),
            {
                "mode": "auto",
                "period": "mid_term",
                "interval": "1d",
                "data_sources": [
                    "technical",
                    "article",
                    "fundamental",
                ],
                "selected_indicators": [
                    "ma",
                    "boll",
                    "rsi",
                    "macd",
                    "kdj",
                ],
                "weights": {
                    "news": 0.20,
                    "technical": 0.40,
                    "fundamental": 0.40,
                },
            },
        )

    def test_configuration_describes_single_indicator_pipeline(self):
        pipeline = BacktestPipeline(
            symbol="ACB",
            trade_config={"max_hold_candles": 20},
            mode="manual",
            data_selection={
                "news": False,
                "fundamental": False,
                "technical": {
                    "ma": False,
                    "boll": False,
                    "rsi": True,
                    "macd": False,
                    "kdj": False,
                },
                "weight": {
                    "news": 0.0,
                    "technical": 1.0,
                    "fundamental": 0.0,
                },
            },
        )

        self.assertEqual(
            pipeline.configuration(),
            {
                "mode": "manual",
                "period": "mid_term",
                "interval": "1d",
                "data_sources": ["technical"],
                "selected_indicators": ["rsi"],
                "weights": {
                    "news": 0.0,
                    "technical": 1.0,
                    "fundamental": 0.0,
                },
            },
        )

    def test_manual_indicator_scores_are_normalized_to_zero_five_scale(self):
        pipeline = BacktestPipeline(
            symbol="ACB",
            trade_config={"max_hold_candles": 20},
            mode="manual",
            data_selection={
                "technical": {
                    "rsi": True,
                    "ma": False,
                    "boll": False,
                    "macd": False,
                    "kdj": False,
                }
            },
        )
        frame = pd.DataFrame(
            {
                "datetime": pd.to_datetime(
                    ["2023-05-03", "2023-05-04", "2023-05-05"]
                ),
                "rsi_score": [0, 1, 1],
                "total_score": [0.0, 1.0, 1.0],
            }
        )

        selected = pipeline.apply_technical_selection(frame)

        self.assertEqual(selected["total_score"].tolist(), [0.0, 5.0, 5.0])
        self.assertEqual(
            pipeline.filter_signal_dates(frame),
            ["2023-05-04"],
        )

    def test_all_five_indicators_use_mid_term_fifty_percent_threshold(self):
        frame = pd.DataFrame(
            {
                "datetime": pd.to_datetime(
                    [
                        "2023-05-03",
                        "2023-05-04",
                        "2023-05-05",
                        "2023-05-06",
                    ]
                ),
                "ma_score": [0, 1, 1, 0],
                "boll_score": [1, 1, 1, 0],
                "rsi_score": [1, 1, 1, 0],
                "macd_score": [0, 0, 1, 0],
                "kdj_score": [0, 0, 0, 0],
                "total_score": [2.0, 3.0, 4.0, 0.0],
                "open": [20.0, 21.0, 22.0, 23.0],
            }
        )

        self.assertEqual(
            self.pipeline.filter_signal_dates(frame),
            ["2023-05-04", "2023-05-05"],
        )

        signaled = SignalGenerator().generate_signals(frame, min_score=2.5)
        self.assertTrue(pd.isna(signaled.iloc[0]["signal"]))
        self.assertEqual(signaled.iloc[1]["signal"], "BUY")
        self.assertEqual(signaled.iloc[2]["signal"], "BUY")
        self.assertTrue(pd.isna(signaled.iloc[3]["signal"]))

    def test_manual_low_technical_weight_disables_technical_prefilter(self):
        pipeline = BacktestPipeline(
            symbol="ACB",
            trade_config={"max_hold_candles": 20},
            mode="manual",
            data_selection={
                "technical": {"rsi": True},
                "weight": {
                    "news": 0.10,
                    "technical": 0.14,
                    "fundamental": 0.76,
                },
            },
        )
        frame = pd.DataFrame(
            {
                "datetime": pd.to_datetime(
                    ["2023-05-03", "2023-05-04", "2023-05-05"]
                ),
                "rsi_score": [0, 0, 0],
            }
        )

        self.assertEqual(pipeline.technical_signal_score(), 0.0)
        self.assertEqual(
            pipeline.filter_signal_dates(frame),
            ["2023-05-03", "2023-05-04"],
        )


if __name__ == "__main__":
    unittest.main()
