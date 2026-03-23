"""
Serper News Crawler
Serper -> Newspaper -> GPT-4o-mini extraction -> save to database
"""
import requests
import sys
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from newspaper import Article
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

# Load environment variables
BASE_DIR = os.path.dirname(__file__)
load_dotenv(os.path.join(BASE_DIR, '..', 'app', '.env'))

# Add app to path for imports
sys.path.append(os.path.join(BASE_DIR, '..'))

from app.config import get_settings
from supabase import create_client

# Get settings
settings = get_settings()
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Serper API config
SERPER_API_KEY = "fd31c8b1df830b479395c7e633bdbc1bf44c37a0"
SERPER_API_URL = "https://google.serper.dev/news"

# Các nguồn tin tức uy tín được phép
TRUSTED_SOURCES = [
    'vietstock.vn', 
]

# ============================================================================
# CẤU HÌNH TÌM KIẾM - CHỈNH TẠI ĐÂY
# ============================================================================
SEARCH_QUERY = "Tin tức Vinamilk Vietstock"          # Từ khóa tìm kiếm (công ty, cổ phiếu, chủ đề...)
STOCK_SYMBOL = "VNM"               # Mã cổ phiếu (hoặc None nếu không có)
TIME_RANGE = "qdr:y"               # qdr:h (1 giờ), qdr:d (1 ngày), qdr:w (1 tuần), qdr:m (1 tháng), qdr:y (1 năm)
NUM_RESULTS = 100                  # Số kết quả lấy từ Serper API (tối đa 100)
MAX_RESULTS = None                 # Số bài tối đa sau khi lọc (hoặc None để lấy tất cả)
# ============================================================================

