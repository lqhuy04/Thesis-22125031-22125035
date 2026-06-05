import os
import time
import logging
import requests
from dotenv import load_dotenv
from supabase import create_client
from typing import Optional, Any

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class Config:
    serper_url = os.getenv("SERPER_API_URL", "https://google.serper.dev")
    serper_key = os.getenv("SERPER_API_KEY", "")
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_KEY", "")
    rate_sleep = float(os.getenv("CRAWL_LOGO_SLEEP", "1.1"))


config = Config()


if not config.supabase_url or not config.supabase_key:
    logger.error("SUPABASE_URL or SUPABASE_KEY not set in environment")
    raise SystemExit(1)


supabase = create_client(config.supabase_url, config.supabase_key)


def search_serper_images(query: str, num: int = 10) -> Optional[str]:
    """Call Serper search with type=images and return first image URL if found."""
    if not config.serper_key:
        logger.error("SERPER_API_KEY not set in environment")
        return None

    url = f"{config.serper_url}/search"
    payload = {"q": query, "type": "images", "num": num}
    headers = {"X-API-KEY": config.serper_key, "Content-Type": "application/json"}

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        # Serper image search returns images array with 'imageUrl' field
        images = data.get("images", [])
        if images and len(images) > 0:
            first_image = images[0]
            img_url = first_image.get("imageUrl")
            if img_url:
                return img_url

        logger.debug("No image URL found in Serper response for query: %s", query)
        return None

    except Exception as e:
        logger.error("Serper image search error for '%s': %s", query, e)
        return None


def fetch_bi_profiles() -> list[dict]:
    """Fetch all BI_Profile rows by paginating through results."""
    all_rows = []
    page = 0
    page_size = 1000
    
    try:
        while True:
            offset = page * page_size
            res = supabase.table("BI_Profile").select("id,symbol,logo,company_name").offset(offset).limit(page_size).execute()
            rows = res.data if res.data else []
            
            if not rows:
                break
            
            all_rows.extend(rows)
            logger.debug(f"Fetched page {page + 1}: {len(rows)} rows (total: {len(all_rows)})")
            
            if len(rows) < page_size:
                break
            
            page += 1
        
        return all_rows
    except Exception as e:
        logger.error("Error fetching BI_Profile rows: %s", e)
        return []


def update_logo(record_id: Any, logo_url: str) -> bool:
    try:
        res = supabase.table("BI_Profile").update({"logo": logo_url}).eq("id", record_id).execute()
        if res and getattr(res, "data", None):
            return True
        return False
    except Exception as e:
        logger.error("Error updating logo for id %s: %s", record_id, e)
        return False


def main(limit: Optional[int] = None, symbol: Optional[str] = None):
    logger.info("Starting BI_Profile logo fetcher (Serper)")

    if symbol:
        # Test mode: search for specific symbol only
        logger.info("Test mode: searching for symbol %s", symbol)
        rows = fetch_bi_profiles()
        rows = [row for row in rows if row.get("symbol", "").strip().upper() == symbol.upper()]
        if not rows:
            logger.info("Symbol %s not found in BI_Profile. Exiting.", symbol)
            return
    else:
        rows = fetch_bi_profiles()
        if not rows:
            logger.info("No BI_Profile rows found. Exiting.")
            return

    logger.info("Loaded %d BI_Profile rows", len(rows))

    updated = 0
    skipped = 0
    processed = 0

    for row in rows:
        if limit and processed >= limit:
            break

        processed += 1
        _id = row.get("id")
        symbol = (row.get("symbol") or "").strip()
        company_name = (row.get("company_name") or "").strip()

        if not symbol:
            logger.debug("Skipping row id %s: no symbol", _id)
            skipped += 1
            continue

        query = f"logo {company_name} moi nhat cafef"
        logger.info("Searching logo for %s: %s", symbol, query)
        img_url = search_serper_images(query)

        if not img_url:
            logger.info("No image found for %s", symbol)
            time.sleep(config.rate_sleep)
            continue

        ok = update_logo(_id, img_url)
        if ok:
            logger.info("Updated logo for %s -> %s", symbol, img_url)
            updated += 1
        else:
            logger.error("Failed to update logo for %s", symbol)

        time.sleep(config.rate_sleep)

    logger.info("Done. processed=%d updated=%d skipped=%d", processed, updated, skipped)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None, help="Limit number of rows to process")
    p.add_argument("--symbol", type=str, default=None, help="Test with specific symbol (e.g., VHM)")
    args = p.parse_args()
    main(limit=args.limit, symbol=args.symbol)
