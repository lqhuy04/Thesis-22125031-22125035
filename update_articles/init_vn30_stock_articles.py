"""
Collect current VN30 stock news from 2024-01-01 through today with Serper.

The crawl is split into calendar-month windows so that older results are not
hidden behind Google's result limit. Progress is written atomically after each
successful Serper response and after every processed article. If Serper runs
out of credits, the script pauses without advancing the cursor; running the
same command later resumes from that exact request.

Crawling never writes articles to Supabase. Reviewable records are appended to
a JSONL file first. Only the explicit --import-reviewed command upserts those
records and their Article_Stock links after review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import httpx
import requests
from dotenv import load_dotenv
from newspaper import Article
from openai import OpenAI
from pydantic import BaseModel, Field
from supabase import create_client

from vn30_symbols import get_vn30_symbols


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CHECKPOINT = SCRIPT_DIR / "init_vn30_stock_articles_checkpoint.json"
DEFAULT_OUTPUT = SCRIPT_DIR / "vn30_stock_articles_review.jsonl"
DEFAULT_IMPORT_CHECKPOINT = (
    SCRIPT_DIR / "vn30_stock_articles_import_checkpoint.json"
)
DEFAULT_START_DATE = date(2024, 1, 1)
VN_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")
ARTICLE_TABLE = "Article"
STOCK_TABLE = "Stock"
ARTICLE_STOCK_TABLE = "Article_Stock"
CHECKPOINT_VERSION = 3
# HOSE removed DGC from VN30 and BSR replaced it effective 2026-05-13.
# The current database mapping still contains the stale DGC relationship.
KNOWN_STALE_VN30_SYMBOLS = {"DGC"}

logger = logging.getLogger(__name__)


class StockExtraction(BaseModel):
    sentiment: str = Field(description="positive | neutral | negative")
    summary: str = Field(
        description="Short Vietnamese summary of the article (1-3 sentences)"
    )


class SerperError(RuntimeError):
    """A Serper request failed and must not advance the checkpoint."""


class SerperCreditsExhausted(SerperError):
    """Serper rejected a request because the account has no credits left."""


class DeepSeekError(RuntimeError):
    """A DeepSeek request failed and the current article must be retried."""


class DeepSeekCreditsExhausted(DeepSeekError):
    """DeepSeek rejected a request because the account has no balance left."""


def deepseek_error_is_credit_exhaustion(exc: Exception) -> bool:
    """Detect DeepSeek's official HTTP 402 insufficient-balance response."""
    status_code = getattr(exc, "status_code", None)
    if status_code == 402:
        return True

    parts = [str(exc)]
    body = getattr(exc, "body", None)
    if body:
        try:
            parts.append(json.dumps(body, ensure_ascii=False))
        except TypeError:
            parts.append(str(body))
    response = getattr(exc, "response", None)
    response_text = getattr(response, "text", None)
    if response_text:
        parts.append(str(response_text))

    normalized = " ".join(parts).lower()
    balance_words = ("balance", "credit", "credits", "quota")
    exhausted_words = (
        "insufficient",
        "depleted",
        "exhausted",
        "run out",
        "not enough",
        "top up",
        "top-up",
    )
    return (
        any(word in normalized for word in balance_words)
        and any(word in normalized for word in exhausted_words)
    )


def response_mentions_credit_exhaustion(status_code: int, body: str) -> bool:
    """Recognize Serper quota errors without depending on one response schema."""
    normalized = (body or "").lower()
    credit_words = ("credit", "credits", "quota", "balance")
    exhausted_words = (
        "depleted",
        "exhausted",
        "insufficient",
        "not enough",
        "no credit",
        "zero",
        "purchase",
        "top up",
        "top-up",
    )
    if status_code == 402:
        return True
    return (
        status_code in {400, 403, 429}
        and any(word in normalized for word in credit_words)
        and any(word in normalized for word in exhausted_words)
    )


def endpoint_url(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    return base_url if base_url.endswith("/news") else f"{base_url}/news"


class SerperClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 20,
        max_retries: int = 3,
        session: Optional[requests.Session] = None,
    ):
        self.url = endpoint_url(base_url)
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max(1, max_retries)
        self.session = session or requests.Session()

    def search(
        self, query: str, page: int, window_start: date, window_end: date
    ) -> list[dict[str, Any]]:
        # Serper forwards Google's custom-date tbs syntax. cd_max is inclusive.
        inclusive_end = window_end - timedelta(days=1)
        payload = {
            "q": (
                f"{query} after:{window_start.isoformat()} "
                f"before:{window_end.isoformat()}"
            ),
            "gl": "vn",
            "hl": "vi",
            "page": page,
            "num": 10,
            "tbs": (
                "cdr:1,"
                f"cd_min:{window_start.strftime('%m/%d/%Y')},"
                f"cd_max:{inclusive_end.strftime('%m/%d/%Y')}"
            ),
        }
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

        last_error = ""
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.post(
                    self.url, json=payload, headers=headers, timeout=self.timeout
                )
            except requests.RequestException as exc:
                last_error = str(exc)
                if attempt < self.max_retries:
                    time.sleep(2 ** (attempt - 1))
                    continue
                raise SerperError(f"Serper connection failed: {exc}") from exc

            body = response.text[:2000]
            if response_mentions_credit_exhaustion(response.status_code, body):
                raise SerperCreditsExhausted(
                    f"Serper credits exhausted (HTTP {response.status_code}): {body}"
                )

            if response.status_code == 429 or response.status_code >= 500:
                last_error = f"HTTP {response.status_code}: {body}"
                if attempt < self.max_retries:
                    retry_after = response.headers.get("Retry-After", "")
                    try:
                        delay = max(float(retry_after), 1.0)
                    except (TypeError, ValueError):
                        delay = float(2 ** (attempt - 1))
                    time.sleep(min(delay, 30))
                    continue

            try:
                response.raise_for_status()
                data = response.json()
            except (requests.RequestException, ValueError) as exc:
                raise SerperError(
                    f"Serper request failed (HTTP {response.status_code}): {body}"
                ) from exc

            if isinstance(data, dict) and data.get("error"):
                error_text = json.dumps(data.get("error"), ensure_ascii=False)
                if response_mentions_credit_exhaustion(
                    400, error_text
                ):
                    raise SerperCreditsExhausted(error_text)
                raise SerperError(f"Serper returned an error: {error_text}")

            news = data.get("news", []) if isinstance(data, dict) else []
            return news if isinstance(news, list) else []

        raise SerperError(f"Serper request failed after retries: {last_error}")


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'; expected YYYY-MM-DD"
        ) from exc


