"""
Market News Crawler
Serper -> Newspaper -> GPT-4o-mini extract symbols/sentiment/summary -> save database
"""

import requests
import sys
import os
import re
from urllib.parse import urlparse
from datetime import datetime, timedelta
from typing import List, Optional

from newspaper import Article
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from openai import OpenAI

# ==========================================================
# ENV + PATH
# ==========================================================

BASE_DIR = os.path.dirname(__file__)
load_dotenv(os.path.join(BASE_DIR, "..", "app", ".env"))

sys.path.append(os.path.join(BASE_DIR, ".."))

from app.config import get_settings
from supabase import create_client


settings = get_settings()
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


# ==========================================================
# SERPER CONFIG
# ==========================================================

SERPER_API_KEY = "fd31c8b1df830b479395c7e633bdbc1bf44c37a0"
SERPER_API_URL = "https://google.serper.dev/news"

SEARCH_QUERY = "(site:vietstock.vn OR site:cafef.vn) tin tức thị trường chứng khoán Việt Nam"
TIME_RANGE = "qdr:d"
NUM_RESULTS = 100
TARGET_SAVED = 100
MAX_FETCH_ROUNDS = 5

TRUSTED_SOURCES = [
    "vietstock.vn",
    "cafef.vn",
]

# ==========================================================
# OPENAI STRUCTURED OUTPUT
# ==========================================================


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


def _get_openai_client() -> OpenAI:

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY in environment")

    return OpenAI(api_key=api_key)


openai_client = _get_openai_client()


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


def parse_absolute_vietnamese_datetime(date_str: str) -> Optional[datetime]:

    if not date_str:
        return None

    value = date_str.strip()

    formats = [
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M:%S%z",
        "%d-%m-%Y %H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    return None


def extract_publish_datetime_from_html(html: str) -> Optional[datetime]:

    if not html:
        return None

    # Vietstock often includes <span class="datenew">06-05-2025 17:34:39+07:00</span>
    datenew_match = re.search(
        r'class=["\']datenew["\'][^>]*>\s*([^<]+?)\s*<',
        html,
        flags=re.IGNORECASE,
    )
    if datenew_match:
        parsed = parse_absolute_vietnamese_datetime(datenew_match.group(1))
        if parsed:
            return parsed

    # Fallback to <span class="date">06/05/2025 17:34</span>
    date_match = re.search(
        r'class=["\']date["\'][^>]*>\s*([^<]+?)\s*<',
        html,
        flags=re.IGNORECASE,
    )
    if date_match:
        parsed = parse_absolute_vietnamese_datetime(date_match.group(1))
        if parsed:
            return parsed

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

    return search_serper_with_options(query=query, time_range=TIME_RANGE, num_results=NUM_RESULTS)


def search_serper_with_options(query: str, time_range: str, num_results: int):

    payload = {
        "q": query,
        "gl": "vn",
        "hl": "vi",
        "num": num_results,
    }

    if time_range:
        payload["tbs"] = time_range

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }

    print("Searching:", query, "|", (time_range or "no-time-filter"), "| num=", num_results)

    res = requests.post(SERPER_API_URL, headers=headers, json=payload)

    data = res.json()

    return data.get("news", [])


def collect_candidates(seen_links: set[str], round_number: int):

    query_variants = [
        SEARCH_QUERY,
        "site:vietstock.vn tin tức thị trường chứng khoán Việt Nam",
        "site:cafef.vn tin tức thị trường chứng khoán Việt Nam",
        "site:vietstock.vn tin tuc chung khoan",
        "site:cafef.vn tin tuc chung khoan",
        "vietstock vn chung khoan",
        "cafef vn chung khoan",
    ]

    time_ranges = ["qdr:d", "qdr:w", "qdr:m", "qdr:y", ""]

    candidates = []

    print(f"\nCollecting candidates - round {round_number}")

    for time_range in time_ranges:
        for query in query_variants:
            items = search_serper_with_options(
                query=query,
                time_range=time_range,
                num_results=NUM_RESULTS,
            )

            print("Serper returned:", len(items))
            if items:
                print("Sources before trusted filter:")
                for item in items[:10]:
                    link = item.get("link", "")
                    domain = urlparse(link).netloc
                    print("-", domain or "(no-domain)", "|", item.get("source"))

            for item in items:
                link = item.get("link", "")
                if not link:
                    continue
                if not is_trusted_source(link):
                    continue
                if link in seen_links:
                    continue
                seen_links.add(link)
                candidates.append(item)

    print("Trusted new candidates:", len(candidates))

    return candidates


