"""Build the public, publication-oriented export from the private review JSONL.

Usage (from repository root):
  python datasets/vn30-news-v1/prepare_release.py \
    --input update_articles/vn30_stock_articles_review.jsonl

The source review file is intentionally not copied into this release because it
contains full article text and embedded images. This script exports references,
metadata, and Stockrium's generated annotations only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

OUT = Path(__file__).resolve().parent
FIELDS = [
    "record_id", "article_url", "title", "published_at", "source",
    "stock_symbol", "sentiment", "summary", "collected_at",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Private review JSONL")
    args = parser.parse_args()
    records = []
    with args.input.open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            try:
                row = json.loads(line)
                article = row["article"]
                symbol = row["stock_symbol"].strip().upper()
                url = article["link"].strip()
                sentiment = article["sentiment"].strip().lower()
                if sentiment not in {"positive", "neutral", "negative"}:
                    raise ValueError(f"unexpected sentiment: {sentiment}")
                if not url.startswith(("http://", "https://")):
                    raise ValueError("article link is not an HTTP(S) URL")
                # Stable opaque identifier; URL and ticker remain explicit fields.
                record_id = hashlib.sha256(f"{symbol}\n{url}".encode()).hexdigest()
                records.append({
                    "record_id": record_id,
                    "article_url": url,
                    "title": article["title"].strip(),
                    "published_at": article["time"],
                    "source": article["source"],
                    "stock_symbol": symbol,
                    "sentiment": sentiment,
                    "summary": article["summary"].strip(),
                    "collected_at": row["collected_at"],
                })
            except Exception as exc:
                raise ValueError(f"Invalid source record at line {line_no}: {exc}") from exc

    records.sort(key=lambda r: (r["published_at"], r["stock_symbol"], r["article_url"]))
    keys = [(r["stock_symbol"], r["article_url"]) for r in records]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate (stock_symbol, article_url) rows; resolve before release")

    jsonl_path = OUT / "data.jsonl"
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    csv_path = OUT / "data.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)

    published = [datetime.fromisoformat(r["published_at"].replace("Z", "+00:00")) for r in records]
    manifest = {
        "dataset_name": "Stockrium VN30 News Dataset",
        "version": "1.0.0",
        "release_date": "2026-09-27",
        "record_unit": "one article-to-stock association",
        "records": len(records),
        "unique_articles": len({r["article_url"] for r in records}),
        "unique_stock_symbols": len({r["stock_symbol"] for r in records}),
        "publication_time_min": min(published).isoformat(),
        "publication_time_max": max(published).isoformat(),
        "sentiment_counts": dict(sorted(Counter(r["sentiment"] for r in records).items())),
        "source_review_file_sha256": sha256(args.input),
        "files": {
            path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in (jsonl_path, csv_path)
        },
        "generator": "prepare_release.py",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
