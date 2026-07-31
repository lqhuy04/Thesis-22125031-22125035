import unittest

import pandas as pd

from app.backtest.visualizer import get_backtest_visualization_data


class BacktestVisualizerConfigurationTests(unittest.TestCase):
    def test_includes_configuration_bollinger_and_kdj_series(self):
        frame = pd.DataFrame(
            {
                "datetime": pd.to_datetime(["2024-01-02", "2024-01-03"]),
                "open": [100.0, 101.0],
                "high": [102.0, 103.0],
                "low": [99.0, 100.0],
                "close": [101.0, 102.0],
                "volume": [1_000, 1_100],
                "bb_upper": [110.0, 111.0],
                "bb_middle": [101.0, 102.0],
                "bb_lower": [92.0, 93.0],
                "kdj_k": [45.0, 48.0],
                "kdj_d": [42.0, 44.0],
                "kdj_j": [51.0, 56.0],
            }
        )
        configuration = {
            "mode": "manual",
            "period": "mid_term",
            "interval": "1d",
            "data_sources": ["technical"],
            "selected_indicators": ["boll", "kdj"],
        }

        output = get_backtest_visualization_data(
            df=frame,
            trades=[],
            metrics={},
            symbol="FPT",
            configuration=configuration,
        )

        self.assertEqual(output["configuration"], configuration)
        self.assertEqual(len(output["bb_upper_data"]), 2)
        self.assertEqual(len(output["bb_middle_data"]), 2)
        self.assertEqual(len(output["bb_lower_data"]), 2)
        self.assertEqual(len(output["kdj_k_data"]), 2)
        self.assertEqual(len(output["kdj_d_data"]), 2)
        self.assertEqual(len(output["kdj_j_data"]), 2)


if __name__ == "__main__":
    unittest.main()
