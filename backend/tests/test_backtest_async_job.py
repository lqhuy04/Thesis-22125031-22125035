import json
import unittest
from unittest.mock import patch

from fastapi import BackgroundTasks

from app.models.backtest_pipeline_schemas import BacktestPipelineRequest
from app.routes.agentic import _run_backtest_job, backtest_pipeline


class BacktestAsyncJobTests(unittest.TestCase):
    def test_submission_returns_202_and_schedules_background_job(self):
        tasks = BackgroundTasks()
        with patch(
            "app.routes.agentic.ExperimentService.create",
            return_value={"id": "experiment-1"},
        ):
            response = backtest_pipeline(
                body=BacktestPipelineRequest(symbol="fpt"),
                background_tasks=tasks,
                current_user={"user_id": "user-1"},
                _rate_limit=None,
            )

        payload = json.loads(response.body)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(payload["data"]["experiment_id"], "experiment-1")
        self.assertEqual(payload["data"]["status"], "running")
        self.assertEqual(payload["data"]["symbol"], "FPT")
        self.assertEqual(len(tasks.tasks), 1)

    def test_background_job_completes_persisted_experiment(self):
        result = {
            "full_metrics": {
                "pnl": {"total_return": 0.12},
                "volume": {"win_rate": 0.5, "n_trades": 6},
                "risk": {"sharpe_ratio": 0.15, "max_drawdown": -0.2},
            },
            "visualization_file": "/api/agentic/backtests/local/result.json",
            "visualization_data_url": "/api/agentic/backtests/files/result.json",
        }
        with (
            patch("app.routes.agentic.run_backtest_pipeline", return_value=result),
            patch("app.routes.agentic.ExperimentService.complete") as complete,
            patch("app.routes.agentic._fail_experiment_safely") as fail,
        ):
            _run_backtest_job(
                experiment_id="experiment-1",
                user_id="user-1",
                body=BacktestPipelineRequest(symbol="fpt"),
            )

        fail.assert_not_called()
        complete.assert_called_once()
        kwargs = complete.call_args.kwargs
        self.assertEqual(kwargs["experiment_id"], "experiment-1")
        self.assertEqual(kwargs["user_id"], "user-1")
        self.assertEqual(kwargs["result_summary"]["net_profit"], 0.12)
        self.assertEqual(
            kwargs["result_reference"],
            "/api/agentic/backtests/files/result.json",
        )

    def test_background_job_marks_experiment_failed(self):
        error = RuntimeError("provider timeout")
        with (
            patch("app.routes.agentic.run_backtest_pipeline", side_effect=error),
            patch("app.routes.agentic.ExperimentService.complete") as complete,
            patch("app.routes.agentic._fail_experiment_safely") as fail,
            patch("app.routes.agentic.logger.exception"),
        ):
            _run_backtest_job(
                experiment_id="experiment-1",
                user_id="user-1",
                body=BacktestPipelineRequest(symbol="FPT"),
            )

        complete.assert_not_called()
        fail.assert_called_once_with("experiment-1", "user-1", error)


if __name__ == "__main__":
    unittest.main()
