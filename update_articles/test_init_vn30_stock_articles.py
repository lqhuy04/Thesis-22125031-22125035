import json
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

import httpx

from init_vn30_stock_articles import (
    DeepSeekCreditsExhausted,
    DeepSeekError,
    DeepSeekStockEnricher,
    Runtime,
    SerperClient,
    SerperCreditsExhausted,
    StagingStore,
    SupabaseReviewImporter,
    endpoint_url,
    build_parser,
    deepseek_error_is_credit_exhaustion,
    load_checkpoint,
    month_windows,
    new_checkpoint,
    parse_serper_datetime,
    response_mentions_credit_exhaustion,
    save_checkpoint,
    run_backfill,
    trim_review_file,
    validated_current_vn30_symbols,
)


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)
        self.headers = {}

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


class VN30SerperBackfillTests(unittest.TestCase):
    def test_stale_dgc_mapping_is_removed_before_vn30_count_check(self):
        expected = {f"S{index:02}" for index in range(30)}
        symbols = validated_current_vn30_symbols(expected | {"DGC"})
        self.assertEqual(set(symbols), expected)
        self.assertEqual(len(symbols), 30)

    def test_unknown_31st_vn30_symbol_still_fails_safely(self):
        symbols = {f"S{index:02}" for index in range(31)}
        with self.assertRaises(RuntimeError):
            validated_current_vn30_symbols(symbols)

    def test_deepseek_is_the_default_enrichment_model(self):
        args = build_parser().parse_args([])
        self.assertEqual(args.model, "deepseek-v4-flash")

    def test_deepseek_enricher_requests_and_validates_json(self):
        class Completions:
            def __init__(self):
                self.request = None

            def create(self, **kwargs):
                self.request = kwargs
                message = type(
                    "Message",
                    (),
                    {
                        "content": json.dumps(
                            {
                                "sentiment": "positive",
                                "summary": "Kết quả kinh doanh tích cực.",
                            }
                        )
                    },
                )()
                choice = type("Choice", (), {"message": message})()
                return type("Response", (), {"choices": [choice]})()

        completions = Completions()
        enricher = object.__new__(DeepSeekStockEnricher)
        enricher.client = type(
            "Client",
            (),
            {
                "chat": type(
                    "Chat", (), {"completions": completions}
                )()
            },
        )()
        enricher.model = "deepseek-v4-flash"

        result = enricher.extract("HPG tăng trưởng", "Nội dung", "HPG", "Hòa Phát")
        self.assertEqual(result["sentiment"], "positive")
        self.assertEqual(
            completions.request["response_format"], {"type": "json_object"}
        )
        self.assertEqual(
            completions.request["extra_body"],
            {"thinking": {"type": "disabled"}},
        )

    def test_deepseek_insufficient_balance_pauses_instead_of_skipping(self):
        class InsufficientBalanceError(Exception):
            status_code = 402

        class Completions:
            def create(self, **_kwargs):
                raise InsufficientBalanceError("Insufficient balance")

        enricher = object.__new__(DeepSeekStockEnricher)
        enricher.client = type(
            "Client",
            (),
            {
                "chat": type(
                    "Chat", (), {"completions": Completions()}
                )()
            },
        )()
        enricher.model = "deepseek-v4-flash"

        with self.assertRaises(DeepSeekCreditsExhausted):
            enricher.extract("Title", "Content", "HPG", "Hòa Phát")

    def test_non_credit_deepseek_error_also_does_not_skip_article(self):
        class TemporaryError(Exception):
            status_code = 503

        class Completions:
            def create(self, **_kwargs):
                raise TemporaryError("Service overloaded")

        enricher = object.__new__(DeepSeekStockEnricher)
        enricher.client = type(
            "Client",
            (),
            {
                "chat": type(
                    "Chat", (), {"completions": Completions()}
                )()
            },
        )()
        enricher.model = "deepseek-v4-flash"

        with self.assertRaises(DeepSeekError):
            enricher.extract("Title", "Content", "HPG", "Hòa Phát")

    def test_deepseek_balance_detection_uses_status_and_message(self):
        status_error = type("Error", (Exception,), {"status_code": 402})()
        self.assertTrue(deepseek_error_is_credit_exhaustion(status_error))
        self.assertTrue(
            deepseek_error_is_credit_exhaustion(
                RuntimeError("Insufficient credit balance; please top up")
            )
        )
        self.assertFalse(
            deepseek_error_is_credit_exhaustion(
                RuntimeError("Rate limit reached")
            )
        )

    def test_deepseek_credit_pause_does_not_advance_current_item(self):
        class Staging:
            def has_pair(self, _link, _symbol):
                return False

            def article_for(self, _link):
                return None

            def count_for_window(self, _symbol, _start, _end):
                return 0

        class Enricher:
            def extract(self, *_args):
                raise DeepSeekCreditsExhausted("Insufficient balance")

        checkpoint = new_checkpoint(
            date(2024, 1, 1),
            date(2024, 1, 31),
            ["HPG"],
            1,
        )
        checkpoint["pending_page"] = {
            "symbol": "HPG",
            "window_start": "2024-01-01",
            "window_end": "2024-02-01",
            "page": 1,
            "fetched_at": "2024-01-31T12:00:00+07:00",
            "next_item_index": 0,
            "items": [
                {
                    "title": "HPG",
                    "link": "https://example.com/hpg",
                    "date": "Jan 15, 2024",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            runtime = Runtime(
                checkpoint_path=Path(directory) / "checkpoint.json",
                checkpoint=checkpoint,
                stocks=[
                    {
                        "id": 1,
                        "symbol": "HPG",
                        "company_name": "Hòa Phát",
                    }
                ],
                windows=[(date(2024, 1, 1), date(2024, 2, 1))],
                serper=object(),
                staging=Staging(),
                enricher=Enricher(),
                request_delay=0,
            )
            with patch(
                "init_vn30_stock_articles.extract_article_content",
                return_value={
                    "title": "HPG",
                    "content": "x" * 200,
                    "publish_date": None,
                    "top_image": None,
                },
            ):
                with self.assertRaises(DeepSeekCreditsExhausted):
                    run_backfill(runtime)
        self.assertEqual(
            checkpoint["pending_page"]["next_item_index"],
            0,
        )

    def test_month_advances_immediately_after_tenth_staged_article(self):
        class Enricher:
            def extract(self, *_args):
                return {"sentiment": "neutral", "summary": "Tóm tắt"}

        checkpoint = new_checkpoint(
            date(2024, 1, 1),
            date(2024, 1, 31),
            ["HPG"],
            10,
            10,
        )
        checkpoint["pending_page"] = {
            "symbol": "HPG",
            "window_start": "2024-01-01",
            "window_end": "2024-02-01",
            "page": 2,
            "fetched_at": "2024-01-31T12:00:00+07:00",
            "next_item_index": 0,
            "items": [
                {
                    "title": "Tenth",
                    "link": "https://example.com/tenth",
                    "date": "Jan 15, 2024",
                },
                {
                    "title": "Must not be processed",
                    "link": "https://example.com/eleventh",
                    "date": "Jan 16, 2024",
                },
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            review_path = Path(directory) / "review.jsonl"
            staging = StagingStore(review_path)
            for index in range(9):
                staging.append(
                    {
                        "title": f"Article {index}",
                        "link": f"https://example.com/{index}",
                        "time": f"2024-01-{index + 1:02}T09:00:00+07:00",
                        "content": "content",
                    },
                    "HPG",
                )
            runtime = Runtime(
                checkpoint_path=Path(directory) / "checkpoint.json",
                checkpoint=checkpoint,
                stocks=[
                    {
                        "id": 1,
                        "symbol": "HPG",
                        "company_name": "Hòa Phát",
                    }
                ],
                windows=[(date(2024, 1, 1), date(2024, 2, 1))],
                serper=object(),
                staging=staging,
                enricher=Enricher(),
                request_delay=0,
            )
            with patch(
                "init_vn30_stock_articles.extract_article_content",
                return_value={
                    "title": "Tenth",
                    "content": "x" * 200,
                    "publish_date": None,
                    "top_image": None,
                },
            ):
                run_backfill(runtime)

            self.assertEqual(staging.record_count, 10)
            self.assertFalse(
                staging.has_pair("https://example.com/eleventh", "HPG")
            )
        self.assertEqual(checkpoint["cursor"]["window_index"], 0)
        self.assertEqual(checkpoint["cursor"]["symbol_index"], 1)
        self.assertIsNone(checkpoint["pending_page"])

    def test_credit_exhaustion_detection(self):
        self.assertTrue(
            response_mentions_credit_exhaustion(
                403, '{"message":"Not enough credits"}'
            )
        )
        self.assertTrue(response_mentions_credit_exhaustion(402, ""))
        self.assertFalse(
            response_mentions_credit_exhaustion(403, '{"message":"Invalid API key"}')
        )
        self.assertFalse(response_mentions_credit_exhaustion(429, "rate limit"))

    def test_credit_error_inside_successful_json_is_detected(self):
        session = FakeSession(
            FakeResponse(200, {"error": "Insufficient credit balance"})
        )
        client = SerperClient(
            "https://google.serper.dev", "test", session=session
        )
        with self.assertRaises(SerperCreditsExhausted):
            client.search(
                "HPG", 1, date(2024, 1, 1), date(2024, 2, 1)
            )

    def test_serper_credit_error_is_not_returned_as_empty_results(self):
        session = FakeSession(
            FakeResponse(403, {"message": "Not enough credits"})
        )
        client = SerperClient(
            "https://google.serper.dev", "test", session=session
        )
        with self.assertRaises(SerperCreditsExhausted):
            client.search(
                "HPG", 3, date(2024, 1, 1), date(2024, 2, 1)
            )
        self.assertEqual(len(session.calls), 1)

    def test_serper_request_uses_custom_month_range(self):
        session = FakeSession(FakeResponse(200, {"news": []}))
        client = SerperClient(
            "https://google.serper.dev/news", "test", session=session
        )
        self.assertEqual(
            client.search("HPG", 2, date(2024, 2, 1), date(2024, 3, 1)),
            [],
        )
        url, request = session.calls[0]
        self.assertEqual(url, endpoint_url("https://google.serper.dev/news"))
        self.assertEqual(request["json"]["page"], 2)
        self.assertIn("after:2024-02-01", request["json"]["q"])
        self.assertIn("before:2024-03-01", request["json"]["q"])
        self.assertIn("cd_max:02/29/2024", request["json"]["tbs"])

    def test_month_windows_cover_partial_final_month(self):
        self.assertEqual(
            month_windows(date(2024, 1, 15), date(2024, 3, 2)),
            [
                (date(2024, 1, 15), date(2024, 2, 1)),
                (date(2024, 2, 1), date(2024, 3, 1)),
                (date(2024, 3, 1), date(2024, 3, 3)),
            ],
        )

    def test_checkpoint_round_trip_preserves_pending_page(self):
        checkpoint = new_checkpoint(
            date(2024, 1, 1), date(2024, 1, 31), ["HPG"], 10
        )
        checkpoint["cursor"]["page"] = 4
        checkpoint["pending_page"] = {
            "symbol": "HPG",
            "window_start": "2024-01-01",
            "window_end": "2024-02-01",
            "page": 4,
            "next_item_index": 2,
            "items": [{"link": "a"}, {"link": "b"}, {"link": "c"}],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.json"
            save_checkpoint(path, checkpoint)
            loaded = load_checkpoint(path)
        self.assertEqual(loaded["cursor"]["page"], 4)
        self.assertEqual(loaded["pending_page"]["next_item_index"], 2)
        self.assertEqual(len(loaded["pending_page"]["items"]), 3)

    def test_parses_common_serper_dates(self):
        self.assertEqual(
            parse_serper_datetime("29 thg 7, 2026").date(),
            date(2026, 7, 29),
        )
        now = datetime.fromisoformat("2026-07-29T12:00:00+07:00")
        self.assertEqual(
            parse_serper_datetime("2 ngày trước", now).date(),
            date(2026, 7, 27),
        )

    def test_jsonl_staging_is_durable_and_deduplicates_on_resume(self):
        article = {
            "title": "Sample",
            "link": "https://example.com/sample",
            "content": "content",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "review.jsonl"
            store = StagingStore(path)
            self.assertTrue(store.append(article, "HPG"))
            self.assertFalse(store.append(article, "HPG"))
            self.assertTrue(store.append(article, "FPT"))

            resumed = StagingStore(path)
            self.assertEqual(resumed.record_count, 2)
            self.assertTrue(resumed.has_pair(article["link"], "HPG"))
            self.assertTrue(resumed.has_pair(article["link"], "FPT"))
            self.assertFalse(resumed.append(article, "HPG"))

    def test_jsonl_staging_repairs_partial_last_write(self):
        article = {
            "title": "Sample",
            "link": "https://example.com/sample",
            "content": "content",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "review.jsonl"
            store = StagingStore(path)
            store.append(article, "HPG")
            with path.open("ab") as handle:
                handle.write(b'{"stock_symbol":"FPT","article":')

            resumed = StagingStore(path)
            self.assertEqual(resumed.record_count, 1)
            with path.open("rb") as handle:
                lines = handle.readlines()
            self.assertEqual(len(lines), 1)

    def test_trim_review_file_keeps_ten_per_symbol_month_and_makes_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "review.jsonl"
            store = StagingStore(path)
            for index in range(12):
                store.append(
                    {
                        "title": f"Article {index}",
                        "link": f"https://example.com/{index}",
                        "time": f"2024-01-{index + 1:02}T09:00:00+07:00",
                        "content": "content",
                    },
                    "HPG",
                )

            result = trim_review_file(path, 10)
            trimmed = StagingStore(path)
            self.assertEqual(result["removed"], 2)
            self.assertEqual(trimmed.record_count, 10)
            self.assertTrue(Path(result["backup"]).exists())
            self.assertEqual(
                StagingStore(Path(result["backup"])).record_count,
                12,
            )

    def test_review_importer_inserts_then_keeps_existing_idempotently(self):
        class Response:
            def __init__(self, data):
                self.data = data

        class Query:
            def __init__(self, client, table):
                self.client = client
                self.table = table
                self.filters = {}
                self.payload = None
                self.operation = "select"

            def select(self, _columns):
                return self

            def eq(self, key, value):
                self.filters[key] = value
                return self

            def limit(self, _value):
                return self

            def insert(self, payload):
                self.operation = "insert"
                self.payload = dict(payload)
                return self

            def update(self, payload):
                self.operation = "update"
                self.payload = dict(payload)
                return self

            def execute(self):
                rows = self.client.rows[self.table]
                if self.operation == "select":
                    matches = [
                        row
                        for row in rows
                        if all(row.get(k) == v for k, v in self.filters.items())
                    ]
                    return Response(matches)
                if self.operation == "insert":
                    row = dict(self.payload)
                    row.setdefault("id", len(rows) + 1)
                    rows.append(row)
                    return Response([row])
                for row in rows:
                    if all(row.get(k) == v for k, v in self.filters.items()):
                        row.update(self.payload)
                return Response([])

        class Client:
            def __init__(self):
                self.rows = {"Article": [], "Article_Stock": []}

            def table(self, name):
                return Query(self, name)

        client = Client()
        importer = SupabaseReviewImporter(client, {"HPG": 99})
        record = {
            "stock_symbol": "HPG",
            "article": {
                "title": "Before review",
                "link": "https://example.com/article",
                "content": "content",
                "article_type": "stock",
            },
        }
        self.assertEqual(importer.upsert(record), "inserted")
        record["article"]["title"] = "After review"
        self.assertEqual(importer.upsert(record), "existing")
        self.assertEqual(len(client.rows["Article"]), 1)
        self.assertEqual(client.rows["Article"][0]["title"], "Before review")
        self.assertEqual(len(client.rows["Article_Stock"]), 1)

    def test_link_retry_rechecks_after_lost_http2_response(self):
        class Response:
            def __init__(self, data):
                self.data = data

        class Query:
            def __init__(self, client, table):
                self.client = client
                self.table = table
                self.filters = {}
                self.operation = "select"
                self.payload = None

            def select(self, _columns):
                return self

            def eq(self, key, value):
                self.filters[key] = value
                return self

            def limit(self, _value):
                return self

            def insert(self, payload):
                self.operation = "insert"
                self.payload = dict(payload)
                return self

            def execute(self):
                rows = self.client.rows[self.table]
                if self.operation == "select":
                    return Response(
                        [
                            row
                            for row in rows
                            if all(
                                row.get(key) == value
                                for key, value in self.filters.items()
                            )
                        ]
                    )
                row = dict(self.payload)
                row["id"] = len(rows) + 1
                rows.append(row)
                if (
                    self.table == "Article_Stock"
                    and not self.client.dropped_once
                ):
                    self.client.dropped_once = True
                    raise httpx.RemoteProtocolError(
                        "ConnectionTerminated after commit"
                    )
                return Response([row])

        class Client:
            def __init__(self):
                self.rows = {
                    "Article": [
                        {
                            "id": 7,
                            "title": "Existing",
                            "link": "https://example.com/existing",
                        }
                    ],
                    "Article_Stock": [],
                }
                self.dropped_once = False

            def table(self, name):
                return Query(self, name)

        client = Client()
        importer = SupabaseReviewImporter(client, {"HPG": 99}, max_retries=3)
        record = {
            "stock_symbol": "HPG",
            "article": {
                "title": "Existing",
                "link": "https://example.com/existing",
                "content": "content",
            },
        }
        with patch("init_vn30_stock_articles.time.sleep"):
            self.assertEqual(importer.upsert(record), "existing")
        self.assertTrue(client.dropped_once)
        self.assertEqual(len(client.rows["Article_Stock"]), 1)

    def test_review_importer_bulk_inserts_fifty_records(self):
        class Response:
            def __init__(self, data):
                self.data = data

        class Query:
            def __init__(self, client, table):
                self.client = client
                self.table = table
                self.filters = {}
                self.operation = "select"
                self.payload = None

            def select(self, _columns):
                return self

            def in_(self, key, values):
                self.filters[key] = set(values)
                return self

            def insert(self, payload):
                self.operation = "insert"
                self.payload = payload if isinstance(payload, list) else [payload]
                return self

            def execute(self):
                rows = self.client.rows[self.table]
                if self.operation == "select":
                    matches = [
                        row
                        for row in rows
                        if all(
                            row.get(key) in values
                            for key, values in self.filters.items()
                        )
                    ]
                    return Response(matches)

                self.client.insert_calls.append(
                    (self.table, len(self.payload))
                )
                inserted = []
                for payload in self.payload:
                    row = dict(payload)
                    row.setdefault("id", len(rows) + 1)
                    rows.append(row)
                    inserted.append(row)
                return Response(inserted)

        class Client:
            def __init__(self):
                self.rows = {"Article": [], "Article_Stock": []}
                self.insert_calls = []

            def table(self, name):
                return Query(self, name)

        records = [
            {
                "stock_symbol": "HPG",
                "article": {
                    "title": f"Article {index}",
                    "link": f"https://example.com/batch-{index}",
                    "content": "content",
                },
            }
            for index in range(50)
        ]
        client = Client()
        importer = SupabaseReviewImporter(client, {"HPG": 99})
        outcomes = importer.upsert_batch(records)

        self.assertEqual(outcomes, {"inserted": 50, "existing": 0})
        self.assertEqual(
            client.insert_calls,
            [("Article", 50), ("Article_Stock", 50)],
        )
        self.assertEqual(len(client.rows["Article"]), 50)
        self.assertEqual(len(client.rows["Article_Stock"]), 50)


if __name__ == "__main__":
    unittest.main()
