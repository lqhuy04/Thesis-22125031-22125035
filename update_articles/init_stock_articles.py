"""
init_stock_articles.py - One-time backfill of VN100 stock news.

For every current VN100 stock, runs Serper queries with pagination and
"tbs": "qdr:y" to scope results to the past year. No AI symbol extraction
is performed; only sentiment + summary are extracted. Every inserted article
is saved with article_type = "stock" and linked to its stock via the
Article_Stock join table.
"""

import os
import json
import time
import logging
import requests
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv
from supabase import create_client
from newspaper import Article
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Optional, List

from vn100_symbols import get_vn100_company_names, get_vn100_symbols

load_dotenv()

# ═════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═════════════════════════════════════════════════════════════════════════════

class Config:
    serper_url = os.getenv("SERPER_API_URL", "https://google.serper.dev")
    serper_key = os.getenv("SERPER_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

config = Config()

ARTICLE_TABLE       = "Article"
STOCK_TABLE         = "Stock"
ARTICLE_STOCK_TABLE = "Article_Stock"
SLEEP_SECONDS       = 1.1
STOCK_SLEEP_SECONDS = 3
PAGES_PER_STOCK     = 5           # Serper trả 5 tin/trang → 5 trang ≈ 50 tin/mã
SERPER_TIME_FILTER  = "qdr:y"      # giới hạn 1 năm gần nhất
CHECKPOINT_FILE     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "init_vn100_stock_articles_checkpoint.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

supabase = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_KEY", "")
)

# ═════════════════════════════════════════════════════════════════════════════
# NEWS EXTRACTION MODEL (stock: chỉ cần sentiment + summary)
# ═════════════════════════════════════════════════════════════════════════════

class StockExtraction(BaseModel):
    sentiment: str = Field(
        description="positive | neutral | negative"
    )
    summary: str = Field(
        description="Short Vietnamese summary of the article (1-3 sentences)"
    )

# ═════════════════════════════════════════════════════════════════════════════
# STOCK (VN100)
# ═════════════════════════════════════════════════════════════════════════════

def get_stocks() -> List[dict]:
    """Fetch VN100 stocks as [{id, stock_symbol, company_name}, ...]."""
    try:
        symbols = get_vn100_symbols(supabase)
        if not symbols:
            return []

        stock_res = (
            supabase.table(STOCK_TABLE)
            .select("id, stock_symbol")
            .in_("stock_symbol", sorted(symbols))
            .execute()
        )
        stock_rows = stock_res.data or []

        company_map = get_vn100_company_names(supabase)

        return [
            {
                "id": row["id"],
                "stock_symbol": row["stock_symbol"],
                "company_name": company_map.get(row["stock_symbol"], row["stock_symbol"]),
            }
            for row in stock_rows
            if row.get("id") is not None and row.get("stock_symbol")
        ]
    except Exception as e:
        logger.error(f"Error loading VN100 stocks: {e}")
        return []

# ═════════════════════════════════════════════════════════════════════════════
# SERPER + ARTICLE EXTRACTION
# ═════════════════════════════════════════════════════════════════════════════

def search_serper(query: str, page: int = 1) -> List[dict]:
    """Search news using Serper API (giới hạn 1 năm gần nhất)."""
    if not config.serper_key:
        logger.warning("SERPER_API_KEY not set")
        return []

    try:
        url = f"{config.serper_url}/news"

        payload = {
            "q": query,
            "gl": "vn",
            "hl": "vi",
            "page": page,
            "num": 10,
            "tbs": SERPER_TIME_FILTER,
        }

        headers = {
            "X-API-KEY": config.serper_key,
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        return data.get("news", [])
    except Exception as e:
        logger.error(f"Serper search error (page {page}): {e}")
        return []

def get_source(url: str) -> str:
    """Extract the domain (source) name from a URL."""
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc[4:] if netloc.startswith("www.") else netloc
    except Exception:
        return ""

def extract_article_content(url: str) -> Optional[dict]:
    """Extract article content using Newspaper."""
    try:
        article = Article(url, language="vi")
        article.download()
        article.parse()
        return {
            "title": article.title,
            "content": article.text,
            "publish_date": article.publish_date,
            "top_image": article.top_image,  # Main image from article
        }
    except Exception as e:
        logger.debug(f"Newspaper extraction error ({url}): {e}")
        return None

def extract_stock_info(title: str, content: str, symbol: str, company_name: str) -> Optional[dict]:
    """Extract sentiment and summary using OpenAI (no stock symbol extraction needed)."""
    if not config.openai_key:
        logger.warning("OPENAI_API_KEY not set")
        return None

    try:
        system_prompt = f"""
Bạn là hệ thống phân tích tin tức tài chính Việt Nam về mã cổ phiếu {symbol} ({company_name}).
Nhiệm vụ:
1. Gán sentiment: positive | neutral | negative (theo góc nhìn tác động đến mã {symbol}).
2. Viết summary ngắn bằng tiếng Việt (1-3 câu).
""".strip()

        user_prompt = f"TITLE:\n{title}\n\nCONTENT:\n{content}"

        openai_client = OpenAI(api_key=config.openai_key)

        response = openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=StockExtraction,
            temperature=0,
        )

        result = response.choices[0].message.parsed
        if not result:
            return None

        sentiment = (result.sentiment or "neutral").strip().lower()
        if sentiment not in {"positive", "neutral", "negative"}:
            sentiment = "neutral"

        return {
            "sentiment": sentiment,
            "summary": (result.summary or "").strip(),
        }
    except Exception as e:
        logger.error(f"OpenAI extraction error: {e}")
        return None