# ==========================================================
# ARTICLE EXTRACTION
# ==========================================================


def extract_article(url):

    try:

        article = Article(url, language="vi")

        article.download()

        article.parse()

        html = article.html or ""
        parsed_from_html = extract_publish_datetime_from_html(html)

        return {
            "title": article.title,
            "content": article.text,
            "publish_date": parsed_from_html or article.publish_date,
        }

    except Exception as e:

        print("extract error:", e)

        return None


# ==========================================================
# OPENAI EXTRACTION
# ==========================================================


def extract_stock_info(title, content):

    try:

        system_prompt = """
Bạn là hệ thống phân tích tin tức tài chính Việt Nam.

Nhiệm vụ:
1. Trích xuất các mã cổ phiếu Việt Nam liên quan.
2. Gán sentiment: positive | neutral | negative.
3. Viết summary ngắn bằng tiếng Việt (1-3 câu).

Quy tắc:
- stock_symbols chỉ gồm mã 3-4 ký tự in hoa (VD: VNM, VIC, ACB, FPT).
- Loại bỏ trùng lặp.
- Nếu không có mã hợp lệ, trả [] cho stock_symbols.
- sentiment bắt buộc thuộc một trong: positive, neutral, negative.
""".strip()

        user_prompt = f"""
TITLE:
{title}

CONTENT:
{content[:7000]}
""".strip()

        completion = openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=NewsExtraction,
            temperature=0,
        )

        result = completion.choices[0].message.parsed

        if not result:
            return None

        # Normalize sentiment to the expected enum in storage.
        normalized_sentiment = (result.sentiment or "neutral").strip().lower()
        if normalized_sentiment not in {"positive", "neutral", "negative"}:
            normalized_sentiment = "neutral"

        cleaned_symbols = []
        for symbol in result.stock_symbols:
            upper_symbol = symbol.strip().upper()
            if re.fullmatch(r"[A-Z]{3,4}", upper_symbol):
                cleaned_symbols.append(upper_symbol)

        unique_symbols = list(dict.fromkeys(cleaned_symbols))

        return NewsExtraction(
            stock_symbols=unique_symbols,
            sentiment=normalized_sentiment,
            summary=(result.summary or "").strip(),
        )

    except Exception as e:

        print("OpenAI error:", e)

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

    saved = 0
    round_number = 0
    seen_links = set()

    while saved < TARGET_SAVED and round_number < MAX_FETCH_ROUNDS:
        round_number += 1

        news_items = collect_candidates(seen_links=seen_links, round_number=round_number)

        if not news_items:
            print("No new trusted candidates left. Stop early.")
            break

        for idx, item in enumerate(news_items):

            if saved >= TARGET_SAVED:
                break

            link = item.get("link")

            print("\n", idx + 1, item.get("title"))

            if is_duplicate(link):

                print("duplicate skip")

                continue

            date_str = item.get("date")

            extracted = extract_article(link)

            if not extracted:

                continue

            content = extracted["content"]

            time_parsed = extracted.get("publish_date")

            if not time_parsed and date_str:
                absolute_from_serper = parse_absolute_vietnamese_datetime(date_str)
                time_parsed = absolute_from_serper or parse_vietnamese_date(date_str)

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
                "summary": ai.summary,
                "time": time_parsed.isoformat() if time_parsed else None,
                "image_url": item.get("imageUrl"),
                "content": content,
                "source": item.get("source"),
                "sentiment": ai.sentiment,
            }

            if save_news(data):

                saved += 1

                print("saved:", ai.stock_symbols, f"({saved}/{TARGET_SAVED})")

    if saved >= TARGET_SAVED:
        print("Target reached.")
    else:
        print("Stopped before target. Saved", saved, "out of", TARGET_SAVED)

    print("\nDONE")

    print("Saved:", saved)


# ==========================================================
# ENTRY
# ==========================================================


if __name__ == "__main__":

    crawl()