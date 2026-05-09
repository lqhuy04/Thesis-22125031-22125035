"""
scheduler.py - Articles Update Scheduler
Chạy liên tục, quản lý 1 tác vụ:
  1. Fetch articles for today → chạy 1 lần lúc 00:00 (nửa đêm)

Giờ Việt Nam = UTC+7
"""

import time
import logging
import subprocess
import sys
from datetime import datetime, timezone, timedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

VN_TZ = timezone(timedelta(hours=7))

# Giờ chạy (giờ Việt Nam)
ARTICLES_RUN_H,  ARTICLES_RUN_M  = 0, 0  # Midnight

articles_process: subprocess.Popen | None = None
articles_done_today: str = ""   # "YYYY-MM-DD" của ngày đã chạy article fetching


def now_vn() -> datetime:
    return datetime.now(VN_TZ)


def hm(dt: datetime) -> tuple[int, int]:
    return dt.hour, dt.minute


# ─────────────────────────────────────────────────────────────────────────────
# ARTICLE FETCH PROCESS
# ─────────────────────────────────────────────────────────────────────────────

def run_article_fetch():
    """Chạy websocket_articles_1d.py để fetch articles cho hôm nay."""
    global articles_process
    
    try:
        logger.info("▶ Running websocket_articles_1d.py")
        articles_process = subprocess.Popen(
            [sys.executable, "websocket_articles_1d.py"],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        
        # Wait for completion
        articles_process.wait()
        
        if articles_process.returncode == 0:
            logger.info("✅ websocket_articles_1d.py completed successfully")
        else:
            logger.error(f"❌ websocket_articles_1d.py exited with code {articles_process.returncode}")
    
    except Exception as e:
        logger.error(f"Error running article fetch: {e}")
    finally:
        articles_process = None


# ─────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────────────────────────

def main():
    global articles_done_today
    logger.info("Scheduler started. Waiting for midnight (VN UTC+7)...")

    while True:
        now   = now_vn()
        today = now.date().isoformat()
        h, m  = hm(now)

        # 1️⃣  Chạy fetch articles đúng 1 lần mỗi ngày lúc >= 00:00 (nửa đêm)
        if (h, m) >= (ARTICLES_RUN_H, ARTICLES_RUN_M):
            if articles_done_today != today:
                logger.info(f"🔄 Triggering article fetch at {h:02d}:{m:02d}")
                articles_done_today = today
                run_article_fetch()

        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    main()
