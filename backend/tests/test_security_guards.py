import unittest
from inspect import signature
from pathlib import Path

from pydantic import ValidationError

from agentic_ai.chatbot.sql_runner import (
    TECHNICAL_MAX_ROWS,
    UnsafeSQLError,
    sanitize_sql,
)
from app.models.agentic_schemas import (
    AdminAnalysisRequest,
    ChatRequest,
    StockAnalysisRequest,
)
from app.models.auth_schemas import LoginRequest, VerifyOTPRequest
from app.models.backtest_pipeline_schemas import BacktestPipelineRequest
from app.backtest.engine import DEFAULT_TRANSACTION_COST_PCT, TradeSimulator
from app.backtest.run import run_full_backtest
from app.utils.otp import OTPService


class SQLGuardTests(unittest.TestCase):
    def test_expected_market_queries_are_allowed_and_capped(self):
        guarded = sanitize_sql('SELECT "stock_symbol" FROM "Stock"')
        self.assertIn("LIMIT 100", guarded)
        sanitize_sql(
            'SELECT ("current_price") AS current_price '
            'FROM "Current_Stock_Price" LIMIT 1'
        )
        sanitize_sql(
            'SELECT "stock_symbol", COUNT(*) AS total FROM "Stock" '
            'GROUP BY ("stock_symbol") HAVING (COUNT(*) > 0) '
            'ORDER BY ("stock_symbol") LIMIT 10'
        )
        sanitize_sql(
            'SELECT COUNT(*) AS total, MAX("stock_symbol") FROM "Stock" LIMIT 50'
        )
        sanitize_sql(
            'WITH prices AS (SELECT * FROM "Current_Stock_Price" LIMIT 10) '
            "SELECT COUNT(*) FROM prices"
        )
        technical_sql = (
            'SELECT "close" FROM "Stock_Price_1d" '
            "ORDER BY trading_time DESC LIMIT 200"
        )
        sanitize_sql(technical_sql, max_rows=TECHNICAL_MAX_ROWS)

        with self.assertRaises(UnsafeSQLError):
            sanitize_sql(
                'SELECT "close" FROM "Stock_Price_1d" LIMIT 201',
                max_rows=TECHNICAL_MAX_ROWS,
            )

    def test_dangerous_queries_are_rejected(self):
        queries = [
            'SELECT pg_read_file(\'/etc/passwd\') FROM "Stock"',
            'SELECT current_setting(\'server_version\') FROM "Stock"',
            'SELECT pg_sleep(1) FROM "Stock"',
            'SELECT random() FROM "Stock"',
            'SELECT * FROM "User"',
            'SELECT * FROM "Stock" LIMIT 101',
            'SELECT * FROM "Stock"; SELECT * FROM "Article"',
        ]
        for query in queries:
            with self.subTest(query=query), self.assertRaises(UnsafeSQLError):
                sanitize_sql(query)


class InputGuardTests(unittest.TestCase):
    def test_existing_mobile_payloads_remain_valid(self):
        LoginRequest(email="admin@example.com", password="Secret123")
        legacy_analysis = StockAnalysisRequest(
            mode="auto",
            symbol="FPT",
            risk_appetite={"period": "short_term"},
        )
        english_analysis = StockAnalysisRequest(
            mode="auto",
            symbol="FPT",
            language="en",
            risk_appetite={"period": "short_term"},
        )
        self.assertEqual(legacy_analysis.language, "vi")
        self.assertEqual(english_analysis.language, "en")
        ChatRequest(
            session_id="123e4567-e89b-42d3-a456-426614174000",
            message="Phân tích FPT",
        )
        BacktestPipelineRequest(symbol="FPT")
        AdminAnalysisRequest(
            mode="manual",
            symbol="FPT",
            risk_appetite={"period": "mid_term"},
            data_selection={
                "news": True,
                "technical": {"rsi": True},
                "fundamental": True,
                "weight": {
                    "news": 0.2,
                    "technical": 0.4,
                    "fundamental": 0.4,
                },
            },
        )

    def test_backtest_legacy_configuration_fields_are_removed(self):
        for field_name in (
            "min_signal_score",
            "one_minute_lookback_days",
            "use_intraday",
        ):
            with self.subTest(field_name=field_name):
                self.assertNotIn(
                    field_name,
                    BacktestPipelineRequest.model_fields,
                )

    def test_backtest_transaction_cost_is_internal_and_defaults_to_0_15_percent(
        self,
    ):
        self.assertNotIn(
            "transaction_cost_pct",
            BacktestPipelineRequest.model_fields,
        )
        self.assertEqual(DEFAULT_TRANSACTION_COST_PCT, 0.0015)
        simulator = TradeSimulator(max_hold_candles=20)
        self.assertEqual(simulator.transaction_cost_pct, 0.0015)
        self.assertEqual(
            signature(run_full_backtest)
            .parameters["transaction_cost_pct"]
            .default,
            0.0015,
        )

    def test_stock_analysis_requires_at_least_one_technical_indicator(self):
        StockAnalysisRequest(
            mode="manual",
            symbol="FPT",
            risk_appetite={"period": "short_term"},
            data_selection={
                "news": False,
                "technical": {
                    "ma": False,
                    "boll": False,
                    "rsi": True,
                    "macd": False,
                    "kdj": False,
                },
                "fundamental": False,
            },
        )

        with self.assertRaises(ValidationError):
            StockAnalysisRequest(
                mode="manual",
                symbol="FPT",
                risk_appetite={"period": "short_term"},
                data_selection={
                    "news": True,
                    "technical": {
                        "ma": False,
                        "boll": False,
                        "rsi": False,
                        "macd": False,
                        "kdj": False,
                    },
                    "fundamental": True,
                },
            )

    def test_oversized_or_malformed_inputs_are_rejected(self):
        invalid_factories = [
            lambda: LoginRequest(email="a@example.com", password="x" * 129),
            lambda: VerifyOTPRequest(email="a@example.com", otp="12AB56"),
            lambda: ChatRequest(
                session_id="not-a-uuid", message="hello"
            ),
            lambda: ChatRequest(
                session_id="123e4567-e89b-42d3-a456-426614174000",
                message="x" * 4001,
            ),
            lambda: BacktestPipelineRequest(symbol="../User"),
            lambda: StockAnalysisRequest(
                mode="auto",
                symbol="FPT",
                language="fr",
                risk_appetite={"period": "short_term"},
            ),
        ]
        for factory in invalid_factories:
            with self.subTest(factory=factory), self.assertRaises(ValidationError):
                factory()

    def test_otp_is_not_stored_as_plaintext(self):
        digest = OTPService._otp_digest(
            "Admin@Example.com", "reset-password", "123456"
        )
        self.assertNotEqual("123456", digest)
        self.assertEqual(64, len(digest))


class AdminEndpointTests(unittest.TestCase):
    def test_unsafe_admin_login_endpoint_is_removed(self):
        auth_source = (
            Path(__file__).parents[1] / "app" / "routes" / "auth.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('"/admin-login"', auth_source)
        self.assertIn('"/admin-session"', auth_source)


if __name__ == "__main__":
    unittest.main()
