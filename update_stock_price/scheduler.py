"""
scheduler.py
Chạy liên tục, quản lý 4 tác vụ:
  1. WebSocket 1m stream  → mở đầu phiên (9:00), đóng cuối phiên (15:30)
  2. WebSocket 1d stream  → mở đầu phiên (9:00), đóng cuối phiên (15:30)
  3. Standardize 1m       → chạy 1 lần lúc 15:35 (sau khi stream đóng)
  4. Standardize 1d       → chạy 1 lần lúc 15:35 (cùng lúc với 1m)

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

# Giờ giao dịch (giờ Việt Nam)
MARKET_OPEN_H,  MARKET_OPEN_M  = 9,  0
MARKET_CLOSE_H, MARKET_CLOSE_M = 15, 00
STANDARDIZE_H,  STANDARDIZE_M  = 15, 5

# Ngày trong tuần giao dịch (0=Mon ... 4=Fri)
TRADING_DAYS = {0, 1, 2, 3, 4}

ws_1m_process:          subprocess.Popen | None = None
ws_1d_process:          subprocess.Popen | None = None
standardize_done_today: str = ""   # "YYYY-MM-DD" của ngày đã chạy standardize


def now_vn() -> datetime:
    return datetime.now(VN_TZ)


def is_trading_day(dt: datetime) -> bool:
    return dt.weekday() in TRADING_DAYS


def hm(dt: datetime) -> tuple[int, int]:
    return dt.hour, dt.minute


# ─────────────────────────────────────────────────────────────────────────────
# WEBSOCKET PROCESSES
# ─────────────────────────────────────────────────────────────────────────────

def start_websockets():
    global ws_1m_process, ws_1d_process

    if not ws_1m_process or ws_1m_process.poll() is not None:
        logger.info("▶ Starting websocket_stock_price_1m.py")
        ws_1m_process = subprocess.Popen(
            [sys.executable, "websocket_stock_price_1m.py"],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

    if not ws_1d_process or ws_1d_process.poll() is not None:
        logger.info("▶ Starting websocket_stock_price_1d.py")
        ws_1d_process = subprocess.Popen(
            [sys.executable, "websocket_stock_price_1d.py"],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )


def stop_websockets():
    global ws_1m_process, ws_1d_process

    for name, proc in [("1m", ws_1m_process), ("1d", ws_1d_process)]:
        if proc and proc.poll() is None:
            logger.info(f"⏹ Stopping WebSocket {name} process")
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()

    ws_1m_process = None
    ws_1d_process = None


# ─────────────────────────────────────────────────────────────────────────────
# STANDARDIZE
# ─────────────────────────────────────────────────────────────────────────────

def run_standardize():
    """Chạy song song cả 1m và 1d, đợi cả 2 xong mới tiếp tục."""
    scripts = [
        "standardize_stock_price_1m.py",
        "standardize_stock_price_1d.py",
    ]

    procs = []
    for script in scripts:
        logger.info(f"▶ Running {script}")
        p = subprocess.Popen(
            [sys.executable, script],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        procs.append((script, p))

    for script, p in procs:
        p.wait()
        if p.returncode == 0:
            logger.info(f"✅ {script} done")
        else:
            logger.error(f"❌ {script} exited with code {p.returncode}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────────────────────────

def main():
    global standardize_done_today
    logger.info("Scheduler started. Waiting for market hours (VN UTC+7)...")

    while True:
        now   = now_vn()
        today = now.date().isoformat()
        h, m  = hm(now)

        if is_trading_day(now):
            in_session = (
                (h, m) >= (MARKET_OPEN_H,  MARKET_OPEN_M) and
                (h, m) <  (MARKET_CLOSE_H, MARKET_CLOSE_M)
            )
            after_close = (h, m) >= (MARKET_CLOSE_H, MARKET_CLOSE_M)

            # 1️⃣  Trong phiên → đảm bảo cả 2 WebSocket đang chạy
            if in_session:
                start_websockets()

            # 2️⃣  Hết phiên → tắt cả 2 WebSocket
            elif after_close:
                stop_websockets()

                # 3️⃣  Chạy standardize đúng 1 lần lúc ≥ 15:35
                if (
                    standardize_done_today != today and
                    (h, m) >= (STANDARDIZE_H, STANDARDIZE_M)
                ):
                    run_standardize()
                    standardize_done_today = today

            # Trước giờ mở → chắc chắn WebSocket không chạy
            else:
                stop_websockets()

        else:
            # Cuối tuần / ngày nghỉ
            stop_websockets()

        time.sleep(30)  # kiểm tra mỗi 30 giây


if __name__ == "__main__":
    main()