class SentimentOutput(BaseModel):
    stock_symbols: List[str] = Field(
        description="List of related Vietnamese stock symbols, e.g. VNM, VIC"
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


def analyze_news(title: str, content: str) -> Optional[SentimentOutput]:
    """
    Analyze symbols, sentiment, and summary of financial news with GPT-4o-mini.
    """
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
{(content or '')[:7000]}
""".strip()

        completion = openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=SentimentOutput,
            temperature=0,
        )

        parsed = completion.choices[0].message.parsed
        if not parsed:
            return None

        normalized_sentiment = (parsed.sentiment or "neutral").strip().lower()
        if normalized_sentiment not in {"positive", "neutral", "negative"}:
            normalized_sentiment = "neutral"

        cleaned_symbols = []
        for symbol in parsed.stock_symbols:
            upper_symbol = symbol.strip().upper()
            if re.fullmatch(r"[A-Z]{3,4}", upper_symbol):
                cleaned_symbols.append(upper_symbol)

        unique_symbols = list(dict.fromkeys(cleaned_symbols))

        return SentimentOutput(
            stock_symbols=unique_symbols,
            sentiment=normalized_sentiment,
            summary=(parsed.summary or "").strip(),
        )

    except Exception as e:
        print(f"  Warning: OpenAI extraction error: {e}")
        return None

def parse_vietnamese_date(date_str: str) -> Optional[datetime]:
    """
    Parse Vietnamese relative date to datetime
    
    Examples:
        "6 ngày trước" -> 2026-02-03
        "2 giờ trước" -> 2 hours ago
        "1 tuần trước" -> 1 week ago
    """
    try:
        date_str = date_str.strip().lower()
        now = datetime.now()
        
        # Pattern: "X <unit> trước"
        pattern = r'(\d+)\s*(phút|giờ|ngày|tuần|tháng|năm)\s*trước'
        match = re.search(pattern, date_str)
        
        if match:
            value = int(match.group(1))
            unit = match.group(2)
            
            if unit == 'phút':
                return now - timedelta(minutes=value)
            elif unit == 'giờ':
                return now - timedelta(hours=value)
            elif unit == 'ngày':
                return now - timedelta(days=value)
            elif unit == 'tuần':
                return now - timedelta(weeks=value)
            elif unit == 'tháng':
                return now - timedelta(days=value * 30)
            elif unit == 'năm':
                return now - timedelta(days=value * 365)
        
        return None
        
    except Exception as e:
        print(f"Error parsing date '{date_str}': {e}")
        return None


def parse_absolute_vietnamese_datetime(date_str: str) -> Optional[datetime]:
    """Parse absolute datetime formats commonly found on Vietstock pages."""
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
    """Extract publish datetime from Vietstock HTML blocks (.datenew/.date)."""
    if not html:
        return None

    datenew_match = re.search(
        r'class=["\']datenew["\'][^>]*>\s*([^<]+?)\s*<',
        html,
        flags=re.IGNORECASE,
    )
    if datenew_match:
        parsed = parse_absolute_vietnamese_datetime(datenew_match.group(1))
        if parsed:
            return parsed

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


def is_trusted_source(url: str) -> bool:
    """
    Kiểm tra xem URL có từ nguồn uy tín không
    
    Args:
        url: URL của bài báo
    
    Returns:
        True nếu nguồn uy tín, False nếu không
    """
    try:
        url_lower = url.lower()
        for source in TRUSTED_SOURCES:
            if source in url_lower:
                return True
        return False
    except Exception as e:
        print(f"Error checking trusted source: {e}")
        return False


def search_serper(query: str, country: str = "vn", language: str = "vi", 
                  time_range: str = "qdr:m", num: int = 100) -> List[Dict]:
    """
    Search news using Serper API
    
    Args:
        query: Search query (e.g., company name)
        country: Country code (default: "vn")
        language: Language code (default: "vi")
        time_range: Time range (qdr:h, qdr:d, qdr:w, qdr:m, qdr:y)
        num: Number of results to fetch (max 100)
    
    Returns:
        List of news items
    """
    try:
        payload = {
            "q": query,
            "gl": country,
            "hl": language,
            "tbs": time_range,
            "num": num
        }
        
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        print(f"🔍 Searching Serper for: {query}")
        response = requests.post(SERPER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        news_items = data.get('news', [])
        
        print(f"✅ Found {len(news_items)} news articles")
        return news_items
        
    except Exception as e:
        print(f"❌ Error searching Serper: {e}")
        return []


def extract_content_with_newspaper(url: str) -> Dict:
    """
    Extract article content using newspaper3k
    
    Args:
        url: Article URL
    
    Returns:
        Dictionary with extracted content
    """
    try:
        print(f"  📄 Extracting content from: {url[:80]}...")
        
        article = Article(url, language='vi')
        article.download()
        article.parse()

        html = article.html or ""
        parsed_publish_date = extract_publish_datetime_from_html(html)
        
        return {
            "title": article.title or None,
            "content": article.text or None,
            "author": ", ".join(article.authors) if article.authors else None,
            "publish_date": parsed_publish_date or article.publish_date
        }
        
    except Exception as e:
        print(f"  ⚠️  Error extracting content: {e}")
        return {
            "title": None,
            "content": None,
            "author": None,
            "publish_date": None
        }


def save_to_database(news_item: Dict, stock_symbol: Optional[str] = None) -> bool:
    """
    Save news to database
    
    Args:
        news_item: News item from Serper + extracted content
        stock_symbol: Optional stock symbol
    
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        data = {
            "title": news_item.get('title'),
            "link": news_item.get('link'),
            "stock_symbol": news_item.get('stock_symbol') or ([stock_symbol] if stock_symbol else []),
            "description": news_item.get('description'),
            "summary": news_item.get('summary'),
            "time": news_item.get('time_parsed').isoformat() if news_item.get('time_parsed') else None,
            "image_url": news_item.get('image_url'),
            "content": news_item.get('content'),
            "source": news_item.get('source'),
            "sentiment": news_item.get('sentiment'),
        }
        
        # Insert to database
        result = supabase.table("financial_news").insert(data).execute()
        
        if result.data and len(result.data) > 0:
            print(f"  ✅ Saved to database")
            return True
        else:
            print(f"  ⚠️  Already exists in database")
            return False
            
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            print(f"  ⚠️  Duplicate (already exists)")
            return False
        print(f"  ❌ Database error: {e}")
        return False


def crawl_news(query: str, stock_symbol: Optional[str] = None, 
               time_range: str = "qdr:m", num_results: int = 100,
               max_results: Optional[int] = None):
    """
    Main crawl function
    
    Args:
        query: Search query
        stock_symbol: Optional stock symbol
        time_range: Time range filter
        num_results: Number of results to fetch from Serper API
        max_results: Maximum number of results to process after filtering
    """
    print("\n" + "="*80)
    print(f"🚀 Starting News Crawler")
    print(f"📊 Query: {query}")
    if stock_symbol:
        print(f"💼 Stock Symbol: {stock_symbol}")
    print(f"⏰ Time Range: {time_range}")
    print("="*80 + "\n")
    
    # Step 1: Search Serper
    news_items = search_serper(query, time_range=time_range, num=num_results)
    
    if not news_items:
        print("⚠️  No news found")
        return
    
    # Filter only trusted sources
    original_count = len(news_items)
    news_items = [item for item in news_items if is_trusted_source(item.get('link', ''))]
    
    if not news_items:
        return
    
    if max_results:
        news_items = news_items[:max_results]
    
    # Step 2: Process each news item
    saved_count = 0
    duplicate_count = 0
    
    for idx, item in enumerate(news_items, 1):
        link = item.get('link', '')
        print(f"\n[{idx}/{len(news_items)}] {item.get('title', 'No title')[:80]}...")
        print(f"  🔗 Source: {link}")
        
        # Extract basic fields from Serper
        title = item.get('title', '')
        description = item.get('snippet', '')
        date_str = item.get('date', '')
        source = item.get('source', 'Serper')
        image_url = item.get('imageUrl', None)
        
        # Step 3: Extract content with newspaper3k
        extracted = extract_content_with_newspaper(link)

        # Prefer exact publish date from page, then absolute date string, then relative date string.
        time_parsed = extracted.get('publish_date')
        if not time_parsed and date_str:
            absolute_from_serper = parse_absolute_vietnamese_datetime(date_str)
            time_parsed = absolute_from_serper or parse_vietnamese_date(date_str)
        
        # Step 3.5: GPT-4o-mini extraction (symbols, sentiment, summary)
        ai = analyze_news(title, extracted.get('content', ''))
        if not ai:
            print("  Warning: AI extraction failed, skip")
            continue

        ai_symbols = ai.stock_symbols
        if stock_symbol and stock_symbol not in ai_symbols:
            ai_symbols = [stock_symbol] + ai_symbols

        print(f"  Sentiment: {ai.sentiment}")
        print(f"  Symbols: {ai_symbols}")
        
        # Use extracted title if original is empty
        if not title and extracted.get('title'):
            title = extracted['title']
        
        # Prepare news item
        news_data = {
            'title': title,
            'link': link,
            'description': description,
            'summary': ai.summary,
            'stock_symbol': ai_symbols,
            'time_parsed': time_parsed,
            'image_url': image_url,
            'content': extracted.get('content'),
            'source': source,
            'sentiment': ai.sentiment
        }
        
        # Step 4: Save to database
        if save_to_database(news_data, stock_symbol):
            saved_count += 1
        else:
            duplicate_count += 1
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"✅ Total found: {len(news_items)}")
    print(f"💾 Saved to database: {saved_count}")
    print(f"⚠️  Duplicates skipped: {duplicate_count}")
    print("="*80 + "\n")


def main():
    """Main function - chỉnh cấu hình ở đầu file"""   
    crawl_news(
        query=SEARCH_QUERY,
        stock_symbol=STOCK_SYMBOL,
        time_range=TIME_RANGE,
        num_results=NUM_RESULTS,
        max_results=MAX_RESULTS
    )


if __name__ == "__main__":
    main()