def month_windows(start: date, end: date) -> list[tuple[date, date]]:
    """Return half-open calendar-month windows covering start..end inclusive."""
    windows: list[tuple[date, date]] = []
    cursor = start
    final_exclusive = end + timedelta(days=1)
    while cursor < final_exclusive:
        if cursor.month == 12:
            next_month = date(cursor.year + 1, 1, 1)
        else:
            next_month = date(cursor.year, cursor.month + 1, 1)
        window_end = min(next_month, final_exclusive)
        windows.append((cursor, window_end))
        cursor = window_end
    return windows


def normalize_datetime(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=VN_TIMEZONE)
    return value


def parse_serper_datetime(
    value: Any, now: Optional[datetime] = None
) -> Optional[datetime]:
    """Parse common absolute and Vietnamese/English relative Serper dates."""
    if not value:
        return None
    if isinstance(value, datetime):
        return normalize_datetime(value)

    raw = str(value).strip()
    if not raw:
        return None
    current = now or datetime.now(VN_TIMEZONE)

    iso_value = raw.replace("Z", "+00:00")
    try:
        return normalize_datetime(datetime.fromisoformat(iso_value))
    except ValueError:
        pass

    vietnamese_month = re.fullmatch(
        r"(\d{1,2})\s+thg\s+(\d{1,2}),?\s+(\d{4})", raw, re.IGNORECASE
    )
    if vietnamese_month:
        day_value, month_value, year_value = map(
            int, vietnamese_month.groups()
        )
        try:
            return datetime(
                year_value, month_value, day_value, tzinfo=VN_TIMEZONE
            )
        except ValueError:
            return None

    for pattern in (
        "%b %d, %Y",
        "%B %d, %Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(raw, pattern).replace(tzinfo=VN_TIMEZONE)
        except ValueError:
            continue

    lowered = raw.lower()
    if lowered in {"yesterday", "hôm qua"}:
        return current - timedelta(days=1)

    relative = re.search(
        r"(\d+)\s*"
        r"(minute|minutes|min|hour|hours|day|days|week|weeks|month|months|"
        r"phút|giờ|ngày|tuần|tháng|năm)",
        lowered,
    )
    if not relative:
        return None
    amount = int(relative.group(1))
    unit = relative.group(2)
    if unit in {"minute", "minutes", "min", "phút"}:
        delta = timedelta(minutes=amount)
    elif unit in {"hour", "hours", "giờ"}:
        delta = timedelta(hours=amount)
    elif unit in {"day", "days", "ngày"}:
        delta = timedelta(days=amount)
    elif unit in {"week", "weeks", "tuần"}:
        delta = timedelta(weeks=amount)
    elif unit in {"month", "months", "tháng"}:
        delta = timedelta(days=30 * amount)
    else:
        delta = timedelta(days=365 * amount)
    return current - delta


def in_window(value: datetime, start: date, end: date) -> bool:
    published_date = value.astimezone(VN_TIMEZONE).date()
    return start <= published_date < end


def get_source(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def extract_article_content(url: str) -> Optional[dict[str, Any]]:
    try:
        article = Article(url, language="vi")
        article.download()
        article.parse()
        return {
            "title": (article.title or "").strip(),
            "content": (article.text or "").strip(),
            "publish_date": normalize_datetime(article.publish_date),
            "top_image": article.top_image or None,
        }
    except Exception as exc:
        logger.warning("Could not extract %s: %s", url, exc)
        return None


class DeepSeekStockEnricher:
    def __init__(self, api_key: str, model: str, base_url: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url.rstrip("/"))
        self.model = model

    def extract(
        self, title: str, content: str, symbol: str, company_name: str
    ) -> Optional[dict[str, str]]:
        system_prompt = f"""
Bạn là hệ thống phân tích tin tức tài chính Việt Nam về mã cổ phiếu
{symbol} ({company_name}).

Nhiệm vụ:
1. Gán sentiment: positive | neutral | negative theo tác động đến mã {symbol}.
2. Viết summary ngắn bằng tiếng Việt (1-3 câu).
3. Chỉ trả về một JSON object đúng mẫu:
   {{"sentiment":"positive|neutral|negative","summary":"..."}}
""".strip()
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"TITLE:\n{title}\n\nCONTENT:\n{content[:16000]}",
                    },
                ],
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=500,
                extra_body={"thinking": {"type": "disabled"}},
            )
        except Exception as exc:
            if deepseek_error_is_credit_exhaustion(exc):
                raise DeepSeekCreditsExhausted(
                    f"DeepSeek balance is exhausted: {exc}"
                ) from exc
            raise DeepSeekError(f"DeepSeek request failed: {exc}") from exc

        try:
            raw_content = response.choices[0].message.content
            if not raw_content:
                return None
            parsed = StockExtraction(**json.loads(raw_content))
            if not parsed or not (parsed.summary or "").strip():
                return None
            sentiment = (parsed.sentiment or "neutral").strip().lower()
            if sentiment not in {"positive", "neutral", "negative"}:
                sentiment = "neutral"
            return {
                "sentiment": sentiment,
                "summary": parsed.summary.strip(),
            }
        except (json.JSONDecodeError, TypeError, ValueError, KeyError) as exc:
            logger.error("DeepSeek returned invalid JSON output: %s", exc)
            return None