def article_exists(title: str, link: str) -> bool:
    """Check if article already exists in database."""
    try:
        result = (
            supabase.table(ARTICLE_TABLE)
            .select("id")
            .eq("title", title)
            .eq("link", link)
            .limit(1)
            .execute()
        )
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Error checking article existence: {e}")
        return False

def insert_stock_article(article_data: dict) -> Optional[int]:
    """Insert stock article (no AI symbol linking). Returns new article id, or None if skipped."""
    try:
        # Check for duplicates
        if article_exists(article_data["title"], article_data["link"]):
            logger.info(f"⏭  Skipped (duplicate): {article_data['title'][:50]}...")
            return None

        # Skip if content too short
        if not article_data.get("content") or len(article_data["content"]) < 100:
            logger.info(f"⏭  Skipped (no content): {article_data['title'][:50]}...")
            return None

        # Insert article
        article_res = supabase.table(ARTICLE_TABLE).insert({
            "title": article_data["title"],
            "link": article_data["link"],
            "description": article_data.get("description", ""),
            "time": article_data.get("time", datetime.now().isoformat()),
            "thumbnail": article_data.get("thumbnail", None),
            "source": article_data.get("source", ""),
            "content": article_data.get("content", ""),
            "sentiment": article_data.get("sentiment", "neutral"),
            "summary": article_data.get("summary", ""),
            "article_type": "stock",
        }).execute()

        if not article_res.data:
            logger.error(f"Failed to insert article: {article_data['title'][:50]}...")
            return None

        article_id = article_res.data[0]["id"]
        logger.info(f"✅ Saved: {article_data['title'][:50]}...")
        return article_id
    except Exception as e:
        logger.error(f"Error inserting article: {e}")
        return None

