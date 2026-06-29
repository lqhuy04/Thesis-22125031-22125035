import os
import time
import logging
import requests
from datetime import datetime
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

TABLE         = "Article"
SLEEP_SECONDS = 1.1
MACRO_QUERY   = "Tin tức kinh tế vĩ mô trong tuần"
MACRO_PAGES   = 3
TRUSTED_SOURCES = ["vietstock.vn", "cafef.vn", "vneconomy.vn", "stockbiz.vn"]

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
# NEWS EXTRACTION MODEL (macro: chỉ cần sentiment + summary)
# ═════════════════════════════════════════════════════════════════════════════

class MacroExtraction(BaseModel):
    sentiment: str = Field(
        description="positive | neutral | negative"
    )
    summary: str = Field(
        description="Short Vietnamese summary of the article (1-3 sentences)"
    )

# ═════════════════════════════════════════════════════════════════════════════
# SERPER + ARTICLE EXTRACTION
# ═════════════════════════════════════════════════════════════════════════════

def search_serper(query: str, page: int = 1) -> List[dict]:
    """Search news using Serper API."""
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
            "num": 10
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
        logger.error(f"Serper search error: {e}")
        return []

def is_trusted_source(url: str) -> bool:
    """Check if URL is from a trusted source."""
    url_lower = url.lower()
    return any(src in url_lower for src in TRUSTED_SOURCES)

def get_source(url: str) -> str:
    """Extract source name from URL."""
    url_lower = url.lower()
    for src in TRUSTED_SOURCES:
        if src in url_lower:
            return src
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

def extract_macro_info(title: str, content: str) -> Optional[dict]:
    """Extract sentiment and summary using OpenAI (no stock symbols for macro news)."""
    if not config.openai_key:
        logger.warning("OPENAI_API_KEY not set")
        return None

    try:
        system_prompt = """
Bạn là hệ thống phân tích tin tức kinh tế vĩ mô Việt Nam.
Nhiệm vụ:
1. Gán sentiment: positive | neutral | negative.
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
            response_format=MacroExtraction,
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
            supabase.table(TABLE)
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

def insert_macro_article(article_data: dict) -> bool:
    """Insert macro article (no stock linking)."""
    try:
        # Check for duplicates
        if article_exists(article_data["title"], article_data["link"]):
            logger.info(f"⏭  Skipped (duplicate): {article_data['title'][:50]}...")
            return False

        # Skip if content too short
        if not article_data.get("content") or len(article_data["content"]) < 100:
            logger.info(f"⏭  Skipped (no content): {article_data['title'][:50]}...")
            return False

        # Insert article
        article_res = supabase.table(TABLE).insert({
            "title": article_data["title"],
            "link": article_data["link"],
            "description": article_data.get("description", ""),
            "time": article_data.get("time", datetime.now().isoformat()),
            "thumbnail": article_data.get("thumbnail", None),
            "source": article_data.get("source", ""),
            "content": article_data.get("content", ""),
            "sentiment": article_data.get("sentiment", "neutral"),
            "summary": article_data.get("summary", ""),
            "article_type": "macro",
        }).execute()

        if not article_res.data:
            logger.error(f"Failed to insert article: {article_data['title'][:50]}...")
            return False

        logger.info(f"✅ Saved: {article_data['title'][:50]}...")
        return True
    except Exception as e:
        logger.error(f"Error inserting article: {e}")
        return False

def get_seen_links_from_db() -> set[str]:
    """Load existing article links so we can skip duplicates before OpenAI runs."""
    try:
        result = supabase.table(TABLE).select("link").execute()
        return {row.get("link") for row in (result.data or []) if row.get("link")}
    except Exception as e:
        logger.error(f"Error loading existing article links: {e}")
        return set()

# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    logger.info("Starting macro economic news fetch...")

    total_articles_fetched = 0
    total_articles_inserted = 0
    seen_links = get_seen_links_from_db()

    news_items: List[dict] = []
    for page in range(1, MACRO_PAGES + 1):
        page_items = search_serper(MACRO_QUERY, page=page)
        if not page_items:
            break
        news_items.extend(page_items)
        time.sleep(SLEEP_SECONDS)

    if not news_items:
        logger.info("No macro news found. Exiting.")
        return

    logger.info(f"Found {len(news_items)} results")

    # Filter trusted sources
    trusted_items = [item for item in news_items if is_trusted_source(item.get("link", ""))]
    logger.info(f"{len(trusted_items)} from trusted sources")

    for item in trusted_items:
        link = item.get("link", "")

        if not link:
            continue

        if link in seen_links:
            logger.info(f"⏭  Skipped duplicate URL before extraction: {link}")
            continue

        # Extract content
        article_content = extract_article_content(link)
        if not article_content:
            continue

        # Extract sentiment + summary with AI (no stock symbols)
        macro_info = extract_macro_info(article_content["title"], article_content["content"])
        if not macro_info:
            continue

        # Use article's actual publish_date if available, otherwise use current time
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
            "sentiment": macro_info["sentiment"],
            "summary": macro_info["summary"],
        }

        # Insert to database
        if insert_macro_article(article_data):
            total_articles_inserted += 1
            seen_links.add(link)

        time.sleep(SLEEP_SECONDS)  # Rate limiting

    total_articles_fetched += len(trusted_items)

    logger.info(f"\n✅ Completed!")
    logger.info(f"Total articles fetched: {total_articles_fetched}")
    logger.info(f"Total articles inserted: {total_articles_inserted}")

if __name__ == "__main__":
    main()
