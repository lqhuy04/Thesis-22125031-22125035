import unittest
from datetime import date
from unittest.mock import patch

import agentic_ai_v2.analyze.graph as graph_module
from agentic_ai_v2.analyze.agents.aggregator import (
    AggregatorLLMOutput,
    aggregator_agent,
)
from agentic_ai_v2.analyze.agents.article_analysis import (
    ArticleAnalysisOutput,
    article_analysis_agent,
)
from agentic_ai_v2.analyze.agents.fundamental_analysis import (
    FundamentalAnalysisOutput,
    fundamental_analysis_agent,
)
from agentic_ai_v2.analyze.agents.fundamental import (
    _cagr,
    _rows_available_before,
    fundamental_agent,
)
from agentic_ai_v2.analyze.agents.recommendation import (
    TradingPlanOutput,
    _calculate_total_score,
    _is_valid_plan,
    recommendation_agent,
)
from agentic_ai_v2.analyze.agents.technical_analysis import (
    TechnicalAnalysisOutput,
    _calculate_score,
    technical_analysis_agent,
)
from agentic_ai_v2.analyze.graph import (
    _route_selected_agents,
    build_graph,
)
from agentic_ai_v2.analyze.language import (
    normalize_language,
    output_language_instruction,
)


class V2AnalysisAgentTests(unittest.TestCase):
    def test_fundamental_cagr_uses_first_and_last_available_year(self):
        rows = [
            {"year": 2021, "roe": 0.20},
            {"year": 2022, "roe": None},
            {"year": 2025, "roe": 0.29282},
        ]

        self.assertAlmostEqual(_cagr(rows, "roe"), 0.10, places=6)

    @patch(
        "agentic_ai_v2.analyze.agents.fundamental._get_industry_rows",
        return_value=[],
    )
    @patch(
        "agentic_ai_v2.analyze.agents.fundamental._get_company_context",
        return_value=(False, None),
    )
    @patch(
        "agentic_ai_v2.analyze.agents.fundamental."
        "FundamentalAnalysisService.get_indicator_history"
    )
    def test_fundamental_agent_uses_indicator_history_for_cagr(
        self,
        get_indicator_history,
        _get_company_context,
        _get_industry_rows,
    ):
        get_indicator_history.return_value = [
            {"year": 2021, "current_ratio": 1.0},
            {"year": 2025, "current_ratio": 1.4641},
        ]

        output = fundamental_agent({"symbol": "vnm"})["agent_results"][
            "fundamental_agent"
        ]

        get_indicator_history.assert_called_once_with("VNM")
        self.assertIn("Phân tích cơ bản (2021–2025)", output)
        self.assertIn("CAGR: 10.00%/năm", output)

    def test_fundamental_backtest_excludes_same_year_and_future_rows(self):
        rows = [
            {"year": 2021, "roe": 0.1},
            {"year": "2022", "roe": 0.2},
            {"year": 2023, "roe": 0.3},
            {"year": 2024, "roe": 0.4},
        ]

        self.assertEqual(
            _rows_available_before(rows, date(2023, 8, 1)),
            rows[:2],
        )
        self.assertIs(_rows_available_before(rows, None), rows)

    @patch(
        "agentic_ai_v2.analyze.agents.article_analysis."
        "_call_article_analysis_llm"
    )
    def test_article_analysis_scores_and_summarizes_article_text(
        self,
        call_llm,
    ):
        call_llm.return_value = ArticleAnalysisOutput(
            score=0.76,
            analysis="Tin tức nhìn chung tích cực.",
        )
        state = {
            "agent_results": {
                "article_agent": "Mã cổ phiếu: FPT\n1. FPT tăng trưởng."
            }
        }

        result = article_analysis_agent(state)["agent_results"][
            "article_analysis_agent"
        ]

        self.assertEqual(
            result,
            {
                "score": 0.76,
                "analysis": "Tin tức nhìn chung tích cực.",
            },
        )
        call_llm.assert_called_once_with(
            "Mã cổ phiếu: FPT\n1. FPT tăng trưởng.",
            "vi",
        )

    @patch(
        "agentic_ai_v2.analyze.agents.fundamental_analysis."
        "_call_fundamental_analysis_llm"
    )
    def test_fundamental_analysis_scores_and_summarizes_fundamental_text(
        self,
        call_llm,
    ):
        call_llm.return_value = FundamentalAnalysisOutput(
            score=0.64,
            analysis="Nền tảng cơ bản ở mức khá.",
        )
        state = {
            "agent_results": {
                "fundamental_agent": "ROE tăng và đòn bẩy ổn định."
            }
        }

        result = fundamental_analysis_agent(state)["agent_results"][
            "fundamental_analysis_agent"
        ]

        self.assertEqual(
            result,
            {
                "score": 0.64,
                "analysis": "Nền tảng cơ bản ở mức khá.",
            },
        )
        call_llm.assert_called_once_with(
            "ROE tăng và đòn bẩy ổn định.",
            "vi",
        )

    @patch(
        "agentic_ai_v2.analyze.agents.technical_analysis."
        "_call_technical_analysis_llm"
    )
    def test_technical_analysis_uses_llm_score(
        self,
        call_llm,
    ):
        technical_data = {
            "current_price": {
                "value": 128.5,
                "source": "Current_Stock_Price",
            },
            "total_score": 3,
            "max_score": 5,
            "indicators": {"rsi": {"score": 1}},
        }
        call_llm.return_value = TechnicalAnalysisOutput(
            score=0.73,
            analysis="Ba trên năm tín hiệu đang tích cực."
        )

        result = technical_analysis_agent(
            {"agent_results": {"technical_agent": technical_data}}
        )["agent_results"]["technical_analysis_agent"]

        self.assertEqual(
            result,
            {
                "score": 0.73,
                "analysis": "Ba trên năm tín hiệu đang tích cực.",
            },
        )
        call_llm.assert_called_once_with(technical_data, "vi")

    @patch(
        "agentic_ai_v2.analyze.agents.technical_analysis."
        "_call_technical_analysis_llm"
    )
    def test_technical_analysis_passes_english_to_llm(
        self,
        call_llm,
    ):
        technical_data = {
            "total_score": 1,
            "max_score": 2,
        }
        call_llm.return_value = TechnicalAnalysisOutput(
            score=0.51,
            analysis="The technical signals are mixed."
        )

        result = technical_analysis_agent(
            {
                "language": "en",
                "agent_results": {
                    "technical_agent": technical_data,
                },
            }
        )["agent_results"]["technical_analysis_agent"]

        self.assertEqual(
            result["analysis"],
            "The technical signals are mixed.",
        )
        call_llm.assert_called_once_with(technical_data, "en")

    @patch(
        "agentic_ai_v2.analyze.agents.technical_analysis."
        "_call_technical_analysis_llm"
    )
    def test_technical_analysis_falls_back_to_rule_score_when_llm_fails(
        self,
        call_llm,
    ):
        call_llm.side_effect = RuntimeError("LLM unavailable")
        technical_data = {
            "total_score": 3,
            "max_score": 5,
            "indicators": {"rsi": {"score": 1}},
        }

        result = technical_analysis_agent(
            {"agent_results": {"technical_agent": technical_data}}
        )["agent_results"]["technical_analysis_agent"]

        self.assertEqual(result["score"], 0.6)
        self.assertEqual(
            result["analysis"],
            "Không thể tóm tắt dữ liệu phân tích kỹ thuật.",
        )

    def test_no_data_fallbacks_follow_english_language(self):
        state = {
            "language": "en",
            "agent_results": {
                "article_agent": "Không có dữ liệu tin tức.",
                "fundamental_agent": (
                    "Không có dữ liệu phân tích cơ bản."
                ),
            },
        }

        article = article_analysis_agent(state)["agent_results"][
            "article_analysis_agent"
        ]
        fundamental = fundamental_analysis_agent(state)[
            "agent_results"
        ]["fundamental_analysis_agent"]
        technical = technical_analysis_agent(
            {"language": "en", "agent_results": {}}
        )["agent_results"]["technical_analysis_agent"]

        self.assertEqual(
            article["analysis"],
            "No news data is available.",
        )
        self.assertEqual(
            fundamental["analysis"],
            "No fundamental analysis data is available.",
        )
        self.assertEqual(
            technical["analysis"],
            "No technical analysis data is available.",
        )

    def test_analysis_language_helpers_default_to_vi_and_support_en(self):
        self.assertEqual(normalize_language(None), "vi")
        self.assertEqual(normalize_language("en"), "en")
        self.assertIn(
            "entirely in English",
            output_language_instruction("en"),
        )

    def test_technical_score_is_bounded_and_handles_invalid_denominator(self):
        self.assertEqual(
            _calculate_score({"total_score": 7, "max_score": 5}),
            1.0,
        )
        self.assertEqual(
            _calculate_score({"total_score": -1, "max_score": 5}),
            0.0,
        )
        self.assertEqual(
            _calculate_score({"total_score": 1, "max_score": 0}),
            0.0,
        )


