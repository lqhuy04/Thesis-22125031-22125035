import os
import time
import logging
import re
import requests
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client
from ssi_fc_data import fc_md_client
from newspaper import Article
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Optional, List

load_dotenv()

# ═════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═════════════════════════════════════════════════════════════════════════════

class Config:
    auth_type      = os.getenv("SSI_AUTH_TYPE", "Bearer")
    consumerID     = os.getenv("SSI_CONSUMER_ID", "")
    consumerSecret = os.getenv("SSI_CONSUMER_SECRET", "")
    url            = os.getenv("SSI_API_URL", "https://fc-data.ssi.com.vn/")
    stream_url     = os.getenv("SSI_STREAM_URL", "https://fc-datahub.ssi.com.vn/")
    serper_url     = os.getenv("SERPER_API_URL", "https://google.serper.dev")
    serper_key     = os.getenv("SERPER_API_KEY", "")
    openai_key     = os.getenv("OPENAI_API_KEY", "")

config = Config()

TABLE         = "Article"
SLEEP_SECONDS = 1.1
SYMBOL_SKIP_SUFFIX_RE = re.compile(r"\d{4}$")
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
# NEWS EXTRACTION MODEL
# ═════════════════════════════════════════════════════════════════════════════

class NewsExtraction(BaseModel):
    stock_symbols: List[str] = Field(
        description="List of Vietnamese stock tickers mentioned. Example: VNM, VIC, ACB"
    )
    sentiment: str = Field(
        description="positive | neutral | negative"
    )
    summary: str = Field(
        description="Short Vietnamese summary of the article (1-3 sentences)"
    )

# ═════════════════════════════════════════════════════════════════════════════
# SSI DATA
# ═════════════════════════════════════════════════════════════════════════════

