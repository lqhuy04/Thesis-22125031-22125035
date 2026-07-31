import unittest

import pandas as pd

from app.backtest.engine import TradeSimulator


class TradeSimulatorMaxHoldTests(unittest.TestCase):
    @staticmethod
    def _frame(total_scores: list[float]) -> pd.DataFrame:
        size = len(total_scores)
        return pd.DataFrame(
            {
                "datetime": pd.date_range("2026-01-01", periods=size),
                "open": [100.0] * size,
                "high": [101.0] * size,
                "low": [99.0] * size,
                "close": [100.0] * size,
                "total_score": total_scores,
                "signal": ["BUY", *([None] * (size - 1))],
            }
        )

    def test_max_hold_includes_entry_candle(self):
        frame = self._frame([3.0] * 6)
        frame["max_hold_candles_override"] = [2, None, None, None, None, None]

        trade = TradeSimulator(
            max_hold_candles=20,
            transaction_cost_pct=0.0,
        ).run(frame)[0]

        self.assertEqual(trade["entry_date"], "2026-01-02 00:00:00")
        self.assertEqual(trade["exit_date"], "2026-01-03 00:00:00")
        self.assertEqual(trade["hold_candles"], 2)
        self.assertEqual(trade["exit_reason"], "TIMEOUT")

    def test_score_exit_cannot_exceed_max_hold(self):
        frame = self._frame([3.0, 3.0, 2.0, 2.0, 2.0])
        frame["max_hold_candles_override"] = [2, None, None, None, None]

        trade = TradeSimulator(
            max_hold_candles=20,
            exit_on_score_drop=True,
            transaction_cost_pct=0.0,
        ).run(frame)[0]

        self.assertEqual(trade["exit_date"], "2026-01-03 00:00:00")
        self.assertEqual(trade["hold_candles"], 2)
        self.assertEqual(trade["exit_reason"], "TIMEOUT")


class TradeSimulatorEntryGapTests(unittest.TestCase):
    @staticmethod
    def _frame(next_open: float) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "datetime": pd.date_range("2026-01-01", periods=4),
                "open": [100.0, next_open, next_open, next_open],
                "high": [101.0, next_open + 1, next_open + 1, next_open + 1],
                "low": [99.0, next_open - 1, next_open - 1, next_open - 1],
                "close": [100.0, next_open, next_open, next_open],
                "total_score": [3.0] * 4,
                "signal": ["BUY", None, None, None],
                "take_profit_price": [120.0, None, None, None],
                "stop_loss_price": [90.0, None, None, None],
                "max_hold_candles_override": [2, None, None, None],
            }
        )

    def test_trade_is_skipped_when_next_open_is_above_take_profit(self):
        trades = TradeSimulator(
            max_hold_candles=20,
            transaction_cost_pct=0.0,
        ).run(self._frame(next_open=125.0))

        self.assertEqual(trades, [])

    def test_trade_is_skipped_when_next_open_is_below_stop_loss(self):
        trades = TradeSimulator(
            max_hold_candles=20,
            transaction_cost_pct=0.0,
        ).run(self._frame(next_open=85.0))

        self.assertEqual(trades, [])

    def test_trade_keeps_pipeline_plan_when_next_open_is_inside_bounds(self):
        trade = TradeSimulator(
            max_hold_candles=20,
            transaction_cost_pct=0.0,
        ).run(self._frame(next_open=100.0))[0]

        self.assertEqual(trade["entry_price"], 100.0)
        self.assertEqual(trade["take_profit"], 120.0)
        self.assertEqual(trade["stop_loss"], 90.0)


if __name__ == "__main__":
    unittest.main()