class V2RecommendationAgentTests(unittest.TestCase):
    def test_period_weights_match_requested_matrix(self):
        fundamental_only = {
            "fundamental": 1.0,
            "technical": 0.0,
            "article": 0.0,
        }
        technical_only = {
            "fundamental": 0.0,
            "technical": 1.0,
            "article": 0.0,
        }
        article_only = {
            "fundamental": 0.0,
            "technical": 0.0,
            "article": 1.0,
        }

        self.assertEqual(
            _calculate_total_score("short_term", fundamental_only),
            0.1,
        )
        self.assertEqual(
            _calculate_total_score("short_term", technical_only),
            0.6,
        )
        self.assertEqual(
            _calculate_total_score("short_term", article_only),
            0.3,
        )
        self.assertEqual(
            _calculate_total_score("mid_term", fundamental_only),
            0.4,
        )
        self.assertEqual(
            _calculate_total_score("mid_term", technical_only),
            0.4,
        )
        self.assertEqual(
            _calculate_total_score("mid_term", article_only),
            0.2,
        )
        self.assertEqual(
            _calculate_total_score("long_term", fundamental_only),
            0.7,
        )
        self.assertEqual(
            _calculate_total_score("long_term", technical_only),
            0.15,
        )
        self.assertEqual(
            _calculate_total_score("long_term", article_only),
            0.15,
        )

    @patch(
        "agentic_ai_v2.analyze.agents.recommendation."
        "_call_trading_plan_llm"
    )
    def test_score_at_threshold_buys_and_returns_llm_trading_plan(
        self,
        call_llm,
    ):
        call_llm.return_value = TradingPlanOutput(
            take_profit=120.0,
            stop_loss=92.0,
            max_hold_candles=30,
        )
        state = {
            "symbol": "FPT",
            "risk_appetite": {"period": "mid_term"},
            "agent_results": {
                "article_analysis_agent": {
                    "score": 0.5,
                    "analysis": "Tin tức khá tích cực.",
                },
                "fundamental_analysis_agent": {
                    "score": 0.75,
                    "analysis": "Cơ bản còn thận trọng.",
                },
                "technical_analysis_agent": {
                    "score": 0.5,
                    "analysis": "Kỹ thuật vừa đạt ngưỡng.",
                },
                "technical_agent": {
                    "current_price": {"value": 100.0},
                },
            },
        }

        result = recommendation_agent(state)["agent_results"][
            "recommendation_agent"
        ]

        self.assertEqual(
            result,
            {
                "score": 0.6,
                "buy": True,
                "recommendation": "Mua",
                "entry_price": 100.0,
                "take_profit": 120.0,
                "stop_loss": 92.0,
                "max_hold_candles": 30,
            },
        )
        call_llm.assert_called_once()

    def test_trading_plan_must_follow_period_ranges_and_reward_risk(self):
        valid_plans = {
            "short_term": TradingPlanOutput(
                take_profit=112.0,
                stop_loss=94.0,
                max_hold_candles=10,
            ),
            "mid_term": TradingPlanOutput(
                take_profit=120.0,
                stop_loss=90.0,
                max_hold_candles=30,
            ),
            "long_term": TradingPlanOutput(
                take_profit=150.0,
                stop_loss=82.0,
                max_hold_candles=52,
            ),
        }

        for period, plan in valid_plans.items():
            with self.subTest(period=period):
                self.assertTrue(_is_valid_plan(plan, 100.0, period))

        invalid_plans = {
            "take_profit_out_of_range": TradingPlanOutput(
                take_profit=107.0,
                stop_loss=95.0,
                max_hold_candles=10,
            ),
            "stop_loss_out_of_range": TradingPlanOutput(
                take_profit=110.0,
                stop_loss=97.0,
                max_hold_candles=10,
            ),
            "max_hold_out_of_range": TradingPlanOutput(
                take_profit=110.0,
                stop_loss=95.0,
                max_hold_candles=16,
            ),
            "reward_risk_too_low": TradingPlanOutput(
                take_profit=108.0,
                stop_loss=93.0,
                max_hold_candles=10,
            ),
        }

        for reason, plan in invalid_plans.items():
            with self.subTest(reason=reason):
                self.assertFalse(
                    _is_valid_plan(plan, 100.0, "short_term")
                )

        self.assertFalse(
            _is_valid_plan(valid_plans["mid_term"], None, "mid_term")
        )

    @patch(
        "agentic_ai_v2.analyze.agents.recommendation."
        "_call_trading_plan_llm"
    )
    def test_invalid_llm_plan_uses_period_fallback(self, call_llm):
        call_llm.return_value = TradingPlanOutput(
            take_profit=110.0,
            stop_loss=95.0,
            max_hold_candles=100,
        )
        state = {
            "risk_appetite": {"period": "mid_term"},
            "agent_results": {
                "article_analysis_agent": {"score": 1.0},
                "fundamental_analysis_agent": {"score": 1.0},
                "technical_analysis_agent": {"score": 1.0},
                "technical_agent": {
                    "current_price": {"value": 100.0},
                },
            },
        }

        result = recommendation_agent(state)["agent_results"][
            "recommendation_agent"
        ]

        self.assertEqual(result["entry_price"], 100.0)
        self.assertEqual(result["take_profit"], 120.0)
        self.assertEqual(result["stop_loss"], 90.0)
        self.assertEqual(result["max_hold_candles"], 30)

    @patch(
        "agentic_ai_v2.analyze.agents.recommendation."
        "_call_trading_plan_llm"
    )
    def test_score_below_threshold_waits_without_calling_llm(
        self,
        call_llm,
    ):
        state = {
            "risk_appetite": {"period": "long_term"},
            "agent_results": {
                "article_analysis_agent": {"score": 0.54},
                "fundamental_analysis_agent": {"score": 0.54},
                "technical_analysis_agent": {"score": 0.54},
            },
        }

        result = recommendation_agent(state)["agent_results"][
            "recommendation_agent"
        ]

        self.assertEqual(
            result,
            {
                "score": 0.54,
                "buy": False,
                "recommendation": "Chờ",
                "entry_price": 0.0,
                "take_profit": 0.0,
                "stop_loss": 0.0,
                "max_hold_candles": 0,
            },
        )
        call_llm.assert_not_called()

    @patch(
        "agentic_ai_v2.analyze.agents.recommendation."
        "_call_trading_plan_llm"
    )
    def test_high_total_score_waits_when_technical_is_below_threshold(
        self,
        call_llm,
    ):
        state = {
            "mode": "auto",
            "risk_appetite": {"period": "long_term"},
            "agent_results": {
                "article_analysis_agent": {"score": 1.0},
                "fundamental_analysis_agent": {"score": 1.0},
                "technical_analysis_agent": {"score": 0.39},
                "technical_agent": {
                    "current_price": {"value": 100.0},
                },
            },
        }

        result = recommendation_agent(state)["agent_results"][
            "recommendation_agent"
        ]

        self.assertEqual(result["score"], 0.9085)
        self.assertFalse(result["buy"])
        self.assertEqual(result["recommendation"], "Chờ")
        self.assertEqual(result["entry_price"], 0.0)
        call_llm.assert_not_called()

    @patch(
        "agentic_ai_v2.analyze.agents.recommendation."
        "_call_trading_plan_llm"
    )
    def test_short_term_keeps_point_60_technical_gate(
        self,
        call_llm,
    ):
        state = {
            "mode": "auto",
            "risk_appetite": {"period": "short_term"},
            "agent_results": {
                "article_analysis_agent": {"score": 1.0},
                "fundamental_analysis_agent": {"score": 1.0},
                "technical_analysis_agent": {"score": 0.59},
            },
        }

        result = recommendation_agent(state)["agent_results"][
            "recommendation_agent"
        ]

        self.assertEqual(result["score"], 0.754)
        self.assertFalse(result["buy"])
        call_llm.assert_not_called()

    @patch(
        "agentic_ai_v2.analyze.agents.recommendation."
        "_call_trading_plan_llm"
    )
    def test_manual_mode_uses_payload_weights(self, call_llm):
        call_llm.return_value = TradingPlanOutput(
            take_profit=150.0,
            stop_loss=82.0,
            max_hold_candles=30,
        )
        state = {
            "mode": "manual",
            "risk_appetite": {"period": "long_term"},
            "data_selection": {
                "weight": {
                    "news": 0.0,
                    "technical": 1.0,
                    "fundamental": 0.0,
                }
            },
            "agent_results": {
                "article_analysis_agent": {"score": 0.9},
                "fundamental_analysis_agent": {"score": 0.1},
                "technical_analysis_agent": {"score": 0.6},
                "technical_agent": {
                    "current_price": {"value": 100.0},
                },
            },
        }

        result = recommendation_agent(state)["agent_results"][
            "recommendation_agent"
        ]

        self.assertEqual(result["score"], 0.6)
        self.assertTrue(result["buy"])
        call_llm.assert_called_once()

    @patch(
        "agentic_ai_v2.analyze.agents.recommendation."
        "_call_trading_plan_llm"
    )
    def test_manual_technical_weight_below_point_15_skips_gate(
        self,
        call_llm,
    ):
        call_llm.return_value = TradingPlanOutput(
            take_profit=150.0,
            stop_loss=82.0,
            max_hold_candles=52,
        )
        state = {
            "mode": "manual",
            "risk_appetite": {"period": "long_term"},
            "data_selection": {
                "weight": {
                    "news": 0.10,
                    "technical": 0.14,
                    "fundamental": 0.76,
                }
            },
            "agent_results": {
                "article_analysis_agent": {"score": 0.8},
                "fundamental_analysis_agent": {"score": 0.8},
                "technical_analysis_agent": {"score": 0.0},
                "technical_agent": {
                    "current_price": {"value": 100.0},
                },
            },
        }

        result = recommendation_agent(state)["agent_results"][
            "recommendation_agent"
        ]

        self.assertEqual(result["score"], 0.688)
        self.assertTrue(result["buy"])
        call_llm.assert_called_once()

    @patch(
        "agentic_ai_v2.analyze.agents.recommendation."
        "_call_trading_plan_llm"
    )
    def test_manual_technical_weight_at_point_15_keeps_gate(
        self,
        call_llm,
    ):
        state = {
            "mode": "manual",
            "risk_appetite": {"period": "long_term"},
            "data_selection": {
                "weight": {
                    "news": 0.10,
                    "technical": 0.15,
                    "fundamental": 0.75,
                }
            },
            "agent_results": {
                "article_analysis_agent": {"score": 0.8},
                "fundamental_analysis_agent": {"score": 0.9},
                "technical_analysis_agent": {"score": 0.39},
            },
        }

        result = recommendation_agent(state)["agent_results"][
            "recommendation_agent"
        ]

        self.assertEqual(result["score"], 0.8135)
        self.assertFalse(result["buy"])
        call_llm.assert_not_called()

    @patch(
        "agentic_ai_v2.analyze.agents.recommendation."
        "_call_trading_plan_llm"
    )
    def test_auto_mode_ignores_payload_weights(self, call_llm):
        state = {
            "mode": "auto",
            "risk_appetite": {"period": "long_term"},
            "data_selection": {
                "weight": {
                    "news": 0.0,
                    "technical": 1.0,
                    "fundamental": 0.0,
                }
            },
            "agent_results": {
                "article_analysis_agent": {"score": 0.9},
                "fundamental_analysis_agent": {"score": 0.1},
                "technical_analysis_agent": {"score": 0.6},
            },
        }

        result = recommendation_agent(state)["agent_results"][
            "recommendation_agent"
        ]

        self.assertEqual(result["score"], 0.295)
        self.assertFalse(result["buy"])
        call_llm.assert_not_called()


