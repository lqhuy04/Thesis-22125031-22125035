"""
update_category_articles.py - Daily update of category (industry) news.

Runs once per day (end of day). For every row in the Category table, runs a
single Serper query for a single page ("tbs": "qdr:d" to scope results to
the past 24 hours). Same extraction/insert logic as init_category_articles.py,
minus the multi-page checkpoint/resume machinery (not needed for a 1-page-
per-category daily job).
"""

import os
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

load_dotenv()

# ═════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═════════════════════════════════════════════════════════════════════════════

class Config:
    serper_url = os.getenv("SERPER_API_URL", "https://google.serper.dev")
    serper_key = os.getenv("SERPER_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

config = Config()

ARTICLE_TABLE          = "Article"
CATEGORY_TABLE         = "Category"
ARTICLE_CATEGORY_TABLE = "Article_Category"
SLEEP_SECONDS          = 1.1
CATEGORY_SLEEP_SECONDS = 3
PAGES_PER_CATEGORY     = 1
SERPER_TIME_FILTER     = "qdr:d"   # giới hạn 1 ngày gần nhất

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
# NEWS EXTRACTION MODEL (category: chỉ cần sentiment + summary)
# ═════════════════════════════════════════════════════════════════════════════

class CategoryExtraction(BaseModel):
    sentiment: str = Field(
        description="positive | neutral | negative"
    )
    summary: str = Field(
        description="Short Vietnamese summary of the article (1-3 sentences)"
    )

# ═════════════════════════════════════════════════════════════════════════════
# CATEGORY
# ═════════════════════════════════════════════════════════════════════════════

def get_categories() -> List[dict]:
    """Fetch all categories (id, category_name) from the database."""
    try:
        result = supabase.table(CATEGORY_TABLE).select("id, category_name").execute()
        return result.data or []
    except Exception as e:
        logger.error(f"Error loading categories: {e}")
        return []

# ═════════════════════════════════════════════════════════════════════════════
# SERPER + ARTICLE EXTRACTION
# ═════════════════════════════════════════════════════════════════════════════

def search_serper(query: str, page: int = 1) -> List[dict]:
    """Search news using Serper API (giới hạn 1 ngày gần nhất)."""
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

def extract_category_info(title: str, content: str, category_name: str) -> Optional[dict]:
    """Extract sentiment and summary using OpenAI (no stock symbols for category news)."""
    if not config.openai_key:
        logger.warning("OPENAI_API_KEY not set")
        return None

    try:
        system_prompt = f"""
Bạn là hệ thống phân tích tin tức ngành {category_name} tại Việt Nam.
Nhiệm vụ:
1. Gán sentiment: positive | neutral | negative (theo góc nhìn tác động đến ngành {category_name}).
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
            response_format=CategoryExtraction,
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

def insert_category_article(article_data: dict) -> Optional[int]:
    """Insert category article (no stock linking). Returns new article id, or None if skipped."""
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
            "article_type": "category",
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

def link_article_category(article_id: int, category_id) -> None:
    """Link an article to a category via Article_Category, skipping if already linked."""
    try:
        existing = (
            supabase.table(ARTICLE_CATEGORY_TABLE)
            .select("id")
            .eq("article_id", article_id)
            .eq("category_id", category_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            return

        supabase.table(ARTICLE_CATEGORY_TABLE).insert({
            "article_id": article_id,
            "category_id": category_id,
        }).execute()
    except Exception as e:
        logger.error(f"Error linking article {article_id} to category {category_id}: {e}")

def get_seen_links_from_db() -> dict[str, int]:
    """Load existing article links -> id so we can skip duplicates before OpenAI runs
    while still being able to link an already-seen article to a new category."""
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
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def process_category(
    category_id,
    category_name: str,
    seen_links: dict[str, int],
) -> tuple[int, int]:
    """Quét 1 trang Serper cho 1 ngành (tin trong 24h qua), lưu các bài mới.
    Trả về (số bài fetch được, số bài đã lưu)."""
    query = f"Tin tức của ngành {category_name} tại Việt Nam"

    news_items = search_serper(query, page=1)
    if not news_items:
        logger.info(f"  → không có tin mới cho ngành {category_name}")
        return 0, 0

    logger.info(f"  → {len(news_items)} tin")
    inserted = 0

    for item in news_items:
        link = item.get("link", "")
        if not link:
            continue

        # Already have this article (from this or an earlier category run):
        # skip re-extraction/AI cost, just link it to this category.
        if link in seen_links:
            logger.info(f"↺  Already have article, linking category only: {link}")
            link_article_category(seen_links[link], category_id)
            continue

        article_content = extract_article_content(link)
        if not article_content:
            continue

        category_info = extract_category_info(
            article_content["title"], article_content["content"], category_name
        )
        if not category_info:
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
            "sentiment": category_info["sentiment"],
            "summary": category_info["summary"],
        }

        article_id = insert_category_article(article_data)
        if article_id:
            inserted += 1
            seen_links[link] = article_id
            link_article_category(article_id, category_id)

        time.sleep(SLEEP_SECONDS)

    return len(news_items), inserted

def main():
    categories = get_categories()
    if not categories:
        logger.error("No categories found. Exiting.")
        return

    logger.info(
        f"Starting daily category news update for {len(categories)} categories "
        f"({PAGES_PER_CATEGORY} page each, past 24h)..."
    )

    seen_links = get_seen_links_from_db()

    total_fetched = 0
    total_inserted = 0

    for c_idx, category in enumerate(categories, 1):
        category_id = category["id"]
        category_name = category["category_name"]

        logger.info(f"\n===== [{c_idx}/{len(categories)}] Category: {category_name} =====")

        fetched, inserted = process_category(category_id, category_name, seen_links)
        total_fetched += fetched
        total_inserted += inserted
        logger.info(f"  → {category_name}: đã lưu {inserted} bài")

        time.sleep(CATEGORY_SLEEP_SECONDS)

    logger.info(f"\n✅ Completed!")
    logger.info(f"Total articles fetched: {total_fetched}")
    logger.info(f"Total articles inserted: {total_inserted}")

if __name__ == "__main__":
    main()
