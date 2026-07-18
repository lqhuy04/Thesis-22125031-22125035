import unittest
from types import SimpleNamespace
from unittest.mock import patch

from agentic_ai.analyze.agents import aggregator


class FakeLengthError(Exception):
    pass


class FakeCompletions:
    def __init__(self):
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        raise FakeLengthError("output reached token limit")


class FakeClient:
    def __init__(self, completions=None):
        self.completions = completions or FakeCompletions()
        self.chat = type("Chat", (), {"completions": self.completions})()
        self.beta = type("Beta", (), {"chat": self.chat})()


class SuccessfulCompletions:
    def __init__(self, parsed):
        self.calls = []
        self.parsed = parsed

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(parsed=self.parsed))]
        )


def backtest_state():
    return {
        "user_input": "Backtest pipeline for ACB on 2023-05-04",
        "risk_appetite": {},
        "data_selection": {},
        "plan": {"technical_analysis_agent": {"interval": "1d"}},
        "agent_results": {
            "technical_analysis_agent": {
                "total_score": 4,
                "max_score": 5,
                "current_price": {"value": 21.28},
                "indicators": {"rsi": {"score": 1}},
            },
            "fundamental_analysis_agent": "ROE 20%, sức khỏe tài chính tốt.",
            "article_agent": "Tin tức tích cực.",
        },
    }


class AggregatorBacktestTests(unittest.TestCase):
    def test_backtest_keeps_original_request_and_never_retries_length_error(self):
        client = FakeClient()
        with (
            patch.object(aggregator, "_get_openai_client", return_value=client),
            patch.object(aggregator, "_LengthError", FakeLengthError),
        ):
            result = aggregator.aggregator_agent(backtest_state())

        self.assertEqual(len(client.completions.calls), 1)
        request = client.completions.calls[0]
        self.assertIs(request["response_format"], aggregator.InvestmentRecommendation)
        self.assertEqual(request["max_tokens"], aggregator._MAX_OUTPUT_TOKENS)
        self.assertEqual(len(request["messages"]), 2)
        self.assertEqual(
            request["messages"][0]["content"], aggregator.AGGREGATOR_SYSTEM_PROMPT
        )
        self.assertEqual(result["final_output"]["recommendation"], "Chờ")

    def test_backtest_keeps_llm_max_hold_candles(self):
        parsed = aggregator.InvestmentRecommendation(
            recommendation="Mua",
            entry_price=21.28,
            take_profit_price=25.0,
            stop_loss_price=19.5,
            max_hold_candles=47,
            analysis={
                "technical": "Kỹ thuật tích cực.",
                "fundamental": "Nền tảng tài chính tốt.",
                "news": "Tin tức hỗ trợ.",
                "summary": "Tín hiệu tổng hợp phù hợp.",
            },
            technical_score=4,
            fundamental_health="strong",
            article_sentiment="positive",
            data_sources_used=["technical", "fundamental", "article"],
        )
        completions = SuccessfulCompletions(parsed)
        client = FakeClient(completions)

        with patch.object(aggregator, "_get_openai_client", return_value=client):
            result = aggregator.aggregator_agent(backtest_state())

        self.assertEqual(len(completions.calls), 1)
        self.assertEqual(result["final_output"]["max_hold_candles"], 47)


if __name__ == "__main__":
    unittest.main()
