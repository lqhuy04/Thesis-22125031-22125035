"""
scheduler.py - Articles Update Scheduler
Chạy liên tục, quản lý 1 tác vụ:
  1. Fetch articles mới (macro, category, stock) → chạy 1 lần mỗi ngày vào cuối ngày

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

# Giờ chạy (giờ Việt Nam) — cuối ngày, sau khi thị trường đóng cửa
ARTICLES_RUN_H, ARTICLES_RUN_M = 23, 0

articles_done_date: str = ""   # "YYYY-MM-DD" của ngày đã chạy article update


def now_vn() -> datetime:
    return datetime.now(VN_TZ)


def hm(dt: datetime) -> tuple[int, int]:
    return dt.hour, dt.minute


# ─────────────────────────────────────────────────────────────────────────────
# ARTICLE UPDATE PROCESSES
# ─────────────────────────────────────────────────────────────────────────────

def run_script(script_name: str) -> None:
    """Chạy một script update_articles và chờ hoàn tất."""
    try:
        logger.info(f"▶ Running {script_name}")
        proc = subprocess.Popen(
            [sys.executable, script_name],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

        proc.wait()

        if proc.returncode == 0:
            logger.info(f"✅ {script_name} completed successfully")
        else:
            logger.error(f"❌ {script_name} exited with code {proc.returncode}")

    except Exception as e:
        logger.error(f"Error running {script_name}: {e}")


def run_daily_updates():
    """Chạy lần lượt 3 job update articles hàng ngày."""
    run_script("update_macro_articles.py")
    run_script("update_category_articles.py")
    run_script("update_stock_articles.py")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────────────────────────

def main():
    global articles_done_date
    logger.info("Scheduler started. Waiting for daily schedule (VN UTC+7)...")

    while True:
        now = now_vn()
        h, m = hm(now)
        current_date = now.strftime("%Y-%m-%d")

        # Chạy fetch articles một lần mỗi ngày vào cuối ngày (giờ cấu hình)
        if (h, m) >= (ARTICLES_RUN_H, ARTICLES_RUN_M):
            if articles_done_date != current_date:
                logger.info(f"🔄 Triggering daily article update for {current_date} at {h:02d}:{m:02d}")
                articles_done_date = current_date
                run_daily_updates()

        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    main()
