# Data dictionary

Each row describes one association between a news article and a listed stock.
The CSV and JSONL files have identical logical fields.

| Field | Type | Meaning |
|---|---|---|
| `record_id` | string | SHA-256 hex digest of the stock symbol, newline, and article URL; stable row key. |
| `article_url` | string | Canonical/source page URL recorded by the collector. |
| `title` | string | Article headline as collected. |
| `published_at` | ISO 8601 string | Source-reported publication time, including timezone when available. |
| `source` | string | Publisher hostname recorded by the collector. |
| `stock_symbol` | string | VN30 ticker associated with this record. |
| `sentiment` | categorical string | `positive`, `neutral`, or `negative`; generated for the article's impact on this stock. |
| `summary` | string | Machine-generated Vietnamese summary, generally one to three sentences. |
| `collected_at` | ISO 8601 string | Time the record was collected, UTC. |

There are no explicit nulls in the released fields. One article may have
multiple rows for different stocks. Do not count rows as unique articles unless
you deduplicate by `article_url`; for stock-level analysis, retain the
article-to-stock association and account for repeated URLs in evaluation.