class StagingStore:
    """Append-only, crash-repairable JSONL storage for human review."""

    def __init__(self, path: Path):
        self.path = path.resolve()
        self.article_by_url: dict[str, dict[str, Any]] = {}
        self.pairs: set[tuple[str, str]] = set()
        self.record_dates: dict[tuple[str, str], date] = {}
        self.record_count = 0
        self._load_and_repair()

    def _load_and_repair(self) -> None:
        if not self.path.exists():
            return

        valid_end = 0
        with self.path.open("rb") as handle:
            line_number = 0
            while True:
                line = handle.readline()
                if not line:
                    break
                line_number += 1
                next_offset = handle.tell()
                if not line.strip():
                    valid_end = next_offset
                    continue
                try:
                    record = json.loads(line.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    # A Ctrl+C during the final append can leave only the last
                    # line partial. Earlier malformed lines require review.
                    if line.endswith(b"\n") or handle.read(1):
                        raise RuntimeError(
                            f"Invalid JSONL record at line {line_number}"
                        ) from exc
                    logger.warning(
                        "Removing incomplete final JSONL record at line %d",
                        line_number,
                    )
                    break
                self._remember(record, line_number)
                valid_end = next_offset

        file_size = self.path.stat().st_size
        if valid_end < file_size:
            with self.path.open("r+b") as handle:
                handle.truncate(valid_end)
                handle.flush()
                os.fsync(handle.fileno())

    def _remember(self, record: dict[str, Any], line_number: int) -> None:
        article = record.get("article")
        symbol = str(record.get("stock_symbol") or "").strip().upper()
        if not isinstance(article, dict) or not article.get("link") or not symbol:
            raise RuntimeError(
                f"Invalid review record at line {line_number}: "
                "stock_symbol and article.link are required"
            )
        link = str(article["link"])
        pair = (link, symbol)
        self.article_by_url.setdefault(link, article)
        self.pairs.add(pair)
        article_time = article.get("time")
        if article_time:
            try:
                parsed_time = datetime.fromisoformat(
                    str(article_time).replace("Z", "+00:00")
                )
                self.record_dates[pair] = parsed_time.astimezone(
                    VN_TIMEZONE
                ).date()
            except ValueError:
                logger.warning(
                    "Review record at line %d has an invalid article time: %s",
                    line_number,
                    article_time,
                )
        self.record_count += 1

    def has_pair(self, link: str, symbol: str) -> bool:
        return (link, symbol.upper()) in self.pairs

    def article_for(self, link: str) -> Optional[dict[str, Any]]:
        return self.article_by_url.get(link)

    def count_for_window(
        self, stock_symbol: str, window_start: date, window_end: date
    ) -> int:
        symbol = stock_symbol.strip().upper()
        return sum(
            1
            for (pair_link, pair_symbol), published_date in self.record_dates.items()
            if pair_link
            and pair_symbol == symbol
            and window_start <= published_date < window_end
        )

    def append(self, article: dict[str, Any], stock_symbol: str) -> bool:
        symbol = stock_symbol.strip().upper()
        link = str(article["link"])
        if self.has_pair(link, symbol):
            return False

        record = {
            "schema_version": 1,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "stock_symbol": symbol,
            "article": article,
        }
        encoded = (
            json.dumps(record, ensure_ascii=False, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("ab", buffering=0) as handle:
            written = handle.write(encoded)
            if written != len(encoded):
                raise OSError(
                    f"Only wrote {written}/{len(encoded)} bytes to {self.path}"
                )
            os.fsync(handle.fileno())

        self._remember(record, self.record_count + 1)
        return True


def validated_current_vn30_symbols(database_symbols: set[str]) -> list[str]:
    normalized = {
        str(symbol).strip().upper()
        for symbol in database_symbols
        if str(symbol).strip()
    }
    stale_symbols = sorted(normalized & KNOWN_STALE_VN30_SYMBOLS)
    if stale_symbols:
        logger.warning(
            "Ignoring known stale VN30 database mapping(s): %s",
            ", ".join(stale_symbols),
        )
    current_symbols = sorted(normalized - KNOWN_STALE_VN30_SYMBOLS)
    if len(current_symbols) != 30:
        raise RuntimeError(
            "Expected exactly 30 current VN30 symbols after known stale "
            f"mappings were removed, found {len(current_symbols)}: "
            f"{', '.join(current_symbols)}"
        )
    return current_symbols


def load_stocks(client: Any, symbols: Optional[list[str]] = None) -> list[dict[str, Any]]:
    if symbols is None:
        symbols = validated_current_vn30_symbols(get_vn30_symbols(client))
    else:
        symbols = sorted({symbol.strip().upper() for symbol in symbols if symbol.strip()})

    stock_response = (
        client.table(STOCK_TABLE)
        .select("id, stock_symbol")
        .in_("stock_symbol", symbols)
        .execute()
    )
    rows = stock_response.data or []
    stock_by_symbol = {
        str(row.get("stock_symbol") or "").strip().upper(): row
        for row in rows
        if row.get("id") is not None and row.get("stock_symbol")
    }
    missing = sorted(set(symbols) - set(stock_by_symbol))
    if missing:
        raise RuntimeError(f"Stock rows not found for: {', '.join(missing)}")

    company_by_symbol = {symbol: symbol for symbol in symbols}
    profile_response = (
        client.table("BI_Profile")
        .select("symbol, company_name")
        .in_("symbol", symbols)
        .execute()
    )
    for row in profile_response.data or []:
        symbol = str(row.get("symbol") or "").strip().upper()
        company_name = str(row.get("company_name") or "").strip()
        if symbol in company_by_symbol and company_name:
            company_by_symbol[symbol] = company_name

    return [
        {
            "id": stock_by_symbol[symbol]["id"],
            "symbol": symbol,
            "company_name": company_by_symbol[symbol],
        }
        for symbol in symbols
    ]


ARTICLE_FIELDS = {
    "title",
    "link",
    "description",
    "time",
    "thumbnail",
    "source",
    "content",
    "sentiment",
    "summary",
    "article_type",
}


def review_file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_review_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise RuntimeError(f"Review file not found: {path}")
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"Invalid JSON in review file at line {line_number}"
                ) from exc
            article = record.get("article")
            symbol = str(record.get("stock_symbol") or "").strip().upper()
            if not isinstance(article, dict) or not article.get("link") or not symbol:
                raise RuntimeError(
                    f"Invalid review record at line {line_number}: "
                    "stock_symbol and article.link are required"
                )
            records.append(record)
    return records


def review_record_month_key(
    record: dict[str, Any],
) -> Optional[tuple[str, str]]:
    symbol = str(record.get("stock_symbol") or "").strip().upper()
    article = record.get("article") or {}
    article_time = article.get("time")
    if not symbol or not article_time:
        return None
    try:
        published_at = datetime.fromisoformat(
            str(article_time).replace("Z", "+00:00")
        )
    except ValueError:
        return None
    return symbol, published_at.astimezone(VN_TIMEZONE).strftime("%Y-%m")


def trim_review_file(
    path: Path, articles_per_month: int
) -> dict[str, Any]:
    """Keep the first N staged records per symbol/month and preserve a backup."""
    if articles_per_month < 1:
        raise RuntimeError("articles_per_month must be at least 1")
    path = path.resolve()
    # Repair only a possible partial final append before parsing all records.
    StagingStore(path)
    records = load_review_records(path)
    counts: dict[tuple[str, str], int] = {}
    kept: list[dict[str, Any]] = []
    removed = 0
    for record in records:
        key = review_record_month_key(record)
        if key is None:
            kept.append(record)
            continue
        current = counts.get(key, 0)
        if current >= articles_per_month:
            removed += 1
            continue
        counts[key] = current + 1
        kept.append(record)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.stem}.backup-{timestamp}{path.suffix}")
    temporary = Path(f"{path}.trim.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for record in kept:
            handle.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n"
            )
        handle.flush()
        os.fsync(handle.fileno())

    shutil.copy2(path, backup)
    try:
        os.replace(temporary, path)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise
    return {
        "kept": len(kept),
        "removed": removed,
        "backup": str(backup),
    }


class SupabaseReviewImporter:
    def __init__(
        self,
        client: Any,
        stock_ids: dict[str, Any],
        max_retries: int = 5,
    ):
        self.client = client
        self.stock_ids = stock_ids
        self.article_ids: dict[str, Any] = {}
        self.max_retries = max(1, max_retries)

    @staticmethod
    def _is_transient_error(exc: Exception) -> bool:
        if isinstance(exc, httpx.TransportError):
            return True
        status_code = getattr(exc, "status_code", None)
        if status_code == 429 or (
            isinstance(status_code, int) and status_code >= 500
        ):
            return True
        normalized = str(exc).lower()
        return any(
            marker in normalized
            for marker in (
                "connectionterminated",
                "connection terminated",
                "connection reset",
                "remoteprotocolerror",
                "server disconnected",
                "timed out",
                "timeout",
            )
        )

    def _retry_delay(self, attempt: int, operation: str, exc: Exception) -> None:
        if not self._is_transient_error(exc) or attempt >= self.max_retries:
            raise exc
        delay = min(float(2 ** (attempt - 1)), 15.0)
        logger.warning(
            "Transient Supabase error during %s (attempt %d/%d): %s; "
            "retrying in %.0fs",
            operation,
            attempt,
            self.max_retries,
            exc,
            delay,
        )
        time.sleep(delay)

    def _article_id(self, link: str) -> Optional[Any]:
        if link in self.article_ids:
            return self.article_ids[link]
        for attempt in range(1, self.max_retries + 1):
            try:
                response = (
                    self.client.table(ARTICLE_TABLE)
                    .select("id")
                    .eq("link", link)
                    .limit(1)
                    .execute()
                )
                if not response.data:
                    return None
                article_id = response.data[0]["id"]
                self.article_ids[link] = article_id
                return article_id
            except Exception as exc:
                self._retry_delay(attempt, "article lookup", exc)
        return None

    def _ensure_link(self, article_id: Any, stock_id: Any) -> None:
        for attempt in range(1, self.max_retries + 1):
            try:
                response = (
                    self.client.table(ARTICLE_STOCK_TABLE)
                    .select("id")
                    .eq("article_id", article_id)
                    .eq("stock_id", stock_id)
                    .limit(1)
                    .execute()
                )
                if not response.data:
                    self.client.table(ARTICLE_STOCK_TABLE).insert(
                        {"article_id": article_id, "stock_id": stock_id}
                    ).execute()
                return
            except Exception as exc:
                # Restart with the lookup. If the INSERT reached Supabase
                # before the connection dropped, the next lookup finds it.
                self._retry_delay(attempt, "article-stock linking", exc)

    def _insert_article(
        self, article: dict[str, Any], link: str
    ) -> tuple[Any, bool]:
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.table(ARTICLE_TABLE).insert(
                    article
                ).execute()
                if not response.data:
                    raise RuntimeError(
                        f"Supabase did not return inserted article for {link}"
                    )
                article_id = response.data[0]["id"]
                self.article_ids[link] = article_id
                return article_id, True
            except Exception as exc:
                if not self._is_transient_error(exc):
                    raise
                self._retry_delay(attempt, "article insert", exc)
                # The server may have committed the INSERT before the
                # connection failed. Recheck by link before inserting again.
                recovered_id = self._article_id(link)
                if recovered_id is not None:
                    return recovered_id, False
        raise RuntimeError(f"Could not insert article after retries: {link}")

    def upsert(self, record: dict[str, Any]) -> str:
        symbol = str(record["stock_symbol"]).strip().upper()
        if symbol not in self.stock_ids:
            raise RuntimeError(f"Stock not found for reviewed symbol {symbol}")

        raw_article = record["article"]
        article = {
            key: value
            for key, value in raw_article.items()
            if key in ARTICLE_FIELDS
        }
        link = str(article.get("link") or "").strip()
        title = str(article.get("title") or "").strip()
        if not link or not title:
            raise RuntimeError(
                f"Reviewed {symbol} record requires article.title and article.link"
            )
        article["link"] = link
        article["title"] = title
        article["article_type"] = "stock"

        article_id = self._article_id(link)
        if article_id is None:
            article_id, inserted = self._insert_article(article, link)
            outcome = "inserted" if inserted else "existing"
        else:
            # Do not PATCH an existing Article. The current database has an
            # update trigger that references a missing NEW.updated_at field.
            # Keeping the existing row also makes re-imports idempotent; the
            # stock relationship is still ensured below.
            outcome = "existing"

        self._ensure_link(article_id, self.stock_ids[symbol])
        return outcome

    def _lookup_article_ids(self, links: list[str]) -> dict[str, Any]:
        unique_links = list(dict.fromkeys(links))
        result = {
            link: self.article_ids[link]
            for link in unique_links
            if link in self.article_ids
        }
        unknown = [link for link in unique_links if link not in result]
        if not unknown:
            return result

        for attempt in range(1, self.max_retries + 1):
            try:
                response = (
                    self.client.table(ARTICLE_TABLE)
                    .select("id, link")
                    .in_("link", unknown)
                    .execute()
                )
                for row in response.data or []:
                    link = str(row.get("link") or "")
                    if link and row.get("id") is not None:
                        self.article_ids[link] = row["id"]
                        result[link] = row["id"]
                return result
            except Exception as exc:
                self._retry_delay(attempt, "batch article lookup", exc)
        return result

    def _insert_article_batch(
        self, articles_by_link: dict[str, dict[str, Any]]
    ) -> set[str]:
        pending = dict(articles_by_link)
        inserted_links: set[str] = set()
        attempt = 1
        while pending:
            try:
                ordered_links = list(pending)
                response = self.client.table(ARTICLE_TABLE).insert(
                    [pending[link] for link in ordered_links]
                ).execute()
                rows = response.data or []
                if len(rows) != len(ordered_links):
                    raise RuntimeError(
                        "Supabase did not return every bulk-inserted article"
                    )
                rows_by_link = {
                    str(row.get("link") or ""): row
                    for row in rows
                    if row.get("link")
                }
                for position, link in enumerate(ordered_links):
                    row = rows_by_link.get(link, rows[position])
                    article_id = row.get("id")
                    if article_id is None:
                        raise RuntimeError(
                            f"Supabase did not return an article id for {link}"
                        )
                    self.article_ids[
                        str(row.get("link") or link)
                    ] = article_id
                    self.article_ids[link] = article_id
                    inserted_links.add(link)
                return inserted_links
            except Exception as exc:
                if not self._is_transient_error(exc):
                    raise
                self._retry_delay(attempt, "batch article insert", exc)
                # The response may have been lost after commit. Resolve all
                # pending links before another INSERT.
                recovered = self._lookup_article_ids(list(pending))
                for link in list(pending):
                    if link in recovered:
                        inserted_links.add(link)
                        pending.pop(link)
                attempt += 1
        return inserted_links

    def _ensure_links_batch(self, pairs: set[tuple[Any, Any]]) -> None:
        if not pairs:
            return
        article_ids = list({article_id for article_id, _ in pairs})
        stock_ids = list({stock_id for _, stock_id in pairs})

        for attempt in range(1, self.max_retries + 1):
            try:
                response = (
                    self.client.table(ARTICLE_STOCK_TABLE)
                    .select("article_id, stock_id")
                    .in_("article_id", article_ids)
                    .in_("stock_id", stock_ids)
                    .execute()
                )
                existing = {
                    (row.get("article_id"), row.get("stock_id"))
                    for row in (response.data or [])
                }
                missing = sorted(
                    pairs - existing,
                    key=lambda pair: (str(pair[0]), str(pair[1])),
                )
                if missing:
                    self.client.table(ARTICLE_STOCK_TABLE).insert(
                        [
                            {"article_id": article_id, "stock_id": stock_id}
                            for article_id, stock_id in missing
                        ]
                    ).execute()
                return
            except Exception as exc:
                # Restart with the bulk lookup. This recovers safely if the
                # relationship INSERT committed before its response was lost.
                self._retry_delay(attempt, "batch article-stock linking", exc)

    def upsert_batch(
        self, records: list[dict[str, Any]]
    ) -> dict[str, int]:
        prepared: list[tuple[str, str, dict[str, Any]]] = []
        article_by_link: dict[str, dict[str, Any]] = {}
        for record in records:
            symbol = str(record["stock_symbol"]).strip().upper()
            if symbol not in self.stock_ids:
                raise RuntimeError(f"Stock not found for reviewed symbol {symbol}")

            raw_article = record["article"]
            article = {
                key: value
                for key, value in raw_article.items()
                if key in ARTICLE_FIELDS
            }
            link = str(article.get("link") or "").strip()
            title = str(article.get("title") or "").strip()
            if not link or not title:
                raise RuntimeError(
                    f"Reviewed {symbol} record requires "
                    "article.title and article.link"
                )
            article["link"] = link
            article["title"] = title
            article["article_type"] = "stock"
            prepared.append((symbol, link, article))
            article_by_link.setdefault(link, article)

        existing_ids = self._lookup_article_ids(list(article_by_link))
        missing_articles = {
            link: article
            for link, article in article_by_link.items()
            if link not in existing_ids
        }
        inserted_links = self._insert_article_batch(missing_articles)

        pairs = {
            (self.article_ids[link], self.stock_ids[symbol])
            for symbol, link, _ in prepared
        }
        self._ensure_links_batch(pairs)

        counts = {"inserted": 0, "existing": 0}
        counted_inserted: set[str] = set()
        for _, link, _ in prepared:
            if link in inserted_links and link not in counted_inserted:
                counts["inserted"] += 1
                counted_inserted.add(link)
            else:
                counts["existing"] += 1
        return counts


def run_review_import(
    client: Any,
    review_path: Path,
    checkpoint_path: Path,
    reset: bool = False,
    batch_size: int = 50,
) -> int:
    review_path = review_path.resolve()
    checkpoint_path = checkpoint_path.resolve()
    if batch_size < 1:
        raise RuntimeError("Import batch size must be at least 1")
    if reset and checkpoint_path.exists():
        checkpoint_path.unlink()

    records = load_review_records(review_path)
    digest = review_file_digest(review_path)
    checkpoint: Optional[dict[str, Any]] = None
    if checkpoint_path.exists():
        with checkpoint_path.open("r", encoding="utf-8") as handle:
            checkpoint = json.load(handle)
        if (
            checkpoint.get("kind") != "review_import"
            or checkpoint.get("source_file") != str(review_path)
            or checkpoint.get("source_sha256") != digest
        ):
            raise RuntimeError(
                "Import checkpoint does not match the reviewed file. "
                "Use --reset-import after confirming the changed file."
            )

    if checkpoint and checkpoint.get("status") == "completed":
        logger.info("Reviewed file was already imported completely.")
        return 0

    if not records:
        now = datetime.now(timezone.utc).isoformat()
        empty_checkpoint = {
            "version": 1,
            "kind": "review_import",
            "status": "completed",
            "source_file": str(review_path),
            "source_sha256": digest,
            "next_record": 0,
            "total_records": 0,
            "stats": {"inserted": 0, "existing": 0},
            "created_at": now,
            "updated_at": now,
            "completed_at": now,
        }
        save_checkpoint(checkpoint_path, empty_checkpoint)
        logger.info("Reviewed file is empty; nothing was imported.")
        return 0

    symbols = sorted(
        {
            str(record["stock_symbol"]).strip().upper()
            for record in records
        }
    )
    stocks = load_stocks(client, symbols)
    importer = SupabaseReviewImporter(
        client, {stock["symbol"]: stock["id"] for stock in stocks}
    )
    if checkpoint is None:
        now = datetime.now(timezone.utc).isoformat()
        checkpoint = {
            "version": 1,
            "kind": "review_import",
            "status": "running",
            "source_file": str(review_path),
            "source_sha256": digest,
            "next_record": 0,
            "total_records": len(records),
            "batch_size": batch_size,
            "stats": {"inserted": 0, "existing": 0},
            "created_at": now,
            "updated_at": now,
        }
        save_checkpoint(checkpoint_path, checkpoint)

    checkpoint["status"] = "running"
    checkpoint.pop("pause_reason", None)
    checkpoint["stats"].setdefault("inserted", 0)
    checkpoint["stats"].setdefault("existing", 0)
    checkpoint["batch_size"] = batch_size
    save_checkpoint(checkpoint_path, checkpoint)
    try:
        while checkpoint["next_record"] < len(records):
            start_index = checkpoint["next_record"]
            end_index = min(start_index + batch_size, len(records))
            outcomes = importer.upsert_batch(records[start_index:end_index])
            for outcome, count in outcomes.items():
                checkpoint["stats"][outcome] += count
            checkpoint["next_record"] = end_index
            save_checkpoint(checkpoint_path, checkpoint)
            logger.info(
                "Imported review records %d-%d/%d "
                "(inserted=%d, existing=%d)",
                start_index + 1,
                end_index,
                len(records),
                outcomes["inserted"],
                outcomes["existing"],
            )
    except KeyboardInterrupt:
        checkpoint["status"] = "paused_by_user"
        checkpoint["pause_reason"] = "Interrupted by user"
        save_checkpoint(checkpoint_path, checkpoint)
        logger.warning("Import paused by user; progress was saved.")
        return 130
    except Exception as exc:
        checkpoint["status"] = "paused_error"
        checkpoint["pause_reason"] = f"{type(exc).__name__}: {exc}"
        save_checkpoint(checkpoint_path, checkpoint)
        logger.exception("Import paused after an error; progress was saved.")
        return 1

    checkpoint["status"] = "completed"
    checkpoint["completed_at"] = datetime.now(timezone.utc).isoformat()
    save_checkpoint(checkpoint_path, checkpoint)
    logger.info("Reviewed import completed: %s", checkpoint["stats"])
    return 0


def new_checkpoint(
    start: date,
    end: date,
    symbols: list[str],
    pages_per_month: int,
    articles_per_month: int = 10,
    output_path: Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "version": CHECKPOINT_VERSION,
        "status": "running",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "symbols": symbols,
        "pages_per_month": pages_per_month,
        "articles_per_month": articles_per_month,
        "output_file": str(output_path.resolve()),
        "cursor": {"symbol_index": 0, "window_index": 0, "page": 1},
        "pending_page": None,
        "stats": {
            "serper_requests": 0,
            "results": 0,
            "staged": 0,
            "duplicate": 0,
            "skipped": 0,
        },
        "created_at": now,
        "updated_at": now,
    }


def load_checkpoint(path: Path) -> Optional[dict[str, Any]]:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        checkpoint = json.load(handle)
    if checkpoint.get("version") == 2:
        checkpoint["version"] = CHECKPOINT_VERSION
        checkpoint.setdefault("articles_per_month", 10)
        logger.info(
            "Migrated collection checkpoint to the 10-articles-per-month format"
        )
    if checkpoint.get("version") != CHECKPOINT_VERSION:
        raise RuntimeError(
            f"Unsupported checkpoint version in {path}: "
            f"{checkpoint.get('version')!r}"
        )
    return checkpoint


def save_checkpoint(path: Path, checkpoint: dict[str, Any]) -> None:
    checkpoint["updated_at"] = datetime.now(timezone.utc).isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(f"{path}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(checkpoint, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def validate_checkpoint(
    checkpoint: dict[str, Any],
    start: date,
    end: date,
    pages_per_month: int,
    articles_per_month: int,
    output_path: Path,
) -> None:
    expected = {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "pages_per_month": pages_per_month,
        "articles_per_month": articles_per_month,
        "output_file": str(output_path.resolve()),
    }
    mismatches = [
        f"{key}: saved={checkpoint.get(key)!r}, requested={value!r}"
        for key, value in expected.items()
        if checkpoint.get(key) != value
    ]
    if mismatches:
        raise RuntimeError(
            "Checkpoint settings do not match this run. Use --reset to start "
            "again.\n" + "\n".join(mismatches)
        )


def checkpoint_summary(checkpoint: dict[str, Any]) -> str:
    cursor = checkpoint.get("cursor", {})
    pending = checkpoint.get("pending_page") or {}
    lines = [
        f"Status: {checkpoint.get('status', 'unknown')}",
        f"Range: {checkpoint.get('start_date')} to {checkpoint.get('end_date')}",
        f"Review file: {checkpoint.get('output_file')}",
        (
            "Monthly target: "
            f"{checkpoint.get('articles_per_month', 10)} staged articles/symbol"
        ),
        (
            "Cursor: symbol index "
            f"{cursor.get('symbol_index', 0)}, month index "
            f"{cursor.get('window_index', 0)}, page {cursor.get('page', 1)}"
        ),
    ]
    if pending:
        lines.append(
            "Cached page: "
            f"{pending.get('symbol')} {pending.get('window_start')} "
            f"page {pending.get('page')}, next item "
            f"{pending.get('next_item_index', 0)}/{len(pending.get('items', []))}"
        )
    stats = checkpoint.get("stats", {})
    lines.append(
        "Stats: "
        + ", ".join(f"{key}={value}" for key, value in stats.items())
    )
    if checkpoint.get("pause_reason"):
        lines.append(f"Pause reason: {checkpoint['pause_reason']}")
    return "\n".join(lines)


@dataclass
class Runtime:
    checkpoint_path: Path
    checkpoint: dict[str, Any]
    stocks: list[dict[str, Any]]
    windows: list[tuple[date, date]]
    serper: SerperClient
    staging: StagingStore
    enricher: DeepSeekStockEnricher
    request_delay: float


def process_result(
    item: dict[str, Any],
    stock: dict[str, Any],
    window_start: date,
    window_end: date,
    staging: StagingStore,
    enricher: DeepSeekStockEnricher,
    result_reference_time: Optional[datetime] = None,
) -> str:
    link = str(item.get("link") or "").strip()
    if not link:
        return "skipped"

    if staging.has_pair(link, stock["symbol"]):
        return "duplicate"

    existing_article = staging.article_for(link)
    if existing_article is not None:
        staging.append(existing_article, stock["symbol"])
        return "staged"

    extracted = extract_article_content(link)
    if not extracted or len(extracted.get("content") or "") < 100:
        return "skipped"

    result_date = parse_serper_datetime(item.get("date"), result_reference_time)
    article_date = result_date or extracted.get("publish_date")
    if article_date is None or not in_window(article_date, window_start, window_end):
        logger.info("Skipping result with missing/out-of-window date: %s", link)
        return "skipped"

    title = extracted.get("title") or str(item.get("title") or "").strip()
    if not title:
        return "skipped"
    analysis = enricher.extract(
        title,
        extracted["content"],
        stock["symbol"],
        stock["company_name"],
    )
    if not analysis:
        return "skipped"

    payload = {
        "title": title,
        "link": link,
        "description": str(item.get("snippet") or ""),
        "time": article_date.isoformat(),
        "thumbnail": item.get("imageUrl") or extracted.get("top_image"),
        "source": get_source(link),
        "content": extracted["content"],
        "sentiment": analysis["sentiment"],
        "summary": analysis["summary"],
        "article_type": "stock",
    }
    return "staged" if staging.append(payload, stock["symbol"]) else "duplicate"


def run_backfill(runtime: Runtime) -> None:
    checkpoint = runtime.checkpoint
    cursor = checkpoint["cursor"]
    stats = checkpoint["stats"]

    while cursor["symbol_index"] < len(runtime.stocks):
        stock = runtime.stocks[cursor["symbol_index"]]
        if cursor["window_index"] >= len(runtime.windows):
            logger.info("Completed all months for %s", stock["symbol"])
            cursor.update(
                {
                    "symbol_index": cursor["symbol_index"] + 1,
                    "window_index": 0,
                    "page": 1,
                }
            )
            checkpoint["pending_page"] = None
            save_checkpoint(runtime.checkpoint_path, checkpoint)
            continue

        window_start, window_end = runtime.windows[cursor["window_index"]]
        monthly_target = checkpoint["articles_per_month"]
        staged_this_month = runtime.staging.count_for_window(
            stock["symbol"], window_start, window_end
        )
        if staged_this_month >= monthly_target:
            logger.info(
                "%s | %s..%s | monthly target reached (%d/%d); advancing",
                stock["symbol"],
                window_start,
                window_end - timedelta(days=1),
                staged_this_month,
                monthly_target,
            )
            cursor.update(
                {"window_index": cursor["window_index"] + 1, "page": 1}
            )
            checkpoint["pending_page"] = None
            save_checkpoint(runtime.checkpoint_path, checkpoint)
            continue

        if cursor["page"] > checkpoint["pages_per_month"]:
            logger.warning(
                "%s | %s..%s | reached the %d-page search limit with "
                "only %d/%d staged articles",
                stock["symbol"],
                window_start,
                window_end - timedelta(days=1),
                checkpoint["pages_per_month"],
                staged_this_month,
                monthly_target,
            )
            cursor.update(
                {"window_index": cursor["window_index"] + 1, "page": 1}
            )
            checkpoint["pending_page"] = None
            save_checkpoint(runtime.checkpoint_path, checkpoint)
            continue

        pending = checkpoint.get("pending_page")
        if pending is None:
            logger.info(
                "%s | %s..%s | Serper page %d",
                stock["symbol"],
                window_start,
                window_end - timedelta(days=1),
                cursor["page"],
            )
            query = (
                f'("{stock["symbol"]}" OR "{stock["company_name"]}") '
                "(cổ phiếu OR chứng khoán OR doanh nghiệp)"
            )
            items = runtime.serper.search(
                query, cursor["page"], window_start, window_end
            )
            stats["serper_requests"] += 1
            stats["results"] += len(items)
            pending = {
                "symbol": stock["symbol"],
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
                "page": cursor["page"],
                "fetched_at": datetime.now(VN_TIMEZONE).isoformat(),
                "next_item_index": 0,
                "items": items,
            }
            checkpoint["pending_page"] = pending
            save_checkpoint(runtime.checkpoint_path, checkpoint)
            if runtime.request_delay > 0:
                time.sleep(runtime.request_delay)

        if not pending["items"]:
            cursor.update(
                {"window_index": cursor["window_index"] + 1, "page": 1}
            )
            checkpoint["pending_page"] = None
            save_checkpoint(runtime.checkpoint_path, checkpoint)
            continue

        while pending["next_item_index"] < len(pending["items"]):
            item_index = pending["next_item_index"]
            fetched_at = pending.get("fetched_at")
            outcome = process_result(
                pending["items"][item_index],
                stock,
                window_start,
                window_end,
                runtime.staging,
                runtime.enricher,
                datetime.fromisoformat(fetched_at) if fetched_at else None,
            )
            stats[outcome] += 1
            pending["next_item_index"] = item_index + 1
            save_checkpoint(runtime.checkpoint_path, checkpoint)
            logger.info(
                "%s %s item %d/%d",
                stock["symbol"],
                outcome,
                item_index + 1,
                len(pending["items"]),
            )
            if runtime.staging.count_for_window(
                stock["symbol"], window_start, window_end
            ) >= monthly_target:
                break

        staged_this_month = runtime.staging.count_for_window(
            stock["symbol"], window_start, window_end
        )
        if staged_this_month >= monthly_target:
            logger.info(
                "%s | %s..%s | staged target reached (%d/%d)",
                stock["symbol"],
                window_start,
                window_end - timedelta(days=1),
                staged_this_month,
                monthly_target,
            )
            cursor.update(
                {"window_index": cursor["window_index"] + 1, "page": 1}
            )
        else:
            cursor["page"] += 1
        checkpoint["pending_page"] = None
        save_checkpoint(runtime.checkpoint_path, checkpoint)

    checkpoint["status"] = "completed"
    checkpoint["completed_at"] = datetime.now(timezone.utc).isoformat()
    checkpoint.pop("pause_reason", None)
    save_checkpoint(runtime.checkpoint_path, checkpoint)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Collect current VN30 news into reviewable JSONL, then explicitly "
            "import the reviewed file into Supabase."
        )
    )
    parser.add_argument("--start-date", type=parse_date, default=None)
    parser.add_argument("--end-date", type=parse_date, default=None)
    parser.add_argument("--pages-per-month", type=int, default=None)
    parser.add_argument(
        "--articles-per-month",
        type=int,
        default=None,
        help="Valid staged articles required per symbol/month (default: 10).",
    )
    parser.add_argument("--request-delay", type=float, default=1.1)
    parser.add_argument("--request-timeout", type=float, default=20)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument(
        "--model",
        default="deepseek-v4-flash",
        help="DeepSeek model used for sentiment and summary.",
    )
    parser.add_argument(
        "--deepseek-base-url",
        default=None,
        help="Default: DEEPSEEK_BASE_URL or https://api.deepseek.com.",
    )
    parser.add_argument(
        "--checkpoint", type=Path, default=DEFAULT_CHECKPOINT
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=f"Review JSONL output (default: {DEFAULT_OUTPUT.name}).",
    )
    parser.add_argument(
        "--import-reviewed",
        type=Path,
        metavar="JSONL",
        help=(
            "Do not crawl; explicitly upsert this reviewed JSONL file into "
            "Article and Article_Stock."
        ),
    )
    parser.add_argument(
        "--import-checkpoint",
        type=Path,
        default=DEFAULT_IMPORT_CHECKPOINT,
    )
    parser.add_argument(
        "--import-batch-size",
        type=int,
        default=50,
        help="Reviewed records processed per Supabase batch (default: 50).",
    )
    parser.add_argument(
        "--reset-import",
        action="store_true",
        help="Discard only the saved reviewed-file import cursor.",
    )
    parser.add_argument(
        "--trim-review-to-limit",
        action="store_true",
        help=(
            "Back up and compact the current review JSONL to the configured "
            "per-symbol monthly article limit, without crawling or DB writes."
        ),
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show checkpoint progress without using Serper or Supabase.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Discard the saved cursor and begin a new run.",
    )
    return parser


