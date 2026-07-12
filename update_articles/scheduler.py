"""
scheduler.py - Articles Update Scheduler
Chạy liên tục, quản lý 1 tác vụ:
  1. Fetch articles mới (macro, category, stock) → chạy 1 lần mỗi tuần vào cuối tuần

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

# Ngày trong tuần chạy (0=Mon ... 5=Sat, 6=Sun) — mặc định thứ Bảy (cuối tuần)
ARTICLES_RUN_WEEKDAY = 5
# Giờ chạy (giờ Việt Nam)
ARTICLES_RUN_H, ARTICLES_RUN_M = 23, 0

articles_done_week: str = ""   # "YYYY-Www" của tuần đã chạy article update


def now_vn() -> datetime:
    return datetime.now(VN_TZ)


def hm(dt: datetime) -> tuple[int, int]:
    return dt.hour, dt.minute


def week_key(dt: datetime) -> str:
    """Khóa định danh tuần theo lịch ISO, vd '2026-W28'."""
    iso = dt.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


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


def run_weekly_updates():
    """Chạy lần lượt 3 job update articles hàng tuần."""
    run_script("update_macro_articles.py")
    run_script("update_category_articles.py")
    run_script("update_stock_articles.py")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────────────────────────

def main():
    global articles_done_week
    logger.info("Scheduler started. Waiting for weekly schedule (VN UTC+7)...")

    while True:
        now = now_vn()
        h, m = hm(now)

        # Chạy fetch articles một lần mỗi tuần vào cuối tuần (ngày + giờ cấu hình)
        if now.weekday() == ARTICLES_RUN_WEEKDAY and (h, m) >= (ARTICLES_RUN_H, ARTICLES_RUN_M):
            current_week = week_key(now)
            if articles_done_week != current_week:
                logger.info(f"🔄 Triggering weekly article update for {current_week} at {h:02d}:{m:02d}")
                articles_done_week = current_week
                run_weekly_updates()

        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    main()
