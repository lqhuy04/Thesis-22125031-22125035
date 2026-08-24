import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from pydantic import ValidationError

from app.models.experiment_schemas import ExperimentComparisonRequest
from app.models.experiment_schemas import ExperimentStatus, ExperimentType
from app.services.experiment_service import ExperimentService


class _ResultStub:
    def __init__(self, *, row=None, rows=None):
        self.row = row
        self.rows = rows or []

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class _ConnectionStub:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))
        return self.results.pop(0)


class _ConnectionContext:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class _PoolStub:
    def __init__(self, connection):
        self._connection = connection

    def connection(self):
        return _ConnectionContext(self._connection)


def _list_row(
    user_id="user-a",
    experiment_id="00000000-0000-0000-0000-000000000001",
):
    now = datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc)
    return (
        experiment_id,
        user_id,
        "Backtest · FPT",
        "backtest",
        "completed",
        "single",
        "FPT",
        "auto",
        {"symbol": "FPT"},
        {"net_profit": 0.12},
        "protected-result-url",
        None,
        now,
        now,
        now,
        1250,
    )


def _detail_row(
    user_id="user-a",
    experiment_id="00000000-0000-0000-0000-000000000001",
):
    row = list(_list_row(user_id, experiment_id))
    row.insert(9, {
        "schema_version": "1.0",
        "configuration_sha256": "config-hash",
    })
    row.insert(11, {"full_metrics": {"pnl": {"total_return": 0.12}}})
    return tuple(row)


class ExperimentServiceTests(unittest.TestCase):
    def setUp(self):
        self.previous_table_ready = ExperimentService._table_ready
        ExperimentService._table_ready = True

    def tearDown(self):
        ExperimentService._table_ready = self.previous_table_ready

    def test_list_is_always_scoped_to_authenticated_user(self):
        connection = _ConnectionStub([_ResultStub(rows=[_list_row()])])
        with patch(
            "app.services.experiment_service.get_pool",
            return_value=_PoolStub(connection),
        ):
            items = ExperimentService.list_for_user(
                user_id="user-a",
                experiment_type=ExperimentType.BACKTEST,
                status=ExperimentStatus.COMPLETED,
                limit=25,
                offset=5,
            )

        query, params = connection.calls[0]
        self.assertIn("WHERE user_id = %s", query)
        self.assertIn("experiment_type = %s", query)
        self.assertIn("status = %s", query)
        self.assertEqual(params, ("user-a", "backtest", "completed", 25, 5))
        self.assertEqual(items[0]["user_id"], "user-a")
        self.assertEqual(items[0]["created_at"], "2026-08-24T12:00:00+00:00")
        self.assertNotIn("result_data", items[0])

    def test_detail_cannot_be_loaded_without_matching_owner(self):
        connection = _ConnectionStub([_ResultStub(row=None)])
        with patch(
            "app.services.experiment_service.get_pool",
            return_value=_PoolStub(connection),
        ):
            result = ExperimentService.get_for_user(
                experiment_id="00000000-0000-0000-0000-000000000001",
                user_id="user-b",
            )

        query, params = connection.calls[0]
        self.assertIn("WHERE id = %s AND user_id = %s", query)
        self.assertEqual(
            params,
            ("00000000-0000-0000-0000-000000000001", "user-b"),
        )
        self.assertIsNone(result)

    def test_completion_update_requires_matching_owner(self):
        connection = _ConnectionStub([_ResultStub(row=_detail_row())])
        with patch(
            "app.services.experiment_service.get_pool",
            return_value=_PoolStub(connection),
        ):
            result = ExperimentService.complete(
                experiment_id="00000000-0000-0000-0000-000000000001",
                user_id="user-a",
                result_summary={"net_profit": 0.12},
                result_data={"metrics": {}},
                result_reference="protected-result-url",
            )

        query, params = connection.calls[0]
        self.assertIn("WHERE id = %s AND user_id = %s", query)
        self.assertEqual(
            params[-2:],
            ("00000000-0000-0000-0000-000000000001", "user-a"),
        )
        self.assertEqual(result["result_data"]["full_metrics"]["pnl"]["total_return"], 0.12)
        self.assertEqual(result["reproducibility"]["schema_version"], "1.0")

    def test_comparison_loads_only_owned_rows_in_requested_order(self):
        first_id = "00000000-0000-0000-0000-000000000001"
        second_id = "00000000-0000-0000-0000-000000000002"
        connection = _ConnectionStub([
            _ResultStub(rows=[
                _detail_row(experiment_id=second_id),
                _detail_row(experiment_id=first_id),
            ])
        ])
        with patch(
            "app.services.experiment_service.get_pool",
            return_value=_PoolStub(connection),
        ):
            items = ExperimentService.get_many_for_user(
                experiment_ids=[first_id, second_id],
                user_id="user-a",
            )

        query, params = connection.calls[0]
        self.assertIn("WHERE user_id = %s AND id IN (%s, %s)", query)
        self.assertEqual(params, ("user-a", first_id, second_id))
        self.assertEqual([item["id"] for item in items], [first_id, second_id])

    def test_comparison_request_rejects_duplicate_or_invalid_counts(self):
        first_id = "00000000-0000-0000-0000-000000000001"
        second_id = "00000000-0000-0000-0000-000000000002"
        valid = ExperimentComparisonRequest(experiment_ids=[first_id, second_id])
        self.assertEqual(len(valid.experiment_ids), 2)

        for invalid_ids in ([first_id], [first_id, first_id]):
            with self.subTest(invalid_ids=invalid_ids), self.assertRaises(ValidationError):
                ExperimentComparisonRequest(experiment_ids=invalid_ids)


if __name__ == "__main__":
    unittest.main()