def require_named_environment(names: tuple[str, ...]) -> tuple[str, ...]:
    values = tuple(
        os.getenv(name, "").strip()
        for name in names
    )
    missing = [name for name, value in zip(names, values) if not value]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )
    return values


def require_crawl_environment() -> tuple[str, str, str, str]:
    return require_named_environment(
        (
            "SUPABASE_URL",
            "SUPABASE_KEY",
            "SERPER_API_KEY",
            "DEEPSEEK_API_KEY",
        )
    )


def require_supabase_environment() -> tuple[str, str]:
    values = require_named_environment(
        (
            "SUPABASE_URL",
            "SUPABASE_KEY",
        )
    )
    return values[0], values[1]


def import_checkpoint_summary(checkpoint_path: Path) -> str:
    if not checkpoint_path.exists():
        return f"No import checkpoint found at {checkpoint_path}"
    with checkpoint_path.open("r", encoding="utf-8") as handle:
        checkpoint = json.load(handle)
    return "\n".join(
        [
            f"Import status: {checkpoint.get('status', 'unknown')}",
            f"Source: {checkpoint.get('source_file')}",
            (
                f"Progress: {checkpoint.get('next_record', 0)}/"
                f"{checkpoint.get('total_records', 0)}"
            ),
            f"Batch size: {checkpoint.get('batch_size', 1)}",
            "Stats: "
            + ", ".join(
                f"{key}={value}"
                for key, value in checkpoint.get("stats", {}).items()
            ),
            (
                f"Pause reason: {checkpoint['pause_reason']}"
                if checkpoint.get("pause_reason")
                else ""
            ),
        ]
    ).rstrip()


