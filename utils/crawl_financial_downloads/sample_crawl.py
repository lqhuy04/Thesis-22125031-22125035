"""
One-off script: download RAW (unmapped) financial statement CSVs for a small
set of representative symbols spanning different statement templates
(bank / securities / insurance / real-estate / baseline non-financial),
WITHOUT running process_all_csvs, so the real Vietnamese line-item labels
are preserved for inspection.
"""
import os
import sys

REPO_ROOT = r"C:\School Project\Thesis-22125031-22125035"
sys.path.insert(0, os.path.join(REPO_ROOT, "utils", "crawl_financial_downloads"))

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_ROOT, "backend", "crawl_bao_cao_tai_chinh", ".env"))

import ssi_financial_downloader as sfd

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "raw_sample"
)
SYMBOLS = ["VCB", "SSI", "BVH", "VIC", "VNM"]

def main():
    downloader = sfd.SSIFinancialDownloader(download_dir=OUTPUT_DIR, headless=False)
    try:
        downloader.start()
        if not downloader.login():
            print("LOGIN FAILED")
            sys.exit(1)

        for sym in SYMBOLS:
            print(f"\n===== {sym} =====")
            try:
                results = downloader.download_all(sym)
                for sheet, path in results.items():
                    status = "OK" if path and os.path.exists(path) else "FAILED"
                    print(f"  {sheet}: {status}")
            except Exception as exc:
                print(f"[ERROR] {sym}: {exc}")
                import traceback
                traceback.print_exc()
    finally:
        downloader.close()

if __name__ == "__main__":
    main()
