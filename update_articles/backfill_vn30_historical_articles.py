"""Backfill historical VN30 company news from CafeF into Supabase.

The CafeF company-event archive is ordered newest-first and can be paged back
many years.  This importer stops as soon as a page crosses ``--start-date``,
so it does not crawl older pages unnecessarily.  It is safe to resume and
deduplicates both Article rows (by normalized URL) and Article_Stock links.

Examples (run from the repository root):

    python update_articles/backfill_vn30_historical_articles.py --dry-run --symbols HPG
    python update_articles/backfill_vn30_historical_articles.py
    python update_articles/backfill_vn30_historical_articles.py --enrich
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import re
import signal
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from newspaper import Article, Config as NewspaperConfig
from pydantic import BaseModel, Field
from requests.adapters import HTTPAdapter
from supabase import Client, create_client
from urllib3.util.retry import Retry

from vn30_symbols import get_vn30_company_names, get_vn30_symbols


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_CHECKPOINT = SCRIPT_DIR / "vn30_historical_articles_checkpoint.json"

# Prefer already-exported variables, then the crawler .env, then backend/.env.
load_dotenv(SCRIPT_DIR / ".env", override=False)
load_dotenv(REPO_ROOT / "backend" / ".env", override=False)

CAFEF_BASE_URL = "https://cafef.vn"
CAFEF_ARCHIVE_URL = f"{CAFEF_BASE_URL}/du-lieu/Ajax/Events_RelatedNews_New.aspx"
DEFAULT_START = date(2023, 1, 1)
DEFAULT_END = date(2025, 12, 31)
PAGE_SIZE = 30  # CafeF currently caps the endpoint at 30 items.
VIETNAM_TZ = timezone(timedelta(hours=7))
TRACKING_QUERY_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("vn30_historical_news")
STAT_KEYS = ("discovered", "inserted", "existing", "failed", "pages_completed")


@dataclass(frozen=True)
class ArchiveItem:
    title: str
    url: str
    published_at: datetime


@dataclass
class ArticlePayload:
    title: str
    link: str
    description: str
    published_at: datetime
    thumbnail: Optional[str]
    content: str
    source: str = "cafef.vn"
    sentiment: str = "neutral"
    summary: str = ""


class StockExtraction(BaseModel):
    sentiment: str = Field(description="positive | neutral | negative")
    summary: str = Field(description="Vietnamese summary in 1-3 sentences")


class PauseController:
    """Turn the first Ctrl+C into a graceful pause request."""

    def __init__(self) -> None:
        self.requested = False
        self._interrupts = 0
        self._previous_handler: Any = None

    def install(self) -> None:
        self._previous_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self._handle)

    def restore(self) -> None:
        if self._previous_handler is not None:
            signal.signal(signal.SIGINT, self._previous_handler)

    def _handle(self, _signum: int, _frame: Any) -> None:
        self._interrupts += 1
        if self._interrupts == 1:
            self.requested = True
            logger.warning("Pause requested. Finishing the current article and saving progress...")
            return
        raise KeyboardInterrupt


def empty_stats() -> dict[str, int]:
    return {key: 0 for key in STAT_KEYS}


def new_checkpoint(start: date, end: date, symbols: list[str]) -> dict[str, Any]:
    return {
        "version": 2,
        "status": "running",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "symbols": symbols,
        "completed_symbols": [],
        "pages": {},
        "stats": {},
        "current": None,
        "updated_at": datetime.now(VIETNAM_TZ).isoformat(),
    }


def parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid date '{value}'; expected YYYY-MM-DD") from exc


def normalize_url(url: str) -> str:
    """Return a stable URL key without fragments or common tracking params."""
    absolute = urljoin(CAFEF_BASE_URL, (url or "").strip())
    parts = urlsplit(absolute)
    scheme = parts.scheme.lower() or "https"
    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if host in {"s.cafef.vn", "m.cafef.vn"}:
        host = "cafef.vn"
    if host == "cafef.vn":
        scheme = "https"
    path = re.sub(r"/{2,}", "/", parts.path).rstrip("/") or "/"
    query = urlencode(
        sorted((key, value) for key, value in parse_qsl(parts.query) if key.lower() not in TRACKING_QUERY_KEYS)
    )
    return urlunsplit((scheme, host, path, query, ""))


def parse_cafef_datetime(value: str) -> datetime:
    value = " ".join(value.split())
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=VIETNAM_TZ)
        except ValueError:
            continue
    raise ValueError(f"Unsupported CafeF date: {value!r}")


def parse_archive_html(html: str) -> list[ArchiveItem]:
    soup = BeautifulSoup(html, "html.parser")
    items: list[ArchiveItem] = []
    for row in soup.select("li"):
        time_node = row.select_one(".timeTitle")
        link_node = row.select_one("a[href]")
        if not time_node or not link_node:
            continue
        title = " ".join(link_node.get_text(" ", strip=True).split())
        href = str(link_node.get("href") or "").strip()
        if not title or not href:
            continue
        try:
            published_at = parse_cafef_datetime(time_node.get_text(" ", strip=True))
        except ValueError as exc:
            logger.warning("Skipping archive item with unknown date: %s", exc)
            continue
        items.append(ArchiveItem(title=title, url=normalize_url(href), published_at=published_at))
    return items


def in_requested_range(item: ArchiveItem, start: date, end: date) -> bool:
    return start <= item.published_at.date() <= end


def page_crossed_start(items: Iterable[ArchiveItem], start: date) -> bool:
    dates = [item.published_at.date() for item in items]
    return bool(dates) and min(dates) < start


def build_session() -> requests.Session:
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36 "
                "StockriumResearchCrawler/1.0"
            ),
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.7",
        }
    )
    return session


class CafeFClient:
    def __init__(self, delay_seconds: float = 1.0, session: Optional[requests.Session] = None):
        self.delay_seconds = max(0.0, delay_seconds)
        self.session = session or build_session()
        self._last_request_at = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        wait_for = self.delay_seconds - elapsed
        if wait_for > 0:
            time.sleep(wait_for + random.uniform(0, min(0.25, self.delay_seconds)))

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        self._throttle()
        response = self.session.get(url, timeout=30, **kwargs)
        self._last_request_at = time.monotonic()
        response.raise_for_status()
        return response

    def archive_page(self, symbol: str, page: int) -> list[ArchiveItem]:
        # The endpoint is case-sensitive. Keep this exact /Ajax/... spelling.
        response = self.get(
            CAFEF_ARCHIVE_URL,
            params={
                "symbol": symbol.lower(),
                "configID": 0,
                "PageIndex": page,
                "PageSize": PAGE_SIZE,
                "Type": 1,
            },
            headers={"Referer": f"{CAFEF_BASE_URL}/du-lieu/hose/{symbol.lower()}.chn"},
        )
        return parse_archive_html(response.text)

    def article(self, item: ArchiveItem) -> ArticlePayload:
        response = self.get(item.url, headers={"Referer": CAFEF_BASE_URL})
        config = NewspaperConfig()
        config.browser_user_agent = str(self.session.headers.get("User-Agent", ""))
        config.request_timeout = 30
        article = Article(item.url, language="vi", config=config)
        article.set_html(response.text)
        try:
            article.parse()
        except Exception as exc:
            logger.warning("Newspaper parse failed for %s: %s", item.url, exc)

        title = " ".join((article.title or item.title).split())
        content = (article.text or "").strip()
        description = " ".join((article.meta_description or "").split())
        if not description and content:
            description = content[:500].rsplit(" ", 1)[0]
        return ArticlePayload(
            title=title or item.title,
            link=normalize_url(item.url),
            description=description,
            published_at=item.published_at,
            thumbnail=article.top_image or None,
            content=content,
            summary=description,
        )


def paginated_rows(client: Client, table: str, columns: str, page_size: int = 1000) -> Iterable[dict]:
    offset = 0
    while True:
        response = client.table(table).select(columns).range(offset, offset + page_size - 1).execute()
        rows = response.data or []
        yield from rows
        if len(rows) < page_size:
            return
        offset += page_size


class ArticleRepository:
    def __init__(self, client: Client, dry_run: bool = False):
        self.client = client
        self.dry_run = dry_run
        self.article_by_url: dict[str, Any] = {}
        self.links: set[tuple[str, str]] = set()

    def warm_cache(self) -> None:
        logger.info("Loading existing article URLs and stock links from Supabase...")
        for row in paginated_rows(self.client, "Article", "id, link"):
            if row.get("id") is not None and row.get("link"):
                self.article_by_url[normalize_url(str(row["link"]))] = row["id"]
        for row in paginated_rows(self.client, "Article_Stock", "article_id, stock_id"):
            if row.get("article_id") is not None and row.get("stock_id") is not None:
                self.links.add((str(row["article_id"]), str(row["stock_id"])))
        logger.info("Cache: %d articles, %d article-stock links", len(self.article_by_url), len(self.links))

    def save(self, payload: ArticlePayload, stock_id: Any) -> tuple[str, bool]:
        key = normalize_url(payload.link)
        article_id = self.article_by_url.get(key)
        inserted = False

        if article_id is None:
            if self.dry_run:
                return "dry-run", True
            result = self.client.table("Article").insert(
                {
                    "title": payload.title,
                    "link": key,
                    "description": payload.description,
                    "time": payload.published_at.isoformat(),
                    "thumbnail": payload.thumbnail,
                    "source": payload.source,
                    "content": payload.content,
                    "sentiment": payload.sentiment,
                    "summary": payload.summary,
                    "article_type": "stock",
                }
            ).execute()
            if not result.data:
                raise RuntimeError(f"Supabase did not return the inserted Article for {key}")
            article_id = result.data[0]["id"]
            self.article_by_url[key] = article_id
            inserted = True

        pair = (str(article_id), str(stock_id))
        if pair not in self.links and not self.dry_run:
            self.client.table("Article_Stock").insert(
                {"article_id": article_id, "stock_id": stock_id}
            ).execute()
            self.links.add(pair)
        return str(article_id), inserted


class Enricher:
    def __init__(self, enabled: bool, model: str):
        self.enabled = enabled
        self.model = model
        self._client: Any = None
        if enabled:
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                raise RuntimeError("--enrich requires OPENAI_API_KEY")
            from openai import OpenAI

            self._client = OpenAI(api_key=api_key)

    def apply(self, payload: ArticlePayload, symbol: str, company_name: str) -> ArticlePayload:
        if not self.enabled:
            return payload
        text = payload.content[:12000] or payload.description
        response = self._client.beta.chat.completions.parse(
            model=self.model,
            temperature=0,
            response_format=StockExtraction,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Phân tích tin tài chính Việt Nam về {symbol} ({company_name}). "
                        "Gán sentiment positive, neutral hoặc negative theo tác động tới cổ phiếu, "
                        "và tóm tắt bằng tiếng Việt trong 1-3 câu. Không thêm dữ kiện ngoài bài."
                    ),
                },
                {"role": "user", "content": f"TIÊU ĐỀ:\n{payload.title}\n\nNỘI DUNG:\n{text}"},
            ],
        )
        parsed = response.choices[0].message.parsed
        if parsed:
            sentiment = (parsed.sentiment or "neutral").strip().lower()
            payload.sentiment = sentiment if sentiment in {"positive", "neutral", "negative"} else "neutral"
            payload.summary = (parsed.summary or payload.description).strip()
        return payload


def load_checkpoint(path: Path, start: date, end: date, symbols: list[str]) -> dict[str, Any]:
    expected = {"start_date": start.isoformat(), "end_date": end.isoformat(), "symbols": symbols}
    if path.exists():
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
            if all(state.get(key) == value for key, value in expected.items()):
                # Migrate page-only v1 checkpoints without losing their work.
                state.setdefault("version", 2)
                state.setdefault("status", "running")
                state.setdefault("completed_symbols", [])
                state.setdefault("pages", {})
                state.setdefault("stats", {})
                state.setdefault("current", None)
                return state
            logger.warning("Ignoring checkpoint because its date range or symbol list differs")
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Ignoring unreadable checkpoint %s: %s", path, exc)
    return new_checkpoint(start, end, symbols)


def save_checkpoint(path: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = datetime.now(VIETNAM_TZ).isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def checkpoint_totals(state: dict[str, Any]) -> dict[str, int]:
    totals = empty_stats()
    for symbol_stats in state.get("stats", {}).values():
        for key in STAT_KEYS:
            totals[key] += int(symbol_stats.get(key, 0))
    return totals


def show_checkpoint_status(path: Path) -> int:
    if not path.exists():
        print(f"No progress file found: {path}")
        return 1
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read progress file {path}: {exc}")
        return 1
    summary = {
        "status": state.get("status", "unknown"),
        "date_range": [state.get("start_date"), state.get("end_date")],
        "symbols_completed": len(state.get("completed_symbols", [])),
        "symbols_total": len(state.get("symbols", [])),
        "completed_symbols": state.get("completed_symbols", []),
        "current": state.get("current"),
        "totals": checkpoint_totals(state),
        "updated_at": state.get("updated_at"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def record_progress(
    checkpoint: dict[str, Any],
    symbol: str,
    symbol_position: int,
    symbol_total: int,
    page: int,
    item_index: int,
    items_on_page: int,
    item: Optional[ArchiveItem],
    processed_urls: set[str],
) -> None:
    previous = checkpoint.get("current") or {}
    same_symbol = previous.get("symbol") == symbol
    last_article_date = (
        item.published_at.isoformat()
        if item
        else previous.get("last_article_date") if same_symbol else None
    )
    last_article_url = (
        normalize_url(item.url)
        if item
        else previous.get("last_article_url") if same_symbol else None
    )
    checkpoint["status"] = "running"
    checkpoint["current"] = {
        "symbol": symbol,
        "symbol_position": symbol_position,
        "symbols_total": symbol_total,
        "page": page,
        "item_index": item_index,
        "items_on_page": items_on_page,
        "last_article_date": last_article_date,
        "last_article_url": last_article_url,
        "page_processed_urls": sorted(processed_urls),
    }


def log_progress(checkpoint: dict[str, Any], stats: dict[str, int]) -> None:
    current = checkpoint.get("current") or {}
    logger.info(
        "PROGRESS symbol %s (%s/%s) | page %s | item %s/%s | date %s | "
        "inserted %d | existing %d | completed symbols %d/%d",
        current.get("symbol", "-"),
        current.get("symbol_position", "-"),
        current.get("symbols_total", "-"),
        current.get("page", "-"),
        current.get("item_index", 0),
        current.get("items_on_page", 0),
        current.get("last_article_date", "-"),
        stats.get("inserted", 0),
        stats.get("existing", 0),
        len(checkpoint.get("completed_symbols", [])),
        len(checkpoint.get("symbols", [])),
    )


def resolve_stocks(client: Client, requested_symbols: Optional[list[str]]) -> list[dict[str, Any]]:
    vn30 = get_vn30_symbols(client)
    if not vn30:
        raise RuntimeError("No VN30 symbols found through MarketIndex/Stock_MarketIndex")
    if requested_symbols:
        requested = {symbol.strip().upper() for symbol in requested_symbols if symbol.strip()}
        invalid = sorted(requested - vn30)
        if invalid:
            raise ValueError(f"Symbols are not in the current VN30 database mapping: {', '.join(invalid)}")
        symbols = requested
    else:
        symbols = vn30

    names = get_vn30_company_names(client)
    result = client.table("Stock").select("id, stock_symbol").in_("stock_symbol", sorted(symbols)).execute()
    stocks = [
        {
            "id": row["id"],
            "symbol": str(row["stock_symbol"]).upper(),
            "company_name": names.get(str(row["stock_symbol"]).upper(), str(row["stock_symbol"]).upper()),
        }
        for row in (result.data or [])
        if row.get("id") is not None and row.get("stock_symbol")
    ]
    stocks.sort(key=lambda row: row["symbol"])
    if len(stocks) != len(symbols):
        found = {row["symbol"] for row in stocks}
        raise RuntimeError(f"Stock rows missing for: {', '.join(sorted(symbols - found))}")
    return stocks


def backfill_symbol(
    cafef: CafeFClient,
    repository: ArticleRepository,
    enricher: Enricher,
    stock: dict[str, Any],
    symbol_position: int,
    symbol_total: int,
    start: date,
    end: date,
    start_page: int,
    max_pages: Optional[int],
    checkpoint: dict[str, Any],
    checkpoint_path: Path,
    pause: Optional[PauseController] = None,
) -> tuple[dict[str, int], str]:
    symbol = stock["symbol"]
    stats = checkpoint.setdefault("stats", {}).setdefault(symbol, empty_stats())
    for key in STAT_KEYS:
        stats.setdefault(key, 0)
    page = start_page
    saved_current = checkpoint.get("current") or {}
    processed_urls = (
        set(saved_current.get("page_processed_urls", []))
        if saved_current.get("symbol") == symbol and int(saved_current.get("page", -1)) == page
        else set()
    )

    while max_pages is None or page <= max_pages:
        record_progress(
            checkpoint, symbol, symbol_position, symbol_total, page, 0, 0, None, processed_urls
        )
        if not repository.dry_run:
            save_checkpoint(checkpoint_path, checkpoint)
        if pause and pause.requested:
            checkpoint["status"] = "paused"
            if not repository.dry_run:
                save_checkpoint(checkpoint_path, checkpoint)
            return stats, "paused"

        logger.info("[%s] archive page %d", symbol, page)
        items = cafef.archive_page(symbol, page)
        if pause and pause.requested:
            checkpoint["status"] = "paused"
            if not repository.dry_run:
                save_checkpoint(checkpoint_path, checkpoint)
            return stats, "paused"
        if not items:
            logger.info("[%s] archive ended at page %d", symbol, page)
            return stats, "complete"

        selected = [item for item in items if in_requested_range(item, start, end)]
        for index, item in enumerate(selected, 1):
            key = normalize_url(item.url)
            if key in processed_urls:
                continue

            stats["discovered"] += 1
            existing_id = repository.article_by_url.get(key)
            payload = ArticlePayload(
                title=item.title,
                link=key,
                description="",
                published_at=item.published_at,
                thumbnail=None,
                content="",
            )
            if existing_id is None:
                logger.info("[%s p%d %d/%d] %s", symbol, page, index, len(selected), item.title[:90])
                try:
                    payload = cafef.article(item)
                except Exception as exc:
                    logger.warning("[%s] article body unavailable for %s: %s", symbol, item.url, exc)
                try:
                    payload = enricher.apply(payload, symbol, stock["company_name"])
                except Exception as exc:
                    logger.warning("[%s] enrichment failed for %s: %s", symbol, item.url, exc)
            try:
                _, inserted = repository.save(payload, stock["id"])
                stats["inserted" if inserted else "existing"] += 1
            except Exception as exc:
                stats["failed"] += 1
                logger.exception("[%s] failed article %s: %s", symbol, item.url, exc)
                record_progress(
                    checkpoint,
                    symbol,
                    symbol_position,
                    symbol_total,
                    page,
                    index,
                    len(selected),
                    item,
                    processed_urls,
                )
                checkpoint["status"] = "failed"
                if not repository.dry_run:
                    save_checkpoint(checkpoint_path, checkpoint)
                return stats, "failed"

            processed_urls.add(key)
            record_progress(
                checkpoint,
                symbol,
                symbol_position,
                symbol_total,
                page,
                index,
                len(selected),
                item,
                processed_urls,
            )
            if not repository.dry_run:
                save_checkpoint(checkpoint_path, checkpoint)
            log_progress(checkpoint, stats)
            if pause and pause.requested:
                checkpoint["status"] = "paused"
                if not repository.dry_run:
                    save_checkpoint(checkpoint_path, checkpoint)
                return stats, "paused"

        stats["pages_completed"] += 1
        checkpoint["pages"][symbol] = page + 1
        processed_urls = set()
        record_progress(
            checkpoint, symbol, symbol_position, symbol_total, page + 1, 0, 0, None, processed_urls
        )
        if not repository.dry_run:
            save_checkpoint(checkpoint_path, checkpoint)
        if page_crossed_start(items, start):
            return stats, "complete"
        page += 1
    if max_pages is not None and page > max_pages:
        logger.info("[%s] stopped at --max-pages=%d; symbol remains resumable", symbol, max_pages)
    return stats, "limited"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", type=parse_iso_date, default=DEFAULT_START)
    parser.add_argument("--end-date", type=parse_iso_date, default=DEFAULT_END)
    parser.add_argument("--symbols", nargs="+", help="Optional current-VN30 subset, e.g. HPG FPT VNM")
    parser.add_argument("--delay", type=float, default=1.0, help="Minimum seconds between CafeF requests")
    parser.add_argument("--max-pages", type=int, help="Safety/debug limit per symbol")
    parser.add_argument("--dry-run", action="store_true", help="Crawl and report without writing Supabase")
    parser.add_argument("--enrich", action="store_true", help="Generate sentiment/summary with OpenAI")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model used with --enrich")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--no-resume", action="store_true", help="Ignore a matching checkpoint")
    parser.add_argument("--status", action="store_true", help="Show saved progress without crawling or DB access")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.status:
        return show_checkpoint_status(args.checkpoint)
    if args.start_date > args.end_date:
        raise SystemExit("--start-date must be on or before --end-date")
    if args.delay < 0:
        raise SystemExit("--delay must be >= 0")
    if args.max_pages is not None and args.max_pages < 1:
        raise SystemExit("--max-pages must be >= 1")

    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_key = os.getenv("SUPABASE_KEY", "").strip()
    if not supabase_url or not supabase_key:
        raise SystemExit("SUPABASE_URL and SUPABASE_KEY are required (backend/.env is loaded automatically)")

    client = create_client(supabase_url, supabase_key)
    stocks = resolve_stocks(client, args.symbols)
    symbols = [stock["symbol"] for stock in stocks]
    checkpoint = (
        new_checkpoint(args.start_date, args.end_date, symbols)
        if args.no_resume or args.dry_run
        else load_checkpoint(args.checkpoint, args.start_date, args.end_date, symbols)
    )

    repository = ArticleRepository(client, dry_run=args.dry_run)
    repository.warm_cache()
    cafef = CafeFClient(delay_seconds=args.delay)
    enricher = Enricher(enabled=args.enrich, model=args.model)
    completed = set(checkpoint.get("completed_symbols", []))
    saved_current = checkpoint.get("current") or {}
    if saved_current:
        logger.info(
            "Resuming saved progress: symbol %s (%s/%s), page %s, item %s/%s, date %s",
            saved_current.get("symbol"),
            saved_current.get("symbol_position"),
            saved_current.get("symbols_total"),
            saved_current.get("page"),
            saved_current.get("item_index"),
            saved_current.get("items_on_page"),
            saved_current.get("last_article_date"),
        )

    logger.info(
        "Backfill %s through %s for %d current VN30 symbols%s",
        args.start_date,
        args.end_date,
        len(stocks),
        " (DRY RUN)" if args.dry_run else "",
    )
    pause = PauseController()
    pause.install()
    final_status = "running"
    try:
        for position, stock in enumerate(stocks, 1):
            symbol = stock["symbol"]
            if symbol in completed:
                logger.info("[%d/%d] %s already completed", position, len(stocks), symbol)
                continue
            current = checkpoint.get("current") or {}
            if current.get("symbol") == symbol:
                start_page = int(current.get("page") or checkpoint.get("pages", {}).get(symbol, 1))
            else:
                start_page = int(checkpoint.get("pages", {}).get(symbol, 1))
            logger.info("[%d/%d] Starting %s from page %d", position, len(stocks), symbol, start_page)
            stats, symbol_status = backfill_symbol(
                cafef,
                repository,
                enricher,
                stock,
                position,
                len(stocks),
                args.start_date,
                args.end_date,
                start_page,
                args.max_pages,
                checkpoint,
                args.checkpoint,
                pause,
            )
            logger.info("[%s] status=%s stats=%s", symbol, symbol_status, stats)
            final_status = symbol_status
            if symbol_status == "complete":
                completed.add(symbol)
                checkpoint["completed_symbols"] = sorted(completed)
                checkpoint["pages"].pop(symbol, None)
                checkpoint["current"] = None
                if not args.dry_run:
                    save_checkpoint(args.checkpoint, checkpoint)
            elif symbol_status in {"paused", "failed"}:
                break
    finally:
        pause.restore()

    totals = checkpoint_totals(checkpoint)
    if len(completed) == len(stocks):
        checkpoint["status"] = "completed"
        checkpoint["current"] = None
        checkpoint["finished_at"] = datetime.now(VIETNAM_TZ).isoformat()
        final_status = "completed"
    elif final_status == "limited":
        checkpoint["status"] = "partial"
    if not args.dry_run:
        save_checkpoint(args.checkpoint, checkpoint)

    logger.info("Run status=%s totals=%s", final_status, totals)
    if final_status == "paused":
        logger.warning("Paused safely. Run the same command again to resume.")
        return 130
    if final_status == "failed":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
