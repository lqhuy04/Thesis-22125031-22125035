"""
Market News Crawler
Crawl tin tức thị trường -> Gemini extract stock symbols -> save database
"""

import requests
import sys
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from newspaper import Article
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI

# ==========================================================
# ENV + PATH
# ==========================================================

load_dotenv(os.path.join(os.path.dirname(__file__), "app", ".env"))

sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from config import get_settings
from supabase import create_client


settings = get_settings()
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


# ==========================================================
# SERPER CONFIG
# ==========================================================

SERPER_API_KEY = "fd31c8b1df830b479395c7e633bdbc1bf44c37a0"
SERPER_API_URL = "https://google.serper.dev/news"

SEARCH_QUERY = "tin tức thị trường chứng khoán Việt Nam Vietstock, Cafef"
TIME_RANGE = "qdr:d"
NUM_RESULTS = 100

TRUSTED_SOURCES = [
    "vietstock.vn",
    "cafef.vn",
]

# ==========================================================
# GEMINI STRUCTURED OUTPUT
# ==========================================================


class NewsExtraction(BaseModel):
    stock_symbols: List[str] = Field(
        description="List of Vietnamese stock tickers mentioned. Example: VNM, VIC, ACB"
    )

    sentiment: str = Field(
        description="positive | neutral | negative"
    )


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=settings.GEMINI_API_KEY,
)

structured_llm = llm.with_structured_output(NewsExtraction)


# ==========================================================
# UTILS
# ==========================================================


def parse_vietnamese_date(date_str: str) -> Optional[datetime]:

    try:

        date_str = date_str.strip().lower()
        now = datetime.now()

        pattern = r"(\d+)\s*(phút|giờ|ngày|tuần|tháng|năm)\s*trước"

        match = re.search(pattern, date_str)

        if match:

            value = int(match.group(1))
            unit = match.group(2)

            if unit == "phút":
                return now - timedelta(minutes=value)

            if unit == "giờ":
                return now - timedelta(hours=value)

            if unit == "ngày":
                return now - timedelta(days=value)

            if unit == "tuần":
                return now - timedelta(weeks=value)

            if unit == "tháng":
                return now - timedelta(days=value * 30)

            if unit == "năm":
                return now - timedelta(days=value * 365)

        return None

    except:
        return None


def is_trusted_source(url: str):

    url = url.lower()

    for source in TRUSTED_SOURCES:

        if source in url:
            return True

    return False


# ==========================================================
# SERPER SEARCH
# ==========================================================


def search_serper(query: str):

    payload = {
        "q": query,
        "gl": "vn",
        "hl": "vi",
        "tbs": TIME_RANGE,
        "num": NUM_RESULTS,
    }

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }

    print("Searching:", query)

    res = requests.post(SERPER_API_URL, headers=headers, json=payload)

    data = res.json()

    return data.get("news", [])


# ==========================================================
# ARTICLE EXTRACTION
# ==========================================================


def extract_article(url):

    try:

        article = Article(url, language="vi")

        article.download()

        article.parse()

        return {
            "title": article.title,
            "content": article.text,
            "publish_date": article.publish_date,
        }

    except Exception as e:

        print("extract error:", e)

        return None


# ==========================================================
# GEMINI EXTRACTION
# ==========================================================


def extract_stock_info(title, content):

    try:

        prompt = f"""
Bạn là hệ thống phân tích tin tức tài chính.

Hãy đọc bài báo và trích xuất:

1. Tóm tắt ngắn
2. Các mã cổ phiếu Việt Nam liên quan (VD: VNM, VIC, ACB, FPT)
3. Sentiment của tin
4. Loại tin

Quy tắc:

- chỉ lấy mã cổ phiếu 3-4 ký tự viết hoa
- loại bỏ trùng lặp
- nếu không có thì trả []

TITLE:
{title}

CONTENT:
{content[:6000]}
"""

        result = structured_llm.invoke(prompt)

        return result

    except Exception as e:

        print("Gemini error:", e)

        return None


# ==========================================================
# DATABASE
# ==========================================================


def is_duplicate(link):

    res = (
        supabase.table("financial_news")
        .select("id")
        .eq("link", link)
        .execute()
    )

    return len(res.data) > 0


def save_news(data):

    try:

        supabase.table("financial_news").insert(data).execute()

        return True

    except Exception as e:

        print("DB error:", e)

        return False


# ==========================================================
# MAIN CRAWLER
# ==========================================================


def crawl():

    print("\nSTART NEWS CRAWLER\n")

    news_items = search_serper(SEARCH_QUERY)

    news_items = [
        n for n in news_items if is_trusted_source(n.get("link", ""))
    ]

    print("Trusted news:", len(news_items))

    saved = 0

    for idx, item in enumerate(news_items):

        link = item.get("link")

        print("\n", idx + 1, item.get("title"))

        if is_duplicate(link):

            print("duplicate skip")

            continue

        date_str = item.get("date")

        time_parsed = parse_vietnamese_date(date_str) if date_str else None

        extracted = extract_article(link)

        if not extracted:

            continue

        content = extracted["content"]

        if not content or len(content) < 200:

            print("content too short")

            continue

        ai = extract_stock_info(extracted["title"], content)

        if not ai:

            continue

        data = {
            "title": extracted["title"],
            "link": link,
            "stock_symbol": ai.stock_symbols,
            "description": item.get("snippet"),
            "time": time_parsed.isoformat() if time_parsed else None,
            "image_url": item.get("imageUrl"),
            "content": content,
            "source": item.get("source"),
            "sentiment": ai.sentiment,
        }

        if save_news(data):

            saved += 1

            print("saved:", ai.stock_symbols)

    print("\nDONE")

    print("Saved:", saved)


# ==========================================================
# ENTRY
# ==========================================================


if __name__ == "__main__":

    crawl()