import unittest
from pathlib import Path

from pydantic import ValidationError

from agentic_ai.chatbot.sql_runner import UnsafeSQLError, sanitize_sql
from app.models.agentic_schemas import ChatRequest, StockAnalysisRequest
from app.models.auth_schemas import LoginRequest, VerifyOTPRequest
from app.models.backtest_pipeline_schemas import BacktestPipelineRequest
from app.utils.otp import OTPService


class SQLGuardTests(unittest.TestCase):
    def test_expected_market_queries_are_allowed_and_capped(self):
        guarded = sanitize_sql('SELECT "stock_symbol" FROM "Stock"')
        self.assertIn("LIMIT 100", guarded)
        sanitize_sql(
            'SELECT COUNT(*) AS total, MAX("stock_symbol") FROM "Stock" LIMIT 50'
        )
        sanitize_sql(
            'WITH prices AS (SELECT * FROM "Current_Stock_Price" LIMIT 10) '
            "SELECT COUNT(*) FROM prices"
        )

    def test_dangerous_queries_are_rejected(self):
        queries = [
            'SELECT pg_read_file(\'/etc/passwd\') FROM "Stock"',
            'SELECT current_setting(\'server_version\') FROM "Stock"',
            'SELECT pg_sleep(1) FROM "Stock"',
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
        StockAnalysisRequest(
            mode="auto",
            symbol="FPT",
            risk_appetite={"period": "short_term"},
        )
        ChatRequest(
            session_id="123e4567-e89b-42d3-a456-426614174000",
            message="Phân tích FPT",
        )
        BacktestPipelineRequest(symbol="FPT")

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
