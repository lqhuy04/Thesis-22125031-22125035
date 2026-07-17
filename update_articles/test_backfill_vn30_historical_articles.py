import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from backfill_vn30_historical_articles import (
    ArchiveItem,
    backfill_symbol,
    in_requested_range,
    normalize_url,
    new_checkpoint,
    page_crossed_start,
    parse_archive_html,
)


class HistoricalArticleCrawlerTests(unittest.TestCase):
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

        class FakeEnricher:
            pass

        checkpoint = {"pages": {}}
        stats, status = backfill_symbol(
            FakeCafeF(),
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

            def save(self, payload, stock_id):
                pause.requested = True
                return "article-id", False

        checkpoint = new_checkpoint(date(2023, 1, 1), date(2025, 12, 31), ["HPG"])
        _, status = backfill_symbol(
            FakeCafeF(),
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

            def save(self, payload, stock_id):
                raise AssertionError("saved URL should be skipped on resume")

        resumed_stats, resumed_status = backfill_symbol(
            FakeCafeF(),
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
        )
        self.assertEqual(resumed_status, "limited")
        self.assertEqual(resumed_stats["existing"], 1)
        self.assertEqual(checkpoint["pages"]["HPG"], 2)


if __name__ == "__main__":
    unittest.main()