def link_article_stock(article_id: int, stock_id) -> None:
    """Link an article to a stock via Article_Stock, skipping if already linked."""
    try:
        existing = (
            supabase.table(ARTICLE_STOCK_TABLE)
            .select("article_id,stock_id")
            .eq("article_id", article_id)
            .eq("stock_id", stock_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            return

        supabase.table(ARTICLE_STOCK_TABLE).insert({
            "article_id": article_id,
            "stock_id": stock_id,
        }).execute()
    except Exception as e:
        logger.error(f"Error linking article {article_id} to stock {stock_id}: {e}")

def get_seen_links_from_db() -> dict[str, int]:
    """Load existing article links -> id so we can skip duplicates before OpenAI runs
    while still being able to link an already-seen article to a new stock."""
    try:
        result = supabase.table(ARTICLE_TABLE).select("id, link").execute()
        return {
            row["link"]: row["id"]
            for row in (result.data or [])
            if row.get("link") and row.get("id") is not None
        }
    except Exception as e:
        logger.error(f"Error loading existing article links: {e}")
        return {}

# ═════════════════════════════════════════════════════════════════════════════
# CHECKPOINT (resume support)
# ═════════════════════════════════════════════════════════════════════════════
#
# {
#   "stocks_completed": [1, 2],    stock ids fully processed
#   "current_stock_id": 3,        stock currently in progress (if any)
#   "next_page_index": 5          next Serper page (1-based) to fetch
# }

def load_checkpoint() -> dict:
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading checkpoint, starting fresh: {e}")
    return {}

def save_checkpoint(state: dict) -> None:
    try:
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving checkpoint: {e}")

def clear_checkpoint() -> None:
    try:
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
    except Exception as e:
        logger.error(f"Error removing checkpoint file: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def process_stock(
    stock_id,
    symbol: str,
    company_name: str,
    seen_links: dict[str, int],
    start_page: int,
    checkpoint: dict,
) -> tuple[int, int]:
    """Quét PAGES_PER_STOCK trang Serper cho 1 mã, lưu các bài mới.
    Trả về (số bài fetch được, số bài đã lưu)."""
    query = f"Tin tức tình hình kinh doanh, hoạt động của {company_name} {symbol}"

    fetched = 0
    inserted = 0

    for page in range(start_page, PAGES_PER_STOCK + 1):
        news_items = search_serper(query, page=page)

        if not news_items:
            logger.info(f"  [page {page}] → không còn kết quả, dừng mã {symbol}")
            break

        logger.info(f"  [page {page}] {len(news_items)} tin")
        fetched += len(news_items)

        for item in news_items:
            link = item.get("link", "")
            if not link:
                continue

            # Already have this article (from this or an earlier stock run):
            # skip re-extraction/AI cost, just link it to this stock.
            if link in seen_links:
                logger.info(f"↺  Already have article, linking stock only: {link}")
                link_article_stock(seen_links[link], stock_id)
                continue

            article_content = extract_article_content(link)
            if not article_content:
                continue

            stock_info = extract_stock_info(
                article_content["title"], article_content["content"], symbol, company_name
            )
            if not stock_info:
                continue

            publish_date = article_content.get("publish_date")
            article_time = publish_date.isoformat() if publish_date else datetime.now().isoformat()

            article_data = {
                "title": article_content["title"],
                "link": link,
                "description": item.get("snippet", ""),
                "time": article_time,
                "thumbnail": item.get("imageUrl") or article_content.get("top_image"),
                "source": get_source(link),
                "content": article_content["content"],
                "sentiment": stock_info["sentiment"],
                "summary": stock_info["summary"],
            }

            article_id = insert_stock_article(article_data)
            if article_id:
                inserted += 1
                seen_links[link] = article_id
                link_article_stock(article_id, stock_id)

            time.sleep(SLEEP_SECONDS)

        checkpoint["current_stock_id"] = stock_id
        checkpoint["next_page_index"] = page + 1
        save_checkpoint(checkpoint)

        time.sleep(SLEEP_SECONDS)  # rate limit giữa các trang

    return fetched, inserted

def main():
    stocks = get_stocks()
    if not stocks:
        logger.error("No VN100 stocks found. Exiting.")
        return

    checkpoint = load_checkpoint()
    if checkpoint:
        logger.info("↻ Resuming from checkpoint...")
    else:
        checkpoint = {
            "stocks_completed": [],
            "current_stock_id": None,
            "next_page_index": 1,
        }
        save_checkpoint(checkpoint)

    completed_ids = set(checkpoint.get("stocks_completed", []))
    resume_stock_id = checkpoint.get("current_stock_id")
    resume_page_index = checkpoint.get("next_page_index", 1)

    logger.info(
        f"Starting stock news backfill for {len(stocks)} VN100 stocks "
        f"({PAGES_PER_STOCK} pages each, past 1 year)..."
    )

    seen_links = get_seen_links_from_db()

    total_fetched = 0
    total_inserted = 0

    for s_idx, stock in enumerate(stocks, 1):
        stock_id = stock["id"]
        symbol = stock["stock_symbol"]
        company_name = stock["company_name"]

        if stock_id in completed_ids:
            logger.info(f"⏭  [{s_idx}/{len(stocks)}] Stock '{symbol}' already completed, skipping.")
            continue

        start_page = resume_page_index if stock_id == resume_stock_id else 1

        logger.info(f"\n===== [{s_idx}/{len(stocks)}] Stock: {symbol} ({company_name}) =====")

        fetched, inserted = process_stock(
            stock_id, symbol, company_name, seen_links, start_page, checkpoint
        )
        total_fetched += fetched
        total_inserted += inserted
        logger.info(f"  → {symbol}: đã lưu {inserted} bài")

        completed_ids.add(stock_id)
        checkpoint["stocks_completed"] = sorted(completed_ids, key=str)
        checkpoint["current_stock_id"] = None
        checkpoint["next_page_index"] = 1
        save_checkpoint(checkpoint)

        time.sleep(STOCK_SLEEP_SECONDS)

    clear_checkpoint()

    logger.info(f"\n✅ Completed!")
    logger.info(f"Total articles fetched: {total_fetched}")
    logger.info(f"Total articles inserted: {total_inserted}")

if __name__ == "__main__":
    main()
