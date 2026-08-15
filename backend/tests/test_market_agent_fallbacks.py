import unittest

from agentic_ai.chatbot.agents.market_agent import (
    _fallback_news_sql_for_symbol,
    _fallback_sql_for_symbol,
    _fallback_technical_sql_for_symbol,
)
from agentic_ai.chatbot.sql_runner import TECHNICAL_MAX_ROWS


class MarketAgentFallbackTests(unittest.TestCase):
    def test_technical_fallback_uses_ohlcv_not_fundamentals(self):
        sql = _fallback_technical_sql_for_symbol("hpg")

        self.assertIn('FROM "Stock_Price_1d"', sql)
        self.assertIn("AS open", sql)
        self.assertIn("AS high", sql)
        self.assertIn("AS low", sql)
        self.assertIn("AS close", sql)
        self.assertIn("AS volume", sql)
        self.assertIn(f"LIMIT {TECHNICAL_MAX_ROWS}", sql)
        self.assertNotIn("FA_Summary", sql)

    def test_non_technical_fallback_remains_fundamental_summary(self):
        self.assertIn("FA_Summary", _fallback_sql_for_symbol("HPG"))

    def test_news_fallback_uses_safe_non_keyword_alias(self):
        sql = _fallback_news_sql_for_symbol("VNM")

        self.assertIn('JOIN "Article_Stock" AS article_stock', sql)
        self.assertIn("article_stock.article_id", sql)
        self.assertIn("article_stock.stock_id", sql)
        self.assertNotIn(" AS as ", sql)


if __name__ == "__main__":
    unittest.main()
