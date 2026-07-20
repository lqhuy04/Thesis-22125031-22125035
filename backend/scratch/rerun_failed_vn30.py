"""Sequentially rerun failed/quota-limited VN30 backtests (excluding MSN)."""

from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
STATUS_PATH = os.path.join(SCRIPT_DIR, "rerun_failed_vn30_status.log")

# Make `app` and `agentic_ai` importable and ensure backend/.env is loaded.
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

# Windows terminals may otherwise use cp1252 and fail on Vietnamese output.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.models.backtest_pipeline_schemas import BacktestPipelineRequest
from app.services.backtest_pipeline_service import run_backtest_pipeline


SYMBOLS = [
    # Missing from vn30_stats.json because the previous run failed.
    "FPT",
    "HDB",
    "SAB",
    # Zero-trade results produced after the API quota was exhausted.
    "SSB",
    "SSI",
    "STB",
    "TCB",
    "TPB",
    "VCB",
    "VJC",
    "VHM",
    "VIC",
    "VNM",
    "VPB",
    "VRE",
    "VIB",
    "VPL",
]


def emit(event: str, **details: object) -> None:
    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "event": event,
        **details,
    }
    line = json.dumps(record, ensure_ascii=False)
    print(line, flush=True)
    with open(STATUS_PATH, "a", encoding="utf-8") as status_file:
        status_file.write(line + "\n")


def main() -> None:
    # Start a fresh status log for this run.
    with open(STATUS_PATH, "w", encoding="utf-8"):
        pass

    emit("batch_started", symbols=SYMBOLS, excluded=["MSN"])
    succeeded: list[str] = []
    failed: list[str] = []

    for index, symbol in enumerate(SYMBOLS, start=1):
        emit("symbol_started", symbol=symbol, index=index, total=len(SYMBOLS))
        try:
            result = run_backtest_pipeline(
                BacktestPipelineRequest(
                    symbol=symbol,
                    start_date="2023-01-01",
                    end_date="2025-12-31",
                    market_symbol="VNINDEX",
                    min_signal_score=3,
                    max_hold_candles=20,
                    transaction_cost_pct=0.0015,
                    one_minute_lookback_days=30,
                    use_intraday=True,
                    exit_on_score_drop=False,
                    mode="auto",
                )
            )
            metrics = result.get("full_metrics", {})
            succeeded.append(symbol)
            emit(
                "symbol_completed",
                symbol=symbol,
                n_trades=metrics.get("volume", {}).get("n_trades", 0),
                total_return=metrics.get("pnl", {}).get("total_return", 0.0),
            )
        except Exception as error:
            failed.append(symbol)
            emit(
                "symbol_failed",
                symbol=symbol,
                error=f"{type(error).__name__}: {error}",
                traceback=traceback.format_exc(),
            )

    emit("batch_completed", succeeded=succeeded, failed=failed)


if __name__ == "__main__":
    main()
