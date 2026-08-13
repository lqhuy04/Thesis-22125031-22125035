import unittest
from unittest.mock import patch

import pandas as pd

from app.services.market_service import MarketService


class MarketPricePageTests(unittest.TestCase):
    @staticmethod
    def _price_frame(periods: int, frequency: str = "1min") -> pd.DataFrame:
        index = pd.date_range(
            "2026-08-01T09:00:00+07:00",
            periods=periods,
            freq=frequency,
        )
        index.name = "trading_time"
        values = [100.0 + position / 100 for position in range(periods)]
        return pd.DataFrame(
            {
                "stock_id": ["stock-id"] * periods,
                "open": values,
                "high": [value + 1 for value in values],
                "low": [value - 1 for value in values],
                "close": [value + 0.5 for value in values],
                "volume": [1000 + position for position in range(periods)],
            },
            index=index,
        )

    def test_page_returns_100_candles_with_indicators_and_cursor(self):
        frame = self._price_frame(161, "15min")
        with (
            patch.object(MarketService, "_resolve_stock_id", return_value="stock-id"),
            patch.object(
                MarketService,
                "_fetch_raw_window",
                return_value=(frame, False),
            ) as fetch_window,
        ):
            result = MarketService.get_stock_price_page(
                "vnm",
                interval="15m",
                limit=100,
                before="2026-08-01T09:00:00+07:00",
            )

        self.assertEqual(len(result["candles"]), 100)
        self.assertTrue(result["hasMore"])
        self.assertEqual(
            result["nextCursor"],
            frame.index[-100].isoformat(),
        )
        self.assertIn("rsi_14", result["candles"][-1])
        self.assertIn("macd_histogram", result["candles"][-1])
        fetch_window.assert_called_once_with(
            "Stock_Price_1m",
            "stock-id",
            2415,
            before="2026-08-01T09:00:00+07:00",
        )

    def test_last_page_has_no_cursor(self):
        frame = self._price_frame(40, "1D")
        with (
            patch.object(MarketService, "_resolve_stock_id", return_value="stock-id"),
            patch.object(
                MarketService,
                "_fetch_raw_window",
                return_value=(frame, True),
            ),
        ):
            result = MarketService.get_stock_price_page(
                "VNM",
                interval="1d",
                limit=100,
            )

        self.assertEqual(len(result["candles"]), 40)
        self.assertFalse(result["hasMore"])
        self.assertIsNone(result["nextCursor"])
        self.assertNotIn("rsi_14", result["candles"][-1])

    def test_retry_handles_errno_35(self):
        attempts = 0

        def operation():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise OSError(35, "Resource temporarily unavailable")
            return "ok"

        with patch("app.services.market_service.time.sleep") as sleep:
            result = MarketService._execute_with_retry(operation)

        self.assertEqual(result, "ok")
        self.assertEqual(attempts, 3)
        self.assertEqual(sleep.call_count, 2)


if __name__ == "__main__":
    unittest.main()
