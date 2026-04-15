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

            for page in [1,2,3]:
                try:
                    items = search_serper(base_query, "qdr:m", page)
                except Exception as e:
                    print(f"Serper error: {e}")
                    continue

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
                    "title": candidate["title"],
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
                    
                    if not record["content"]:
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
