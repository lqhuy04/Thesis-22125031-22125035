import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from backfill_vn30_historical_articles import (
    ArchiveItem,
    ArticlePayload,
    ArticleRepository,
    backfill_symbol,
    in_requested_range,
    normalize_url,
    new_checkpoint,
    page_crossed_start,
    parse_archive_html,
)


class FakeFetcher:
    workers = 1

    def fetch_many(self, items):
        if items:
            raise AssertionError("test did not expect article body fetching")
        return {}


class HistoricalArticleCrawlerTests(unittest.TestCase):
    def test_monthly_limit_keeps_only_ten_newest_items(self):
        items = [
            ArchiveItem(
                f"item-{index}",
                f"https://cafef.vn/item-{index}.chn",
                datetime(2025, 6, 30 - index, 9, 0, tzinfo=timezone.utc),
            )
            for index in range(12)
        ]

        class FakeCafeF:
            def archive_page(self, symbol, page):
                return items

        class ReturningFetcher:
            workers = 4

            def fetch_many(self, requested):
                return {
                    item.url: ArticlePayload(
                        item.title, item.url, "", item.published_at, None, "content"
                    )
                    for item in requested
                }

        class NoopEnricher:
            def apply(self, payload, symbol, company_name):
                return payload

        repository = ArticleRepository(client=None, dry_run=True)
        checkpoint = new_checkpoint(date(2023, 1, 1), date(2025, 12, 31), ["HPG"], 10)
        stats, status = backfill_symbol(
            FakeCafeF(),
            ReturningFetcher(),
            repository,
            NoopEnricher(),
            {"id": "stock-id", "symbol": "HPG", "company_name": "Hoa Phat"},
            1,
            1,
            date(2023, 1, 1),
            date(2025, 12, 31),
            1,
            1,
            checkpoint,
            Path("unused.json"),
            20,
            10,
        )
        self.assertEqual(status, "limited")
        self.assertEqual(stats["inserted"], 10)
        self.assertEqual(stats["monthly_skipped"], 2)
        self.assertEqual(checkpoint["monthly_counts"]["HPG"]["2025-06"], 10)

    def test_repository_bulk_inserts_articles_and_links(self):
        class Response:
            def __init__(self, data):
                self.data = data

        class Query:
            def __init__(self, client, table):
                self.client = client
                self.table = table
                self.rows = None

            def insert(self, rows):
                self.rows = rows if isinstance(rows, list) else [rows]
                return self

            def execute(self):
                self.client.calls.append((self.table, self.rows))
                if self.table == "Article":
                    return Response(
                        [{**row, "id": f"new-{index}"} for index, row in enumerate(self.rows, 1)]
                    )
                return Response(self.rows)

        class FakeClient:
            def __init__(self):
                self.calls = []

            def table(self, name):
                return Query(self, name)

        def payload(name):
            return ArticlePayload(
                name,
                f"https://cafef.vn/{name}.chn",
                "description",
                datetime(2025, 1, 1, tzinfo=timezone.utc),
                None,
                "content",
            )

        client = FakeClient()
        repository = ArticleRepository(client)
        repository.article_by_url["https://cafef.vn/existing.chn"] = "existing-id"
        results = repository.save_batch(
            [(payload("first"), "stock-id"), (payload("second"), "stock-id"),
             (payload("existing"), "stock-id")]
        )
        self.assertEqual([inserted for _, inserted in results], [True, True, False])
        self.assertEqual([(table, len(rows)) for table, rows in client.calls],
                         [("Article", 2), ("Article_Stock", 3)])

    def test_parse_archive_html(self):
        html = """
        <ul class="News_Title_Link">
          <li><span class="timeTitle">31/12/2025 23:45</span>
              <a class="docnhanhTitle" href="/sample-story-123.chn?utm_source=x"> Sample title </a></li>
          <li>not an article</li>
        </ul>
        """
        items = parse_archive_html(html)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "Sample title")
        self.assertEqual(
            items[0].published_at,
            datetime(2025, 12, 31, 23, 45, tzinfo=timezone(timedelta(hours=7))),
        )
        self.assertEqual(items[0].url, "https://cafef.vn/sample-story-123.chn")

    def test_normalize_url(self):
        self.assertEqual(
            normalize_url("https://www.cafef.vn/a.chn?b=2&utm_campaign=x&a=1#section"),
            "https://cafef.vn/a.chn?a=1&b=2",
        )
        self.assertEqual(normalize_url("https://s.cafef.vn/a.chn"), "https://cafef.vn/a.chn")
        self.assertEqual(normalize_url("http://cafef.vn/a.chn"), "https://cafef.vn/a.chn")

    def test_range_and_stop_condition(self):
        items = [
            ArchiveItem("a", "https://cafef.vn/a", datetime(2023, 1, 2)),
            ArchiveItem("b", "https://cafef.vn/b", datetime(2022, 12, 31)),
        ]
        self.assertTrue(in_requested_range(items[0], date(2023, 1, 1), date(2025, 12, 31)))
        self.assertFalse(in_requested_range(items[1], date(2023, 1, 1), date(2025, 12, 31)))
        self.assertTrue(page_crossed_start(items, date(2023, 1, 1)))

    def test_page_limit_does_not_mark_symbol_complete(self):
        class FakeCafeF:
            def archive_page(self, symbol, page):
                return [ArchiveItem("future", "https://cafef.vn/future", datetime(2026, 1, 1, tzinfo=timezone.utc))]

        class FakeRepository:
            dry_run = True
            article_by_url = {}

            def monthly_counts(self, stock_id, start, end):
                return {}

        class FakeEnricher:
            pass

        checkpoint = {"pages": {}}
        stats, status = backfill_symbol(
            FakeCafeF(),
            FakeFetcher(),
            FakeRepository(),
            FakeEnricher(),
            {"id": "stock-id", "symbol": "HPG", "company_name": "Hoa Phat"},
            1,
            30,
            date(2023, 1, 1),
            date(2025, 12, 31),
            1,
            1,
            checkpoint,
            Path("unused.json"),
            20,
            10,
        )
        self.assertEqual(status, "limited")
        self.assertEqual(stats["discovered"], 0)
        self.assertEqual(checkpoint["pages"]["HPG"], 2)

    def test_pause_records_symbol_date_and_url_after_current_article(self):
        item = ArchiveItem(
            "historical",
            "https://cafef.vn/historical.chn",
            datetime(2025, 6, 1, 9, 30, tzinfo=timezone(timedelta(hours=7))),
        )

        class FakeCafeF:
            def archive_page(self, symbol, page):
                return [item]

        class FakePause:
            requested = False

        pause = FakePause()

        class FakeRepository:
            dry_run = True
            article_by_url = {item.url: "article-id"}

            def monthly_counts(self, stock_id, start, end):
                return {}

            def is_linked(self, url, stock_id):
                return False

            def save_batch(self, entries):
                pause.requested = True
                return [("article-id", False) for _ in entries]

        checkpoint = new_checkpoint(date(2023, 1, 1), date(2025, 12, 31), ["HPG"])
        _, status = backfill_symbol(
            FakeCafeF(),
            FakeFetcher(),
            FakeRepository(),
            object(),
            {"id": "stock-id", "symbol": "HPG", "company_name": "Hoa Phat"},
            1,
            1,
            date(2023, 1, 1),
            date(2025, 12, 31),
            1,
            None,
            checkpoint,
            Path("unused.json"),
            20,
            10,
            pause,
        )
        self.assertEqual(status, "paused")
        self.assertEqual(checkpoint["status"], "paused")
        self.assertEqual(checkpoint["current"]["symbol"], "HPG")
        self.assertEqual(checkpoint["current"]["last_article_date"], "2025-06-01T09:30:00+07:00")
        self.assertEqual(checkpoint["current"]["last_article_url"], item.url)
        self.assertEqual(checkpoint["current"]["page_processed_urls"], [item.url])

        class ResumeRepository:
            dry_run = True
            article_by_url = {item.url: "article-id"}

            def monthly_counts(self, stock_id, start, end):
                return {}

            def is_linked(self, url, stock_id):
                return False

            def save_batch(self, entries):
                raise AssertionError("saved URL should be skipped on resume")

        resumed_stats, resumed_status = backfill_symbol(
            FakeCafeF(),
            FakeFetcher(),
            ResumeRepository(),
            object(),
            {"id": "stock-id", "symbol": "HPG", "company_name": "Hoa Phat"},
            1,
            1,
            date(2023, 1, 1),
            date(2025, 12, 31),
            checkpoint["current"]["page"],
            1,
            checkpoint,
            Path("unused.json"),
            20,
            10,
        )
        self.assertEqual(resumed_status, "limited")
        self.assertEqual(resumed_stats["existing"], 1)
        self.assertEqual(checkpoint["pages"]["HPG"], 2)


if __name__ == "__main__":
    unittest.main()