class V2AggregatorAgentTests(unittest.TestCase):
    @patch(
        "agentic_ai_v2.analyze.agents.aggregator."
        "_call_aggregator_llm"
    )
    def test_aggregator_maps_existing_results_and_adds_llm_fields(
        self,
        call_llm,
    ):
        call_llm.return_value = AggregatorLLMOutput(
            confidence=0.83,
            summary="Các nguồn nhìn chung đồng thuận với quyết định.",
        )
        state = {
            "symbol": "FPT",
            "risk_appetite": {"period": "mid_term"},
            "agent_results": {
                "article_analysis_agent": {
                    "score": 0.7,
                    "analysis": "Tin tức hỗ trợ.",
                },
                "fundamental_analysis_agent": {
                    "score": 0.65,
                    "analysis": "Nền tảng cơ bản khá.",
                },
                "technical_analysis_agent": {
                    "score": 0.8,
                    "analysis": "Xu hướng kỹ thuật tích cực.",
                },
                "recommendation_agent": {
                    "score": 0.735,
                    "buy": True,
                    "recommendation": "Mua",
                    "entry_price": 128_500.0,
                    "take_profit": 150_000.0,
                    "stop_loss": 118_000.0,
                    "max_hold_candles": 30,
                },
            },
        }

        result = aggregator_agent(state)

        self.assertEqual(
            result["final_output"],
            {
                "buy": True,
                "entry_price": 128_500.0,
                "take_profit_price": 150_000.0,
                "stop_loss_price": 118_000.0,
                "max_hold_candles": 30,
                "analysis": {
                    "technical": "Xu hướng kỹ thuật tích cực.",
                    "fundamental": "Nền tảng cơ bản khá.",
                    "news": "Tin tức hỗ trợ.",
                    "summary": (
                        "Các nguồn nhìn chung đồng thuận với quyết định."
                    ),
                },
                "score": {
                    "news": 0.7,
                    "technical": 0.8,
                    "fundamental": 0.65,
                    "total": 0.735,
                },
                "confidence": 0.83,
            },
        )
        call_llm.assert_called_once_with(state)

    @patch(
        "agentic_ai_v2.analyze.agents.aggregator."
        "_call_aggregator_llm",
        side_effect=RuntimeError("LLM unavailable"),
    )
    def test_aggregator_returns_error_when_llm_synthesis_fails(
        self,
        _call_llm,
    ):
        with patch(
            "agentic_ai_v2.analyze.agents.aggregator.logger.exception"
        ):
            result = aggregator_agent({"agent_results": {}})

        self.assertEqual(result, {"error": "LLM unavailable"})