def main(argv: Optional[list[str]] = None) -> int:
    load_dotenv(SCRIPT_DIR / ".env")
    args = build_parser().parse_args(argv)
    checkpoint_path = args.checkpoint.resolve()
    import_checkpoint_path = args.import_checkpoint.resolve()

    if args.import_reviewed:
        if args.status:
            print(import_checkpoint_summary(import_checkpoint_path))
            return 0
        supabase_url, supabase_key = require_supabase_environment()
        client = create_client(supabase_url, supabase_key)
        return run_review_import(
            client,
            args.import_reviewed,
            import_checkpoint_path,
            reset=args.reset_import,
            batch_size=args.import_batch_size,
        )

    if args.reset_import:
        raise RuntimeError("--reset-import requires --import-reviewed")

    if args.trim_review_to_limit:
        checkpoint = load_checkpoint(checkpoint_path)
        output_path = (
            args.output.resolve()
            if args.output is not None
            else Path(checkpoint["output_file"])
            if checkpoint
            else DEFAULT_OUTPUT.resolve()
        )
        articles_per_month = (
            args.articles_per_month
            if args.articles_per_month is not None
            else int(checkpoint.get("articles_per_month", 10))
            if checkpoint
            else 10
        )
        result = trim_review_file(output_path, articles_per_month)
        if checkpoint:
            checkpoint["articles_per_month"] = articles_per_month
            checkpoint["stats"]["staged"] = result["kept"]
            checkpoint["stats"]["trimmed"] = (
                checkpoint["stats"].get("trimmed", 0) + result["removed"]
            )
            save_checkpoint(checkpoint_path, checkpoint)
        print(
            f"Kept {result['kept']} records; removed {result['removed']}. "
            f"Backup: {result['backup']}"
        )
        return 0

    if args.status:
        checkpoint = load_checkpoint(checkpoint_path)
        print(
            checkpoint_summary(checkpoint)
            if checkpoint
            else f"No checkpoint found at {checkpoint_path}"
        )
        return 0

    if args.reset and checkpoint_path.exists():
        checkpoint_path.unlink()

    checkpoint = load_checkpoint(checkpoint_path)
    output_path = (
        args.output.resolve()
        if args.output is not None
        else Path(checkpoint["output_file"])
        if checkpoint
        else DEFAULT_OUTPUT.resolve()
    )

    if checkpoint and checkpoint.get("status") == "completed" and not args.reset:
        logger.info(
            "This collection is already complete. Review %s, use --status to "
            "inspect progress, or --reset to start another pass.",
            output_path,
        )
        return 0

    saved_start = checkpoint.get("start_date") if checkpoint else None
    saved_end = checkpoint.get("end_date") if checkpoint else None
    start = args.start_date or (
        date.fromisoformat(saved_start) if saved_start else DEFAULT_START_DATE
    )
    end = args.end_date or (
        date.fromisoformat(saved_end) if saved_end else datetime.now(VN_TIMEZONE).date()
    )
    pages_per_month = (
        args.pages_per_month
        if args.pages_per_month is not None
        else int(checkpoint["pages_per_month"]) if checkpoint else 10
    )
    articles_per_month = (
        args.articles_per_month
        if args.articles_per_month is not None
        else int(checkpoint.get("articles_per_month", 10))
        if checkpoint
        else 10
    )
    if start > end:
        raise RuntimeError("--start-date must be on or before --end-date")
    if pages_per_month < 1:
        raise RuntimeError("--pages-per-month must be at least 1")
    if articles_per_month < 1:
        raise RuntimeError("--articles-per-month must be at least 1")
    if checkpoint:
        validate_checkpoint(
            checkpoint,
            start,
            end,
            pages_per_month,
            articles_per_month,
            output_path,
        )

    supabase_url, supabase_key, serper_key, deepseek_key = (
        require_crawl_environment()
    )
    client = create_client(supabase_url, supabase_key)
    saved_symbols = checkpoint.get("symbols") if checkpoint else None
    stocks = load_stocks(client, saved_symbols)
    symbols = [stock["symbol"] for stock in stocks]

    if checkpoint is None:
        checkpoint = new_checkpoint(
            start,
            end,
            symbols,
            pages_per_month,
            articles_per_month,
            output_path,
        )
        save_checkpoint(checkpoint_path, checkpoint)
    elif symbols != checkpoint["symbols"]:
        raise RuntimeError("Saved VN30 symbols could not be restored in the same order")

    checkpoint["status"] = "running"
    checkpoint.pop("pause_reason", None)
    save_checkpoint(checkpoint_path, checkpoint)

    runtime = Runtime(
        checkpoint_path=checkpoint_path,
        checkpoint=checkpoint,
        stocks=stocks,
        windows=month_windows(start, end),
        serper=SerperClient(
            os.getenv("SERPER_API_URL", "https://google.serper.dev"),
            serper_key,
            timeout=args.request_timeout,
            max_retries=args.max_retries,
        ),
        staging=StagingStore(output_path),
        enricher=DeepSeekStockEnricher(
            deepseek_key,
            args.model,
            args.deepseek_base_url
            or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        ),
        request_delay=max(args.request_delay, 0),
    )

    logger.info(
        "Starting VN30 collection: %d symbols, %s through %s, "
        "target %d staged/month, up to %d pages/month",
        len(stocks),
        start,
        end,
        articles_per_month,
        pages_per_month,
    )
    logger.info("Review records will be written only to %s", output_path)
    try:
        run_backfill(runtime)
    except SerperCreditsExhausted as exc:
        checkpoint["status"] = "paused_serper_credits"
        checkpoint["pause_reason"] = str(exc)
        save_checkpoint(checkpoint_path, checkpoint)
        logger.warning(
            "Serper credits are depleted. Progress was saved. Add credits and "
            "run the same command to resume."
        )
        return 2
    except DeepSeekCreditsExhausted as exc:
        checkpoint["status"] = "paused_deepseek_credits"
        checkpoint["pause_reason"] = str(exc)
        save_checkpoint(checkpoint_path, checkpoint)
        logger.warning(
            "DeepSeek balance is exhausted. Progress was saved without "
            "advancing the current article. Add balance and run the same "
            "command to resume."
        )
        return 3
    except KeyboardInterrupt:
        checkpoint["status"] = "paused_by_user"
        checkpoint["pause_reason"] = "Interrupted by user"
        save_checkpoint(checkpoint_path, checkpoint)
        logger.warning("Paused by user; progress and review data were saved.")
        return 130
    except Exception as exc:
        checkpoint["status"] = "paused_error"
        checkpoint["pause_reason"] = f"{type(exc).__name__}: {exc}"
        save_checkpoint(checkpoint_path, checkpoint)
        logger.exception("Collection paused after an error; progress was saved.")
        return 1

    logger.info(
        "VN30 collection completed. Review %s before importing. Stats: %s",
        output_path,
        checkpoint.get("stats"),
    )
    return 0
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    sys.exit(main())