def get_ssi_access_token() -> str:
    """Get access token from SSI API using consumer credentials."""
    try:
        url = "https://fc-data.ssi.com.vn/api/v2/Market/AccessToken"
        payload = {
            "consumerID": config.consumerID,
            "consumerSecret": config.consumerSecret
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        access_token = data.get("data", {}).get("accessToken", "")
        if not access_token:
            raise ValueError("No access token in response")
        
        logger.info("Successfully obtained SSI access token")
        return access_token
    except Exception as e:
        logger.error(f"Failed to get SSI access token: {e}")
        return ""

def get_all_symbols() -> list[str]:
    """Fetch all HOSE symbols from SSI API."""
    try:
        access_token = get_ssi_access_token()
        if not access_token:
            return []
        
        url = "https://fc-data.ssi.com.vn/api/v2/Market/Securities?Market=HOSE&PageSize=1000"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        symbols = [item.get("Symbol") for item in (data.get("data") or []) if item.get("Symbol")]
        logger.info(f"Fetched {len(symbols)} HOSE symbols from SSI API")
        return sorted(symbols)
    except Exception as e:
        logger.error(f"Failed to fetch symbols from SSI API: {e}")
        return []

def filter_symbols(symbols: list[str]) -> list[str]:
    """Skip symbols that end with four digits."""
    return [symbol for symbol in symbols if not SYMBOL_SKIP_SUFFIX_RE.search(symbol)]

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

def extract_stock_info(title: str, content: str) -> Optional[dict]:
    """Extract stock symbols and sentiment using OpenAI."""
    if not config.openai_key:
        logger.warning("OPENAI_API_KEY not set")
        return None
    
    try:
        system_prompt = """
Bạn là hệ thống phân tích tin tức tài chính Việt Nam.
Nhiệm vụ:
1. Trích xuất các mã cổ phiếu Việt Nam liên quan.
2. Gán sentiment: positive | neutral | negative.
3. Viết summary ngắn bằng tiếng Việt (1-3 câu).
Quy tắc:
- stock_symbols chỉ gồm mã 3-4 ký tự in hoa (VD: VNM, VIC, ACB).
- Nếu không có mã hợp lệ, trả [] cho stock_symbols.
""".strip()

        user_prompt = f"TITLE:\n{title}\n\nCONTENT:\n{content}"

        openai_client = OpenAI(api_key=config.openai_key)

        response = openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=NewsExtraction,
            temperature=0,
        )

        result = response.choices[0].message.parsed
        if not result:
            return None

        sentiment = (result.sentiment or "neutral").strip().lower()
        if sentiment not in {"positive", "neutral", "negative"}:
            sentiment = "neutral"

        symbols = list(dict.fromkeys(
            s.strip().upper() for s in result.stock_symbols
            if re.fullmatch(r"[A-Z]{3,4}", s.strip().upper())
        ))

        return {
            "stock_symbols": symbols,
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

def insert_article_with_stocks(article_data: dict) -> bool:
    """Insert article and link to stocks."""
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
        }).execute()

        if not article_res.data:
            logger.error(f"Failed to insert article: {article_data['title'][:50]}...")
            return False

        article_id = article_res.data[0]["id"]

        # Link to stocks
        for symbol in article_data.get("stock_symbols", []):
            try:
                stock_res = (
                    supabase.table("Stock")
                    .select("id")
                    .eq("stock_symbol", symbol)
                    .execute()
                )

                if not stock_res.data:
                    logger.debug(f"Symbol not found: {symbol}")
                    continue

                stock_id = stock_res.data[0]["id"]

                supabase.table("Article_Stock").insert({
                    "article_id": article_id,
                    "stock_id": stock_id,
                }).execute()
            except Exception as e:
                logger.debug(f"Error linking stock {symbol}: {e}")
                continue

        logger.info(f"✅ Saved: {article_data['title'][:50]}... | stocks: {article_data.get('stock_symbols', [])}")
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
    logger.info("Starting websocket article fetch for today...")
    
    symbols = get_all_symbols()
    if not symbols:
        logger.error("No symbols found. Exiting.")
        return

    symbols = filter_symbols(symbols)
    if not symbols:
        logger.error("No symbols left after filtering. Exiting.")
        return

    logger.info(f"Processing {len(symbols)} HOSE symbols (without 4-digit suffix)...")
    
    total_articles_fetched = 0
    total_articles_inserted = 0
    seen_links = get_seen_links_from_db()
    
    for idx, symbol in enumerate(symbols, 1):
        logger.info(f"\n[{idx}/{len(symbols)}] Fetching news for {symbol}...")
        
        # Search for news in last 24 hours
        query = f"{symbol} cổ phiếu chứng khoán"
        news_items = search_serper(query)
        
        if not news_items:
            logger.info(f"  → No news found")
            time.sleep(SLEEP_SECONDS)
            continue

        logger.info(f"  → Found {len(news_items)} results")

        # Filter trusted sources
        trusted_items = [item for item in news_items if is_trusted_source(item.get("link", ""))]
        logger.info(f"  → {len(trusted_items)} from trusted sources")

        articles_processed = 0
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

            # Extract stock info with AI
            stock_info = extract_stock_info(article_content["title"], article_content["content"])
            if not stock_info:
                continue

            # Prepare article data
            # Use article's actual publish_date if available, otherwise use current time
            publish_date = article_content.get("publish_date")
            article_time = publish_date.isoformat() if publish_date else datetime.now().isoformat()
            
            article_data = {
                "title": article_content["title"],
                "link": link,
                "description": item.get("snippet", ""),
                "time": article_time,
                "thumbnail": item.get("imageUrl") or article_content.get("top_image"),  # Serper imageUrl or Newspaper top_image
                "source": get_source(link),
                "content": article_content["content"],
                "sentiment": stock_info["sentiment"],
                "summary": stock_info["summary"],
                "stock_symbols": stock_info["stock_symbols"],
            }

            # Insert to database
            if insert_article_with_stocks(article_data):
                total_articles_inserted += 1
                articles_processed += 1
                seen_links.add(link)

            time.sleep(SLEEP_SECONDS)  # Rate limiting

        total_articles_fetched += len(trusted_items)
        logger.info(f"  → Processed {articles_processed}/{len(trusted_items)}")
        time.sleep(SLEEP_SECONDS)
    
    logger.info(f"\n✅ Completed!")
    logger.info(f"Total articles fetched: {total_articles_fetched}")
    logger.info(f"Total articles inserted: {total_articles_inserted}")

if __name__ == "__main__":
    main()