class V2AnalysisGraphTests(unittest.TestCase):
    def test_auto_mode_starts_all_source_agents(self):
        self.assertEqual(
            _route_selected_agents({"mode": "auto"}),
            [
                "article_agent",
                "technical_agent",
                "fundamental_agent",
            ],
        )

    def test_manual_mode_starts_only_selected_source_agents(self):
        state = {
            "mode": "manual",
            "data_selection": {
                "news": True,
                "technical": {"rsi": True, "macd": False},
                "fundamental": False,
            },
        }

        self.assertEqual(
            _route_selected_agents(state),
            ["article_agent", "technical_agent"],
        )

    def test_each_source_flows_through_its_analysis_agent(self):
        edges = {
            (edge.source, edge.target)
            for edge in build_graph().get_graph().edges
        }

        self.assertIn(
            ("article_agent", "article_analysis_agent"),
            edges,
        )
        self.assertIn(
            ("article_analysis_agent", "recommendation_agent"),
            edges,
        )
        self.assertIn(
            ("fundamental_agent", "fundamental_analysis_agent"),
            edges,
        )
        self.assertIn(
            ("fundamental_analysis_agent", "recommendation_agent"),
            edges,
        )
        self.assertIn(
            ("technical_agent", "technical_analysis_agent"),
            edges,
        )
        self.assertIn(
            ("technical_analysis_agent", "recommendation_agent"),
            edges,
        )
        self.assertIn(
            ("recommendation_agent", "aggregator"),
            edges,
        )

    def test_parallel_source_chains_merge_before_single_aggregator_run(self):
        aggregator_inputs = []

        def source_result(name, value):
            return lambda _state: {
                "agent_results": {
                    name: value,
                }
            }

        def analysis_result(source_name, analysis_name):
            return lambda state: {
                "agent_results": {
                    analysis_name: {
                        "score": 0.5,
                        "analysis": str(
                            state["agent_results"][source_name]
                        ),
                    }
                }
            }

        def aggregate(state):
            aggregator_inputs.append(state["agent_results"])
            return {"final_output": state["agent_results"]}

        def recommend(state):
            for analysis_name in (
                "article_analysis_agent",
                "fundamental_analysis_agent",
                "technical_analysis_agent",
            ):
                if analysis_name not in state["agent_results"]:
                    raise AssertionError(
                        f"Missing analysis result: {analysis_name}"
                    )
            return {
                "agent_results": {
                    "recommendation_agent": {
                        "score": 0.5,
                        "buy": False,
                        "recommendation": "Chờ",
                        "entry_price": 0.0,
                        "take_profit": 0.0,
                        "stop_loss": 0.0,
                        "max_hold_candles": 0,
                    }
                }
            }

        with (
            patch.object(
                graph_module,
                "orchestrator_agent",
                return_value={"plan": {}},
            ),
            patch.object(
                graph_module,
                "article_agent",
                source_result("article_agent", "article raw"),
            ),
            patch.object(
                graph_module,
                "article_analysis_agent",
                analysis_result(
                    "article_agent",
                    "article_analysis_agent",
                ),
            ),
            patch.object(
                graph_module,
                "fundamental_agent",
                source_result("fundamental_agent", "fundamental raw"),
            ),
            patch.object(
                graph_module,
                "fundamental_analysis_agent",
                analysis_result(
                    "fundamental_agent",
                    "fundamental_analysis_agent",
                ),
            ),
            patch.object(
                graph_module,
                "technical_agent",
                source_result(
                    "technical_agent",
                    {"total_score": 2, "max_score": 5},
                ),
            ),
            patch.object(
                graph_module,
                "technical_analysis_agent",
                analysis_result(
                    "technical_agent",
                    "technical_analysis_agent",
                ),
            ),
            patch.object(
                graph_module,
                "recommendation_agent",
                recommend,
            ),
            patch.object(
                graph_module,
                "aggregator_agent",
                aggregate,
            ),
        ):
            result = graph_module.build_graph().invoke(
                {
                    "mode": "auto",
                    "agent_results": {},
                }
            )

        self.assertEqual(len(aggregator_inputs), 1)
        self.assertIn(
            "recommendation_agent",
            result["final_output"],
        )


if __name__ == "__main__":
    unittest.main()
