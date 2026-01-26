"""
StockBiz News Crawler with Database Integration
Crawls financial news from https://stockbiz.vn/doanh-nghiep and saves to Supabase
Extracts full article content from each article URL
"""

import time
import json
import sys
import os
import re
from datetime import datetime
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

# Load environment variables from app/.env before importing app modules
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '..', 'app', '.env')
load_dotenv(env_path)

# Add parent directory to path to import from app
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.models.news_schemas import NewsCreate
from app.services.news_db_service import NewsDBService
import asyncio


class StockBizCrawler:
    def __init__(self, headless: bool = True, save_to_db: bool = True, extract_content: bool = True, clear_before_save: bool = False):
        """
        Initialize the StockBiz crawler
        
        Args:
            headless: Run browser in headless mode (no GUI)
            save_to_db: Save crawled news to database
            extract_content: Extract full article content from each URL
            clear_before_save: Clear existing news from database before saving new data
        """
        self.base_url = "https://stockbiz.vn/doanh-nghiep"
        self.driver = None
        self.headless = headless
        self.save_to_db = save_to_db
        self.extract_content = extract_content
        self.clear_before_save = clear_before_save
        self.news_data = []
        
    def setup_driver(self):
        """Setup Chrome WebDriver with options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        
    def scroll_and_collect(self, check_interval: float = 1.0, stop_at_latest: bool = False):
        """
        Monitor and collect items as user scrolls manually
        
        Args:
            check_interval: Time between checks for new items (seconds)
            stop_at_latest: Stop when reaching a news item already in database
        """
        seen_links = set()  # Track unique news items by link
        
        # Get latest news link from database if stop_at_latest is enabled
        latest_db_link = None
        if stop_at_latest and self.save_to_db:
            try:
                latest_db_link = asyncio.run(NewsDBService.get_latest_news_link())
                if latest_db_link:
                    print(f"Will stop when reaching: {latest_db_link[:80]}...")
            except Exception as e:
                print(f"Could not fetch latest news link: {e}")
        
        print("\n" + "="*60)
        print("MANUAL SCROLL MODE - Active Monitoring")
        print("="*60)
        print("📜 Scroll the page with your mouse/trackpad")
        print("🔍 The crawler is watching and will collect items automatically")
        print("🛑 Close the browser window when you're done scrolling")
        print("="*60 + "\n")
        
        last_count = 0
        check_count = 0
        
        while True:
            # Check if browser is still open
            try:
                _ = self.driver.current_url
            except Exception:
                print("\n✓ Browser closed. Stopping collection.")
                print(f"Total items collected: {len(self.news_data)}")
                break
            
            # Collect items from current view
            try:
                news_items = self.driver.find_elements(By.CSS_SELECTOR, '[data-test-id="virtuoso-item-list"] > div[data-index]')
            except Exception:
                print("\n✓ Browser closed. Stopping collection.")
                break
            
            # Parse visible items
            items_added = 0
            for item in news_items:
                news_data = self.parse_news_item(item)
                if news_data and news_data['link'] not in seen_links:
                    seen_links.add(news_data['link'])
                    
                    # Check if we've reached the latest news in database
                    if stop_at_latest and latest_db_link and news_data['link'] == latest_db_link:
                        print(f"\n✓ Reached latest news in database! ({len(self.news_data)} items)")
                        print("Continuing to monitor for more news as you scroll...")
                        stop_at_latest = False  # Only show once
                    
                    self.news_data.append(news_data)
                    items_added += 1
                    print(f"  + [{len(self.news_data)}] {news_data['title'][:65]}...")
            
            # Show periodic status update
            if items_added > 0:
                last_count = len(self.news_data)
            
            check_count += 1
            if check_count % 5 == 0:  # Every 5 checks, show status
                print(f"  → Monitoring... ({len(self.news_data)} items collected)")
            
            # Wait before next check
            time.sleep(check_interval)
        
        # Extract full content from each article if enabled
        if self.extract_content and self.news_data:
            print(f"\n{'='*60}")
            print(f"Extracting full content from {len(self.news_data)} articles...")
            print(f"Note: This will reopen browser if you closed it")
            print(f"{'='*60}\n")
            
            for idx, news in enumerate(self.news_data, 1):
                print(f"[{idx}/{len(self.news_data)}] {news['title'][:60]}...")
                article_content = self.extract_article_content(news['link'])
                if article_content:
                    news.update(article_content)
                    if article_content['is_content_extracted']:
                        # Count total blocks extracted
                        num_blocks = len(article_content['content']['blocks']) if article_content['content'] else 0
                        print(f"  ✓ Extracted {num_blocks} content blocks")
                    else:
                        print(f"  ⚠ Could not extract content")
                time.sleep(1)  # Be nice to the server
    
    def parse_time(self, time_str: str) -> str:
        """
        Parse Vietnamese time string to standard format
        
        Args:
            time_str: Time string like "Hôm qua 23:10" or "2 giờ trước"
            
        Returns:
            Formatted datetime string
        """
        try:
            time_str = time_str.strip()
            
            if "Hôm qua" in time_str:
                # Yesterday
                time_part = time_str.split()[-1]  # Get "23:10"
                return f"Yesterday {time_part}"
            elif "giờ trước" in time_str or "phút trước" in time_str:
                # Hours or minutes ago
                return time_str
            else:
                return time_str
        except Exception as e:
            print(f"Error parsing time: {e}")
            return time_str
    
    def parse_news_item(self, item_element) -> Optional[Dict]:
        """
        Parse a single news item element
        
        Args:
            item_element: Selenium WebElement or BeautifulSoup element
            
        Returns:
            Dictionary with news data or None if parsing fails
        """
        try:
            html = item_element.get_attribute('outerHTML') if hasattr(item_element, 'get_attribute') else str(item_element)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title and link
            title_element = soup.select_one('div.text-lg.font-semibold a')
            if not title_element:
                return None
                
            title = title_element.get_text(strip=True)
            link = title_element.get('href', '')
            if link and not link.startswith('http'):
                link = f"https://stockbiz.vn{link}"
            
            # Extract image
            img_element = soup.select_one('img[alt]')
            image_url = img_element.get('src', '') if img_element else ''
            
            # Extract stock symbol and price change
            stock_element = soup.select_one('span.font-semibold')
            stock_symbol = ''
            
            if stock_element:
                stock_text = stock_element.get_text(strip=True)
                # Split by price change span
                price_span = stock_element.find('span')
                if price_span:
                    stock_symbol = stock_text.split(price_span.get_text())[0].strip()
                else:
                    stock_symbol = stock_text
            
            # Extract description
            desc_element = soup.select_one('div.mb-2.line-clamp-2, div.mb-2.line-clamp-3')
            description = desc_element.get_text(strip=True) if desc_element else ''
            
            # Extract time
            time_element = soup.select_one('span.text-gray-400')
            time_str = time_element.get_text(strip=True) if time_element else ''
            parsed_time = self.parse_time(time_str)
            
            news_item = {
                'title': title,
                'link': link,
                'stock_symbol': stock_symbol if stock_symbol else None,
                'description': description,
                'time': parsed_time,
                'image_url': image_url
            }
            
            return news_item
            
        except Exception as e:
            print(f"Error parsing news item: {e}")
            return None
    
    def extract_article_content(self, article_url: str) -> Optional[Dict]:
        """
        Extract full content from article URL as structured blocks
        
        Args:
            article_url: Full URL to the article
            
        Returns:
            Dictionary with structured content, author, images, tags, related_stocks
        """
        try:
            print(f"  → Extracting content from: {article_url[:70]}...")
            
            # Check if driver is still valid, if not create a new one
            try:
                _ = self.driver.current_url
            except:
                print(f"  ⚠ Browser closed, reopening for content extraction...")
                self.setup_driver()
            
            # Navigate to article page
            self.driver.get(article_url)
            time.sleep(2)  # Wait for page to load
            
            # Get page HTML
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract author
            author = None
            author_element = soup.select_one('div.author, span.author, a.author, [class*="author"]')
            if author_element:
                author = author_element.get_text(strip=True)
            
            # Extract structured content as blocks
            content_blocks = []
            all_text_content = []  # For stock symbol extraction
            
            # Try different content container selectors
            content_container_selectors = [
                'div.article-content',
                'div.post-content',
                'div.entry-content',
                'article div.content',
                'div[class*="content"]',
                'article'
            ]
            
            content_container = None
            for selector in content_container_selectors:
                container = soup.select_one(selector)
                if container:
                    content_container = container
                    break
            
            if content_container:
                # Process children elements in order to maintain structure
                for element in content_container.children:
                    if not element.name:  # Skip text nodes
                        continue
                    
                    # Handle paragraphs (text blocks)
                    if element.name in ['p', 'div', 'span']:
                        # Check if element contains an image
                        img = element.find('img')
                        if img:
                            # Add image block
                            img_url = img.get('src') or img.get('data-src')
                            if img_url and img_url.startswith('http'):
                                caption = img.get('alt') or img.get('title') or ''
                                content_blocks.append({
                                    'type': 'image',
                                    'url': img_url,
                                    'caption': caption,
                                    'alt': caption
                                })
                        
                        # Get text content
                        text = element.get_text(strip=True)
                        if text and len(text) > 30:  # Filter out short fragments
                            content_blocks.append({
                                'type': 'text',
                                'content': text
                            })
                            all_text_content.append(text)
                    
                    # Handle standalone images
                    elif element.name == 'img':
                        img_url = element.get('src') or element.get('data-src')
                        if img_url and img_url.startswith('http'):
                            caption = element.get('alt') or element.get('title') or ''
                            content_blocks.append({
                                'type': 'image',
                                'url': img_url,
                                'caption': caption,
                                'alt': caption
                            })
                    
                    # Handle figure elements (typically contain images with captions)
                    elif element.name == 'figure':
                        img = element.find('img')
                        figcaption = element.find('figcaption')
                        
                        if img:
                            img_url = img.get('src') or img.get('data-src')
                            if img_url and img_url.startswith('http'):
                                caption = figcaption.get_text(strip=True) if figcaption else (img.get('alt') or '')
                                content_blocks.append({
                                    'type': 'image',
                                    'url': img_url,
                                    'caption': caption,
                                    'alt': img.get('alt') or caption
                                })
            
            # Create structured content
            structured_content = {'blocks': content_blocks} if content_blocks else None
            
            # Extract all images for article_images array (legacy field)
            article_images = []
            for block in content_blocks:
                if block['type'] == 'image':
                    article_images.append(block['url'])
            
            # Extract tags/categories
            tags = []
            tag_elements = soup.select('a[rel="tag"], .tags a, .categories a, [class*="tag"] a')
            for tag in tag_elements:
                tag_text = tag.get_text(strip=True)
                if tag_text:
                    tags.append(tag_text)
            
            return {
                'content': structured_content,
                'author': author,
                'article_images': list(set(article_images))[:10],  # Limit to 10 unique images
                'tags': list(set(tags))[:10],  # Limit to 10 unique tags
                'is_content_extracted': structured_content is not None
            }
            
        except Exception as e:
            print(f"  ✗ Error extracting article content: {e}")
            return {
                'content': None,
                'author': None,
                'article_images': [],
                'tags': [],
                'is_content_extracted': False
            }
    
    def crawl(self, check_interval: float = 1.0, stop_at_latest: bool = False) -> List[Dict]:
        """
        Main crawl method with manual scrolling
        
        Args:
            check_interval: How often to check for new items (seconds)
            stop_at_latest: Stop when reaching the latest news in database
            
        Returns:
            List of news items
        """
        try:
            print(f"Starting crawler for {self.base_url}")
            self.setup_driver()
            
            # Navigate to the page
            print("Loading page...")
            self.driver.get(self.base_url)
            
            # Wait for the virtuoso list to load
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test-id="virtuoso-item-list"]')))
            
            print("Page loaded successfully")
            
            # Monitor and collect items as user scrolls manually
            print(f"Starting manual scroll monitoring...")
            print("Note: Site uses virtual scrolling - scroll with your mouse!\n")
            self.scroll_and_collect(check_interval=check_interval, stop_at_latest=stop_at_latest)
            
            print(f"\nSuccessfully crawled {len(self.news_data)} unique news items")
            return self.news_data
            
        except Exception as e:
            print(f"Error during crawling: {e}")
            return self.news_data
        
        finally:
            if self.driver:
                self.driver.quit()
    
    async def save_to_database(self) -> Dict[str, int]:
        """
        Save crawled news to database
        
        Returns:
            Dictionary with created and skipped counts
        """
        if not self.news_data:
            return {"created": 0, "skipped": 0}
        
        # Clear table if requested
        if self.clear_before_save:
            print("\n⚠️  Clearing existing news from database...")
            try:
                from supabase import create_client
                from app.config import get_settings
                settings = get_settings()
                supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                supabase.table("financial_news").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
                print("✓ Table cleared successfully\n")
            except Exception as e:
                print(f"✗ Error clearing table: {e}\n")
        
        print(f"\nSaving {len(self.news_data)} news items to database...")
        
        # Convert to NewsCreate objects
        news_create_list = [NewsCreate(**news) for news in self.news_data]
        
        # Bulk insert
        result = await NewsDBService.bulk_create_news(news_create_list)
        
        print(f"Created {result['created']} new items, skipped {result['skipped']} duplicates")
        return result


async def main():
    """Main function to run the crawler"""
    # Create crawler instance
    # Set save_to_db=True to save to database, headless=False to see browser
    # Set extract_content=True to extract full article content (slower but more complete)
    # Set clear_before_save=True to clear existing news before saving (fresh start)
    crawler = StockBizCrawler(
        headless=False, 
        save_to_db=True,
        extract_content=True,      # Enable full content extraction
        clear_before_save=True     # Set True to clear table before saving
    )
    
    # Crawl news with manual scrolling
    # You scroll the page yourself, the crawler monitors and collects items automatically
    # stop_at_latest=True will notify when reaching a news item already in database
    # check_interval controls how often it checks for new items (in seconds)
    # Close the browser window when you're done scrolling
    news_data = crawler.crawl(check_interval=1.0, stop_at_latest=True)
    
    # Save to database if enabled
    if crawler.save_to_db and news_data:
        result = await crawler.save_to_database()
        print("\n" + "="*50)
        print("DATABASE SAVE SUMMARY")
        print("="*50)
        print(f"Total crawled: {len(news_data)}")
        print(f"New items saved: {result['created']}")
        print(f"Duplicates skipped: {result['skipped']}")
        
        # Print sample
        if news_data:
            print("\nSample news item:")
            print(json.dumps(news_data[0], indent=2, ensure_ascii=False))
    elif not news_data:
        print("No data was crawled")


if __name__ == "__main__":
    asyncio.run(main())