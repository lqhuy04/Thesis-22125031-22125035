"""
init_articles.py
Khởi tạo tin tức 1 NĂM cho các mã thuộc rổ VN30.

Cách hoạt động:
    1. Lấy danh sách mã VN30 từ Supabase (vn30_symbols.get_vn30_symbols).
    2. Với mỗi mã, gọi Serper /news qua 10 trang (mỗi trang 10 tin) với bộ lọc
       thời gian tbs=qdr:y (trong 1 năm gần nhất).
    3. Chỉ giữ tin từ nguồn tin cậy (vietstock, cafef, vneconomy, stockbiz).
    4. Trích nội dung bằng Newspaper, phân tích mã/sentiment/summary bằng OpenAI.
    5. Lưu vào bảng Article và liên kết Article_Stock.

Chạy 1 lần để seed dữ liệu ban đầu; các job định kỳ (websocket_articles_1d.py)
sẽ cập nhật tiếp sau đó.
"""

import os
import time
import logging
import re
import requests
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from newspaper import Article
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Optional, List

from vn30_symbols import get_vn30_company_names

load_dotenv()

# ═════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═════════════════════════════════════════════════════════════════════════════

class Config:
    serper_url = os.getenv("SERPER_API_URL", "https://google.serper.dev")
    serper_key = os.getenv("SERPER_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

config = Config()

TABLE           = "Article"
SLEEP_SECONDS   = 1.1
PAGES_PER_SYMBOL = 10           # Serper trả 10 tin/trang → 10 trang ≈ 100 tin/mã
SERPER_TIME_FILTER = "qdr:y"    # giới hạn 1 năm gần nhất
TRUSTED_SOURCES = [
    "vietstock.vn", "cafef.vn", "vneconomy.vn", "stockbiz.vn",
    "tinnhanhchungkhoan.vn", "vietnambiz.vn", "ndh.vn", "baodautu.vn",
    "nguoiquansat.vn", "markettimes.vn", "fireant.vn", "cafebiz.vn",
    "tapchitaichinh.vn", "vnexpress.net", "dantri.com.vn", "vietnamplus.vn",
]

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
            "top_image": article.top_image,
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
        if article_exists(article_data["title"], article_data["link"]):
            logger.info(f"⏭  Skipped (duplicate): {article_data['title'][:50]}...")
            return False

        if not article_data.get("content") or len(article_data["content"]) < 100:
            logger.info(f"⏭  Skipped (no content): {article_data['title'][:50]}...")
            return False

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
            "article_type": "stock",
        }).execute()

        if not article_res.data:
            logger.error(f"Failed to insert article: {article_data['title'][:50]}...")
            return False

        article_id = article_res.data[0]["id"]

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

def process_symbol(symbol: str, company_name: str, seen_links: set[str]) -> int:
    """Xử lý 1 mã: quét 10 trang Serper, lưu các bài mới. Trả về số bài đã lưu."""
    query = f"Tin tức tình hình kinh doanh, hoạt động của {company_name} {symbol}"
    inserted = 0

    for page in range(1, PAGES_PER_SYMBOL + 1):
        news_items = search_serper(query, page=page)

        if not news_items:
            logger.info(f"  [page {page}] → không còn kết quả, dừng mã {symbol}")
            break

        trusted_items = [item for item in news_items if is_trusted_source(item.get("link", ""))]
        logger.info(f"  [page {page}] {len(news_items)} tin, {len(trusted_items)} từ nguồn tin cậy")

        for item in trusted_items:
            link = item.get("link", "")
            if not link:
                continue

            if link in seen_links:
                logger.info(f"⏭  Skipped duplicate URL before extraction: {link}")
                continue

            article_content = extract_article_content(link)
            if not article_content:
                continue

            stock_info = extract_stock_info(article_content["title"], article_content["content"])
            if not stock_info:
                continue

            publish_date = article_content.get("publish_date")
            article_time = publish_date.isoformat() if publish_date else datetime.now().isoformat()

            # Hybrid: luôn gán mã đang query + union thêm mã AI trích được,
            # tránh trường hợp AI trả [] khiến bài không link được mã nào.
            linked_symbols = list(dict.fromkeys([symbol] + stock_info["stock_symbols"]))

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
                "stock_symbols": linked_symbols,
            }

            if insert_article_with_stocks(article_data):
                inserted += 1
                seen_links.add(link)

            time.sleep(SLEEP_SECONDS)

        time.sleep(SLEEP_SECONDS)  # rate limit giữa các trang

    return inserted

def main():
    logger.info("Bắt đầu khởi tạo tin tức 1 năm cho VN30...")

    company_map = get_vn30_company_names(supabase)
    if not company_map:
        logger.error("Không lấy được mã VN30. Thoát.")
        return

    symbols = sorted(company_map.keys())
    logger.info(f"Sẽ xử lý {len(symbols)} mã VN30: {symbols}")

    seen_links = get_seen_links_from_db()
    total_inserted = 0

    for idx, symbol in enumerate(symbols, 1):
        company_name = company_map[symbol]
        logger.info(f"\n[{idx}/{len(symbols)}] === {symbol} ({company_name}) ===")
        inserted = process_symbol(symbol, company_name, seen_links)
        total_inserted += inserted
        logger.info(f"  → {symbol}: đã lưu {inserted} bài")

    logger.info(f"\n✅ Hoàn tất! Tổng số bài đã lưu: {total_inserted}")

if __name__ == "__main__":
    main()
