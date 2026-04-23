"""
News Database Service
Handles database operations for financial news
"""
import requests
from supabase import create_client, Client
from app.config import settings
from app.models.article_schema import ArticlesResponse
from typing import Optional, List
from datetime import datetime, timedelta
from newspaper import Article
from pydantic import BaseModel, Field
import re
from openai import OpenAI


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


supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
class ArticlesService:
    """Service for news database operations"""

    @staticmethod
    def get_articles(limit: Optional[int] = None) -> List[ArticlesResponse]:
        try:
            query = supabase.table("Article").select("*").order("time", desc=True)
            if limit is not None:
                query = query.limit(max(1, limit))
            result = query.execute()
            return [ArticlesResponse(**item) for item in result.data] if result.data else []

        except Exception as e:
            print(f"Error getting news: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def get_articles_by_stock_symbol(stock_symbol: str, limit: Optional[int] = None) -> List[ArticlesResponse]:
        try:
            stock = supabase.table("Stock").select("id").eq("stock_symbol", stock_symbol).execute()
            stock_id = stock.data[0]["id"] if stock.data else None
            if not stock_id:
                return []
            
            result = (
                supabase.table("Article_Stock")
                .select("Article(*)")
                .eq("stock_id", stock_id)
                .execute()
            )

            if not result.data:
                return []

            # Bước 3: Lấy danh sách article_id từ kết quả trên
            article_ids = []
            article_map = {}
            for item in result.data:
                article = item.get("Article")
                if not article:
                    continue
                article_id = str(article.get("id") or "")
                if article_id:
                    article_ids.append(article_id)
                    article_map[article_id] = article

            if not article_ids:
                return []

            # Bước 4: Đếm số stock được tag cho mỗi article_id
            # Chỉ giữ lại article nào chỉ có đúng 1 stock tag
            count_result = (
                supabase.table("Article_Stock")
                .select("article_id")
                .in_("article_id", article_ids)
                .execute()
            )

            from collections import Counter
            tag_counts = Counter(
                str(row["article_id"]) for row in count_result.data
            )
            exclusive_ids = {aid for aid, count in tag_counts.items() if count == 1}

            # Bước 5: Build response chỉ từ exclusive articles
            articles = []
            for article_id, article in article_map.items():
                if article_id not in exclusive_ids:
                    continue
                try:
                    articles.append(ArticlesResponse(**article))
                except Exception:
                    continue

            articles.sort(key=lambda item: item.time or datetime.min, reverse=True)
            if limit is not None:
                return articles[: max(1, limit)]
            return articles

        except Exception as e:
            print(f"Error getting news: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def get_macro_articles(min_symbols: int = 2, limit: int = 50) -> List[ArticlesResponse]:
        try:
            min_symbols = max(1, min_symbols)
            limit = max(1, limit)

            result = supabase.rpc(
                "get_macro_articles",
                {"min_symbols": min_symbols, "lim": limit}
            ).execute()

            if not result.data:
                return []

            macro_items = []
            for article in result.data:
                try:
                    macro_items.append(ArticlesResponse(**article))
                except Exception:
                    continue

            return macro_items

        except Exception as e:
            print(f"Error getting macro news: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def get_articles_by_category_id(category_id: str, limit: int = 100) -> List[ArticlesResponse]:
        """
        Get news for a specific category by ID.
        Category(id) -> Category_Stock(stock_id) -> Article_Stock(article_id) -> Article
        """
        try:
            limit = max(1, limit)


            # Step 1: Get all stock_ids linked to this category
            category_stock_result = (
                supabase.table("Category_Stock")
                .select("stock_id")
                .eq("category_id", category_id)
                .execute()
            )
            if not category_stock_result.data:
                return []

            stock_ids = list({
                str(row["stock_id"])
                for row in category_stock_result.data
                if row.get("stock_id")
            })
            if not stock_ids:
                return []

            # Step 2: Get all article_ids linked to these stocks
            links_result = (
                supabase.table("Article_Stock")
                .select("article_id")
                .in_("stock_id", stock_ids)
                .execute()
            )
            if not links_result.data:
                return []

            article_ids = list({
                str(row["article_id"])
                for row in links_result.data
                if row.get("article_id")
            })
            if not article_ids:
                return []

            # Step 3: Fetch articles, sorted by time desc
            articles_result = (
                supabase.table("Article")
                .select("*")
                .in_("id", article_ids)
                .order("time", desc=True)
                .limit(limit)
                .execute()
            )
            if not articles_result.data:
                return []

            articles: List[ArticlesResponse] = []
            for item in articles_result.data:
                try:
                    articles.append(ArticlesResponse(**item))
                except Exception:
                    continue

            return articles

        except Exception as e:
            print(f"Error getting news by category_id={category_id}: {e}")
            import traceback
            traceback.print_exc()
            return []
        
    @staticmethod
    def get_business_articles(limit: Optional[int] = None) -> List[ArticlesResponse]:
        try:
            result = (
                supabase.table("Article")
                .select("*")
                .execute()
            )

            if not result.data:
                return []
            
            # Bước 3: Lấy danh sách article_id từ kết quả trên
            article_ids = []
            article_map = {}
            for item in result.data:
                article_id = str(item.get("id") or "")
                if article_id:
                    article_ids.append(article_id)
                    article_map[article_id] = item

            if not article_ids:
                return []

            # Bước 4: Đếm số stock được tag cho mỗi article_id
            # Chỉ giữ lại article nào chỉ có đúng 1 stock tag
            count_result = (
                supabase.table("Article_Stock")
                .select("article_id")
                .in_("article_id", article_ids)
                .execute()
            )

            from collections import Counter
            tag_counts = Counter(
                str(row["article_id"]) for row in count_result.data
            )
            exclusive_ids = {aid for aid, count in tag_counts.items() if count == 1}

            # Bước 5: Build response chỉ từ exclusive articles
            articles = []
            for article_id, article in article_map.items():
                if article_id not in exclusive_ids:
                    continue
                try:
                    articles.append(ArticlesResponse(**article))
                except Exception:
                    continue

            articles.sort(key=lambda item: item.time or datetime.min, reverse=True)
            if limit is not None:
                return articles[: max(1, limit)]
            return articles

        except Exception as e:
            print(f"Error getting news: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def get_today_highlight(
        stock_limit: int = 10,
        articles_per_stock: int = 2,
        return_debug: bool = False,
    ) -> List[dict] | dict:
        """
        Traverse latest articles, keep only exclusive articles (1 symbol per article),
        collect latest unique stocks, and return each stock with latest exclusive news.
        """
        try:
            from collections import Counter, defaultdict

            stock_limit = max(1, stock_limit)
            articles_per_stock = max(1, articles_per_stock)

            debug_info = {
                "stock_limit": stock_limit,
                "articles_per_stock": articles_per_stock,
                "pages_scanned": 0,
                "articles_scanned": 0,
                "articles_with_id": 0,
                "article_stock_links_scanned": 0,
                "exclusive_article_candidates": 0,
                "unique_exclusive_stocks_seen": 0,
                "strict_stocks_count": 0,
                "fallback_stocks_count": 0,
                "selected_stocks_count": 0,
                "returned_stocks_count": 0,
                "ended_reason": "",
            }

            def finalize(items: List[dict], ended_reason: Optional[str] = None) -> List[dict] | dict:
                if ended_reason:
                    debug_info["ended_reason"] = ended_reason
                debug_info["returned_stocks_count"] = len(items)
                if return_debug:
                    return {"data": items, "debug": debug_info}
                return items

            def fetch_article_stock_links(article_ids: List[str], batch_size: int = 1000) -> List[dict]:
                """Fetch all Article_Stock links for article_ids, avoiding default row cap."""
                all_rows: List[dict] = []
                start = 0
                while True:
                    batch_result = (
                        supabase.table("Article_Stock")
                        .select("id, article_id, stock_id")
                        .in_("article_id", article_ids)
                        .order("id", desc=False)
                        .range(start, start + batch_size - 1)
                        .execute()
                    )
                    rows = batch_result.data or []
                    if not rows:
                        break

                    all_rows.extend(rows)
                    if len(rows) < batch_size:
                        break

                    start += batch_size

                return all_rows

            page_size = 500
            cursor_time = None
            cursor_id = None

            stock_to_articles = defaultdict(list)
            stock_latest_time = {}

            while True:
                qualified_stock_count = sum(
                    1 for items in stock_to_articles.values() if len(items) >= articles_per_stock
                )
                if qualified_stock_count >= stock_limit:
                    break

                query = (
                    supabase.table("Article")
                    .select("*")
                    .order("time", desc=True)
                    .order("id", desc=True)
                    .limit(page_size)
                )

                if cursor_time and cursor_id:
                    query = query.or_(
                        f"time.lt.{cursor_time},and(time.eq.{cursor_time},id.lt.{cursor_id})"
                    )

                latest_articles_result = query.execute()
                debug_info["pages_scanned"] += 1

                article_rows = latest_articles_result.data or []
                debug_info["articles_scanned"] += len(article_rows)
                if not article_rows:
                    debug_info["ended_reason"] = "no_more_articles"
                    break

                article_ids = [
                    str(item.get("id"))
                    for item in article_rows
                    if item.get("id")
                ]
                debug_info["articles_with_id"] += len(article_ids)
                if not article_ids:
                    if len(article_rows) < page_size:
                        debug_info["ended_reason"] = "last_page_without_article_ids"
                        break
                    last_row = article_rows[-1]
                    cursor_time = last_row.get("time")
                    cursor_id = last_row.get("id")
                    continue

                links_data = fetch_article_stock_links(article_ids=article_ids)
                debug_info["article_stock_links_scanned"] += len(links_data)
                if not links_data:
                    if len(article_rows) < page_size:
                        debug_info["ended_reason"] = "last_page_without_links"
                        break
                    last_row = article_rows[-1]
                    cursor_time = last_row.get("time")
                    cursor_id = last_row.get("id")
                    continue

                tag_counts = Counter(
                    str(row.get("article_id"))
                    for row in links_data
                    if row.get("article_id")
                )

                article_to_stock_id = {}
                for row in links_data:
                    article_id = str(row.get("article_id") or "")
                    stock_id = str(row.get("stock_id") or "")
                    if not article_id or not stock_id:
                        continue
                    if tag_counts.get(article_id) != 1:
                        continue
                    article_to_stock_id[article_id] = stock_id

                debug_info["exclusive_article_candidates"] += len(article_to_stock_id)

                for article in article_rows:
                    article_id = str(article.get("id") or "")
                    stock_id = article_to_stock_id.get(article_id)
                    if not stock_id:
                        continue

                    if stock_id not in stock_latest_time:
                        stock_latest_time[stock_id] = article.get("time")

                    if len(stock_to_articles[stock_id]) < articles_per_stock:
                        stock_to_articles[stock_id].append(article)

                if len(article_rows) < page_size:
                    debug_info["ended_reason"] = "reached_last_page"
                    break

                last_row = article_rows[-1]
                cursor_time = last_row.get("time")
                cursor_id = last_row.get("id")

            strict_stock_ids = [
                stock_id
                for stock_id, items in stock_to_articles.items()
                if len(items) >= articles_per_stock
            ]

            fallback_stock_ids = [
                stock_id
                for stock_id, items in stock_to_articles.items()
                if len(items) > 0 and len(items) < articles_per_stock
            ]

            debug_info["unique_exclusive_stocks_seen"] = len(stock_to_articles)
            debug_info["strict_stocks_count"] = len(strict_stock_ids)
            debug_info["fallback_stocks_count"] = len(fallback_stock_ids)

            if not strict_stock_ids and not fallback_stock_ids:
                return finalize([], "no_eligible_stocks")

            strict_stock_ids = sorted(
                strict_stock_ids,
                key=lambda sid: stock_latest_time.get(sid) or datetime.min,
                reverse=True,
            )

            fallback_stock_ids = sorted(
                fallback_stock_ids,
                key=lambda sid: stock_latest_time.get(sid) or datetime.min,
                reverse=True,
            )

            selected_stock_ids = (strict_stock_ids + fallback_stock_ids)[:stock_limit]
            debug_info["selected_stocks_count"] = len(selected_stock_ids)

            stock_result = (
                supabase.table("Stock")
                .select("id, stock_symbol")
                .in_("id", selected_stock_ids)
                .execute()
            )
            stock_symbol_map = {
                str(item.get("id")): item.get("stock_symbol", "")
                for item in (stock_result.data or [])
                if item.get("id")
            }

            selected_symbols = [
                stock_symbol_map[sid]
                for sid in selected_stock_ids
                if stock_symbol_map.get(sid)
            ]

            if not selected_symbols:
                return finalize([], "selected_stocks_missing_symbols")

            profile_result = (
                supabase.table("BI_Profile")
                .select("stock_id, symbol, company_name, exchange")
                .in_("symbol", selected_symbols)
                .execute()
            )
            profile_map = {
                str(item.get("symbol") or ""): item
                for item in (profile_result.data or [])
                if item.get("symbol")
            }

            price_result = (
                supabase.table("Current_Stock_Price")
                .select("symbol, price_change, per_price_change, ceiling_price, floor_price, ref_price, current_price, total_match_vol, total_match_val")
                .in_("symbol", selected_symbols)
                .execute()
            )
            price_map = {
                str(item.get("symbol") or ""): item
                for item in (price_result.data or [])
                if item.get("symbol")
            }

            def to_float(value) -> float:
                try:
                    if value is None or value == "":
                        return 0.0
                    return float(value)
                except Exception:
                    return 0.0

            def to_str(value) -> str:
                if value is None:
                    return ""
                if hasattr(value, "isoformat"):
                    return value.isoformat()
                return str(value)

            def to_news_item(article: dict, stock_symbol: str) -> dict:
                return {
                    "id": str(article.get("id") or ""),
                    "title": str(article.get("title") or ""),
                    "link": str(article.get("link") or ""),
                    "stock_symbol": stock_symbol,
                    "description": str(article.get("description") or ""),
                    "time": to_str(article.get("time")),
                    "image_url": str(article.get("image_url") or ""),
                    "published_at": to_str(article.get("published_at") or article.get("time")),
                    "content": str(article.get("content") or ""),
                    "source": str(article.get("source") or ""),
                    "sentiment": str(article.get("sentiment") or ""),
                }

            highlights = []
            for stock_id in selected_stock_ids:
                stock_symbol = stock_symbol_map.get(stock_id, "")
                if not stock_symbol:
                    continue

                stock_articles = stock_to_articles.get(stock_id, [])
                if len(stock_articles) < articles_per_stock:
                    # Fallback query to fetch up to 2 exclusive latest news for this stock.
                    fallback_articles = ArticlesService.get_articles_by_stock_symbol(
                        stock_symbol=stock_symbol,
                        limit=articles_per_stock,
                    )
                    if fallback_articles:
                        stock_articles = [article.dict() for article in fallback_articles]

                profile = profile_map.get(stock_symbol, {})
                price = price_map.get(stock_symbol, {})

                if not stock_articles:
                    continue

                highlights.append(
                    {
                        "stock_id": stock_id,
                        "symbol": stock_symbol,
                        "company_name": str(profile.get("company_name") or ""),
                        "exchange": str(profile.get("exchange") or ""),
                        "PriceChange": to_float(price.get("price_change")),
                        "PerPriceChange": to_float(price.get("per_price_change")),
                        "CeilingPrice": to_float(price.get("ceiling_price")),
                        "FloorPrice": to_float(price.get("floor_price")),
                        "RefPrice": to_float(price.get("ref_price")),
                        "CurrentPrice": to_float(price.get("current_price")),
                        "TotalMatchVol": to_float(price.get("total_match_vol")),
                        "TotalMatchVal": to_float(price.get("total_match_val")),
                        "news": [
                            to_news_item(article=item, stock_symbol=stock_symbol)
                            for item in stock_articles[:articles_per_stock]
                        ],
                    }
                )

            return finalize(highlights, debug_info.get("ended_reason") or "completed")

        except Exception as e:
            print(f"Error getting today highlights: {e}")
            import traceback
            traceback.print_exc()
            if return_debug:
                return {
                    "data": [],
                    "debug": {
                        "error": str(e),
                        "ended_reason": "exception",
                    },
                }
            return []
        
    # ----------------------------------------------------------------------------------------------------
    @staticmethod
    def updateNewArticles(symbol: Optional[str] = "") -> bool:
        try:
            # ── Utils ──────────────────────────────────────────────
            def search_serper(query: str, time_range: str, page: Optional[int] = 1) -> List[dict]:
                payload = {
                    "q": query,
                    "gl": "vn",
                    "hl": "vi",
                    "tbs": time_range,
                    "page": page,
                }

                headers = {
                    "X-API-KEY": settings.SERPER_API_KEY,
                    "Content-Type": "application/json",
                }

                res = requests.post(settings.SERPER_API_URL, headers=headers, json=payload, timeout=10)
                res.raise_for_status()
                return res.json().get("organic", [])

            def is_trusted(url: str) -> bool:
                url = url.lower()
                return any(src in url for src in TRUSTED_SOURCES)
            
            def get_source(url: str) -> str:
                url = url.lower()
                for src in TRUSTED_SOURCES:
                    if src in url:
                        return src
                return ""
            
            def extract_article(url: str) -> Optional[dict]:
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
                    print(f"Extract error ({url}): {e}")
                    return None
                
            def extract_stock_info(title: str, content: str) -> Optional[dict]:
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

                    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

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
                    print(f"OpenAI error: {e}")
                    return None
                
            import calendar

            def subtract_months(dt: datetime, months: int) -> datetime:
                """Trừ số tháng chính xác (handle overflow ngày)"""
                year = dt.year
                month = dt.month - months

                while month <= 0:
                    month += 12
                    year -= 1

                day = min(dt.day, calendar.monthrange(year, month)[1])
                return dt.replace(year=year, month=month, day=day)

            def parse_date_string(date_str: str) -> str:
                now = datetime.now()
                date_str = date_str.strip().lower()

                # ========================
                # 1. "n đơn vị trước"
                # ========================
                match = re.match(r"(\d+)\s*(phút|giờ|ngày|tuần|tháng)\s*trước", date_str)
                if match:
                    value = int(match.group(1))
                    unit = match.group(2)

                    if unit == "phút":
                        result = now - timedelta(minutes=value)
                    elif unit == "giờ":
                        result = now - timedelta(hours=value)
                    elif unit == "ngày":
                        result = now - timedelta(days=value)
                    elif unit == "tuần":
                        result = now - timedelta(weeks=value)
                    elif unit == "tháng":
                        result = subtract_months(now, value)

                    return result.strftime("%Y-%m-%d")

                # ========================
                # 2. "dd thg m, yyyy"
                # ========================
                match = re.match(r"(\d{1,2})\s*thg\s*(\d{1,2}),\s*(\d{4})", date_str)
                if match:
                    day = int(match.group(1))
                    month = int(match.group(2))
                    year = int(match.group(3))

                    result = datetime(year, month, day)
                    return result.strftime("%Y-%m-%d")

                # ========================
                # 3. Extra (nên có)
                # ========================
                if date_str == "hôm qua":
                    return (now - timedelta(days=1)).strftime("%Y-%m-%d")

                if date_str in ["vừa xong", "mới đây"]:
                    return now.strftime("%Y-%m-%d")

                # ========================
                raise ValueError(f"Không parse được date string: {date_str}")
            
            # ── Search ──────────────────────────────────────────────
            TRUSTED_SOURCES = ["vietstock.vn", "cafef.vn", "vneconomy.vn", "stockbiz.vn"]

            base_query = "(site:vietstock.vn OR site:cafef.vn OR site:vneconomy.vn OR site:stockbiz.vn) tin tức thị trường chứng khoán Việt Nam"
            if symbol:
                base_query = f"(site:vietstock.vn OR site:cafef.vn OR site:vneconomy.vn OR site:stockbiz.vn) tin tức doanh nghiệp của mã cổ phiếu {symbol}"

            seen_links: set[str] = set()
            candidates: List[dict] = []

            try:
                items = search_serper(base_query, "qdr:m", 1)
            except Exception as e:
                print(f"Serper error: {e}")

            for item in items:
                link = item.get("link", "")
                if not link or not is_trusted(link) or link in seen_links:
                    continue

                seen_links.add(link)
                candidates.append(item)
                    

            print(f"Trusted candidates collected: {len(candidates)}")

            # ── Newspaper + AI ──────────────────────────────────────────────
            records = []
            for candidate in candidates:
                article = extract_article(candidate["link"])
                if not article:
                    continue
                
                ai = extract_stock_info(article["title"], article["content"])
                if not ai:
                    continue
            

                record = {
                    "title": article["title"],
                    "link": candidate["link"],
                    "description": candidate["snippet"],
                    "time": parse_date_string(candidate["date"]),
                    "content": article["content"],
                    "source": get_source(candidate["link"]),
                    "stock_symbols": ai["stock_symbols"],
                    "sentiment": ai["sentiment"],
                    "summary": ai["summary"],
                }

                records.append(record)

            # ── Database ──────────────────────────────────────────────
            try:
                for record in records:
                    # 0. Check duplicate link
                    existing = (
                        supabase.table("Article")
                        .select("id")
                        .eq("link", record["link"])
                        .execute()
                    )

                    if existing.data:
                        print(f"Duplicate, skip: {record['link']}")
                        continue
                    
                    if not record["content"] or len(record["content"]) < 500:
                        print(f"No content, skip: {record['link']}")
                        continue

                    # 1. Insert article, lấy id trả về
                    article_res = supabase.table("Article").insert({
                        "title": record["title"],
                        "link": record["link"],
                        "description": record["description"],
                        "time": record["time"],
                        "content": record["content"],
                        "source": record["source"],
                        "sentiment": record["sentiment"],
                        "summary": record["summary"],
                    }).execute()

                    if not article_res.data:
                        print(f"Insert article failed: {record['link']}")
                        continue

                    article_id = article_res.data[0]["id"]

                    # 2. Tìm stock_id cho từng symbol, insert Article_Stock
                    for symbol in record["stock_symbols"]:
                        stock_res = (
                            supabase.table("Stock")
                            .select("id")
                            .eq("stock_symbol", symbol)
                            .execute()
                        )

                        if not stock_res.data:
                            print(f"Symbol not found in Stock table: {symbol}")
                            continue

                        stock_id = stock_res.data[0]["id"]

                        supabase.table("Article_Stock").insert({
                            "article_id": article_id,
                            "stock_id": stock_id,
                        }).execute()

                    print(f"Saved: {record['title'][:60]} | symbols: {record['stock_symbols']}")

                
            except Exception as e:
                    print(f"DB error: {e}")
                    return False
            

            return True

        except Exception as e:
            print(f"Error update new articles: {e}")
            import traceback
            traceback.print_exc()
            return False
