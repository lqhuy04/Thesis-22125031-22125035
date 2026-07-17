# VN30 historical news backfill (2023-2025)

`backfill_vn30_historical_articles.py` reads CafeF's paginated company-news
archive directly. It does not use Serper. The current VN30 constituents and
their database IDs come from `MarketIndex`, `Stock_MarketIndex`, and `Stock`.

## Install and preview

From the repository root:

```powershell
pip install -r update_articles/requirements.txt
python update_articles/backfill_vn30_historical_articles.py --dry-run --symbols HPG --max-pages 25
```

The dry run makes CafeF requests and reports what it finds, but does not write
to Supabase and does not create a checkpoint.

## Import all 30 symbols

```powershell
python update_articles/backfill_vn30_historical_articles.py
```

Defaults are `2023-01-01` through `2025-12-31`. Existing `Article` rows are
matched by normalized URL and only the missing `Article_Stock` relationship is
added. A progress file beside the script is updated after every article. It
records the current symbol, publication date, page, item, URL, per-symbol
counters, and completed symbols.

## Pause, inspect, and resume

Press `Ctrl+C` once. The importer finishes the current article, atomically saves
its exact position, and exits. Pressing `Ctrl+C` a second time forces an
immediate exit; the preceding saved article remains the resume point.

Inspect progress without accessing CafeF or Supabase:

```powershell
python update_articles/backfill_vn30_historical_articles.py --status
```

Resume by running the original command again:

```powershell
python update_articles/backfill_vn30_historical_articles.py
```

The current archive page is revisited and already processed URLs are skipped,
which prevents gaps if CafeF pagination shifts while paused. The progress file
is retained with `status: completed` after the backfill finishes. Use
`--no-resume` only when intentionally starting a fresh pass.

By default, `sentiment` is `neutral` and `summary` uses the article description.
To generate both fields with the configured `OPENAI_API_KEY`:

```powershell
python update_articles/backfill_vn30_historical_articles.py --enrich
```

Run only one copy of the importer at a time. Deduplication is cached at startup;
concurrent copies could both observe the same URL as missing before either one
inserts it.

Useful options:

```text
--symbols HPG FPT VNM   import only a current-VN30 subset
--start-date YYYY-MM-DD override the lower date bound
--end-date YYYY-MM-DD   override the upper date bound
--delay 1.5             increase the minimum delay between CafeF requests
--no-resume             ignore an existing matching checkpoint
--status                display saved progress without network or DB access
--dry-run               never write to Supabase
```

This uses the *current* VN30 mapping in the database. If the research requires
point-in-time index membership, first load a dated constituent list and pass
the desired symbols explicitly (the current implementation rejects symbols not
in the current DB mapping).
