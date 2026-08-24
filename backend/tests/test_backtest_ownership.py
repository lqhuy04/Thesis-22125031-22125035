import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.models.backtest_pipeline_schemas import BacktestPipelineRequest
from app.services.backtest_pipeline_service import run_backtest_pipeline
from app.utils.supabase_storage import (
    download_backtest_file,
    list_backtest_files,
    upload_backtest_file,
)
from app.utils.user_namespace import user_namespace


class _BucketStub:
    def __init__(self):
        self.upload_args = None
        self.list_path = None
        self.download_path = None

    def upload(self, **kwargs):
        self.upload_args = kwargs

    def list(self, path):
        self.list_path = path
        return [
            {
                "name": "FPT_20260824_120000_000001_backtest.json",
                "created_at": "2026-08-24T12:00:00Z",
            }
        ]

    def download(self, path):
        self.download_path = path
        return b"owned-backtest"


class _StorageStub:
    def __init__(self, bucket):
        self.bucket = bucket
        self.bucket_name = None

    def from_(self, bucket_name):
        self.bucket_name = bucket_name
        return self.bucket


class _ClientStub:
    def __init__(self, bucket):
        self.storage = _StorageStub(bucket)


class BacktestOwnershipTests(unittest.TestCase):
    def test_user_namespace_rejects_path_traversal(self):
        self.assertEqual(user_namespace("user-123"), "user-123")
        for invalid in ("", "../other-user", "user/other", "user other"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                user_namespace(invalid)

    def test_storage_operations_are_scoped_to_authenticated_user(self):
        bucket = _BucketStub()
        client = _ClientStub(bucket)
        filename = "FPT_20260824_120000_000001_backtest.json"

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / filename
            file_path.write_bytes(b"{}")

            with patch(
                "app.utils.supabase_storage.get_supabase_client",
                return_value=client,
            ):
                protected_url = upload_backtest_file(
                    "user-123",
                    str(file_path),
                    filename,
                    "application/json",
                )
                files = list_backtest_files("user-123")
                content = download_backtest_file("user-123", filename)

        self.assertEqual(
            bucket.upload_args["path"],
            f"user-123/{filename}",
        )
        self.assertEqual(bucket.list_path, "user-123")
        self.assertEqual(bucket.download_path, f"user-123/{filename}")
        self.assertNotIn("user-123", protected_url)
        self.assertEqual(files[0]["json_url"], protected_url)
        self.assertEqual(content, b"owned-backtest")

    @patch("app.services.backtest_pipeline_service.run_full_backtest")
    @patch("app.services.backtest_pipeline_service._build_market_dataframe")
    @patch("app.services.backtest_pipeline_service._build_dataframe")
    def test_pipeline_propagates_authenticated_user_to_backtest(
        self,
        build_dataframe,
        build_market_dataframe,
        run_full_backtest,
    ):
        build_dataframe.return_value = object()
        build_market_dataframe.return_value = object()
        run_full_backtest.return_value = {"result": "ok"}

        result = run_backtest_pipeline(
            BacktestPipelineRequest(symbol="FPT"),
            user_id="user-123",
        )

        self.assertEqual(result, {"result": "ok"})
        self.assertEqual(
            run_full_backtest.call_args.kwargs["owner_user_id"],
            "user-123",
        )


if __name__ == "__main__":
    unittest.main()
