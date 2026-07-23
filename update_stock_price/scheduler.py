"""
scheduler.py
Chạy liên tục, quản lý các tiến trình cập nhật giá:
  1. WebSocket 1m stream     → mở đầu phiên (9:00), đóng cuối phiên (15:00)
  2. WebSocket 1d stream     → mở đầu phiên (9:00), đóng cuối phiên (15:00)
  3. MarketIndex 1m poller   → mở đầu phiên (9:00), đóng cuối phiên (15:00)
  4. MarketIndex 1d poller   → mở đầu phiên (9:00), đóng cuối phiên (15:00)
  5. Standardize stock 1m    → chạy 1 lần lúc 15:05 (sau khi stream đóng)
  6. Standardize stock 1d    → chạy tuần tự sau standardize stock 1m
  7. Standardize index 1m    → chạy tuần tự sau standardize stock 1d
  8. Standardize index 1d    → chạy tuần tự sau standardize index 1m

Giờ Việt Nam = UTC+7
"""

import time
import logging
import subprocess
import sys
import signal
from datetime import datetime, timezone, timedelta
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent

VN_TZ = timezone(timedelta(hours=7))

# Giờ giao dịch (giờ Việt Nam)
MARKET_OPEN_H,  MARKET_OPEN_M  = 9,  0
MARKET_CLOSE_H, MARKET_CLOSE_M = 15, 00
STANDARDIZE_H,  STANDARDIZE_M  = 15, 5

# Ngày trong tuần giao dịch (0=Mon ... 4=Fri)
TRADING_DAYS = {0, 1, 2, 3, 4}

ws_1m_process:          subprocess.Popen | None = None
ws_1d_process:          subprocess.Popen | None = None
ws_market_index_1m_process: subprocess.Popen | None = None
ws_market_index_1d_process: subprocess.Popen | None = None
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
    global ws_market_index_1m_process, ws_market_index_1d_process

    if not ws_1m_process or ws_1m_process.poll() is not None:
        if ws_1m_process and ws_1m_process.poll() is not None:
            logger.warning(f"⚠ WebSocket 1m crashed with return code {ws_1m_process.returncode}")
        logger.info("▶ Starting websocket_stock_price_1m.py")
        ws_1m_process = subprocess.Popen(
            [sys.executable, "-u", str(BASE_DIR / "websocket" / "websocket_stock_price_1m.py")],
            cwd=str(BASE_DIR),
            text=True,
            bufsize=1,
        )

    if not ws_1d_process or ws_1d_process.poll() is not None:
        if ws_1d_process and ws_1d_process.poll() is not None:
            logger.warning(f"⚠ WebSocket 1d crashed with return code {ws_1d_process.returncode}")
        logger.info("▶ Starting websocket_stock_price_1d.py")
        ws_1d_process = subprocess.Popen(
            [sys.executable, "-u", str(BASE_DIR / "websocket" / "websocket_stock_price_1d.py")],
            cwd=str(BASE_DIR),
            text=True,
            bufsize=1,
        )


    if (
        not ws_market_index_1m_process
        or ws_market_index_1m_process.poll() is not None
    ):
        if (
            ws_market_index_1m_process
            and ws_market_index_1m_process.poll() is not None
        ):
            logger.warning(
                "⚠ MarketIndex 1m poller crashed with return code "
                f"{ws_market_index_1m_process.returncode}"
            )
        logger.info("▶ Starting websocket_marketIndex_value_1m.py")
        ws_market_index_1m_process = subprocess.Popen(
            [
                sys.executable,
                "-u",
                str(
                    BASE_DIR
                    / "websocket"
                    / "websocket_marketIndex_value_1m.py"
                ),
            ],
            cwd=str(BASE_DIR),
            text=True,
            bufsize=1,
        )

    if (
        not ws_market_index_1d_process
        or ws_market_index_1d_process.poll() is not None
    ):
        if (
            ws_market_index_1d_process
            and ws_market_index_1d_process.poll() is not None
        ):
            logger.warning(
                "⚠ MarketIndex 1d poller crashed with return code "
                f"{ws_market_index_1d_process.returncode}"
            )
        logger.info("▶ Starting websocket_marketIndex_value_1d.py")
        ws_market_index_1d_process = subprocess.Popen(
            [
                sys.executable,
                "-u",
                str(
                    BASE_DIR
                    / "websocket"
                    / "websocket_marketIndex_value_1d.py"
                ),
            ],
            cwd=str(BASE_DIR),
            text=True,
            bufsize=1,
        )


def stop_websockets():
    global ws_1m_process, ws_1d_process
    global ws_market_index_1m_process, ws_market_index_1d_process

    processes = [
        ("stock 1m", ws_1m_process),
        ("stock 1d", ws_1d_process),
        ("MarketIndex 1m", ws_market_index_1m_process),
        ("MarketIndex 1d", ws_market_index_1d_process),
    ]
    for name, proc in processes:
        if proc and proc.poll() is None:
            logger.info(f"⏹ Stopping {name} process")
            try:
                proc.send_signal(signal.SIGINT)
            except Exception as e:
                logger.warning(
                    f"⚠ Failed to send SIGINT to {name}: {e}; "
                    "falling back to terminate()"
                )
                proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()

    ws_1m_process = None
    ws_1d_process = None
    ws_market_index_1m_process = None
    ws_market_index_1d_process = None


# ─────────────────────────────────────────────────────────────────────────────
# STANDARDIZE
# ─────────────────────────────────────────────────────────────────────────────

def run_standardize():
    """Chạy tuần tự các job standardize stock và MarketIndex.

    Chạy tuần tự thay vì song song để tránh các script cùng gọi SSI một lúc gây
    vượt rate-limit.
    """
    scripts = [
        BASE_DIR / "standardize" / "standardize_stock_price_1m.py",
        BASE_DIR / "standardize" / "standardize_stock_price_1d.py",
        BASE_DIR / "standardize" / "standardize_marketIndex_value_1m.py",
        BASE_DIR / "standardize" / "standardize_marketIndex_value_1d.py",
    ]

    for script_path in scripts:
        logger.info(f"▶ Running {script_path.name}")
        p = subprocess.Popen(
            [sys.executable, "-u", str(script_path)],
            cwd=str(BASE_DIR),
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        p.wait()
        if p.returncode == 0:
            logger.info(f"✅ {script_path.name} done")
        else:
            logger.error(f"❌ {script_path.name} exited with code {p.returncode}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────────────────────────

def main():
    global standardize_done_today
    logger.info("Scheduler started. Waiting for market hours (VN UTC+7)...")

    while True:
        try:
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

                    # 3️⃣  Chạy standardize đúng 1 lần lúc ≥ 15:05
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
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}", exc_info=True)
            time.sleep(30)


if __name__ == "__main__":
    main()
