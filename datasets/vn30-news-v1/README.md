# Stockrium VN30 News Dataset

Version 1.0.0 · release snapshot: 2026-09-27

This release contains Vietnamese financial-news records associated with VN30
listed stocks, plus Stockrium's stock-specific sentiment label and generated
Vietnamese summary. It is intended for research on financial news processing
and stock-level sentiment. It is a snapshot of an application dataset, not a
complete archive of all news published about VN30 companies.

## Package contents

- `data.jsonl`: UTF-8 JSON Lines, one article-to-stock association per line.
- `data.csv`: the same records in UTF-8 CSV (BOM included for spreadsheet compatibility).
- `manifest.json`: snapshot statistics and SHA-256 checksums.
- `DATA_DICTIONARY.md`: field definitions and interpretation.
- `CITATION.cff`: machine-readable citation metadata for Quoc Huy Le, Vinh Khang Nguyen, and Ms Nguyen Thi Minh Tuyen.
- `RELEASE_GUIDE.md`: steps to create a tagged release, archive it on Zenodo,
  and cite its version-specific DOI.
- `LICENSE`: license for the dataset's original annotations and selection.
- `prepare_release.py`: reproducible export from the private review file.

The release deliberately excludes source article bodies, descriptions, and
embedded thumbnail images. Article titles and metadata remain attributable to
their original publishers; each record includes the source URL. Check the
publisher's terms and applicable law before republishing or redistributing
those underlying works. The license in this package does not grant rights to
third-party article text, images, or websites.

## Coverage and method

The included release has 8,927 article-to-stock associations and 6,850 distinct
article URLs across 30 symbols. Publication timestamps span 2024-01-01 through
2026-07-29. The collection process searches for stock news with Serper/Google
results and downloads article pages; records were written to a reviewable JSONL
file and then imported into the project's Supabase `Article` and
`Article_Stock` tables. The source crawler and review/import workflow are in
`update_articles/init_vn30_stock_articles.py`.

Rows are keyed by `(stock_symbol, article_url)`, so a single article can appear
more than once when it is associated with multiple stocks. These repeated
article URLs are not independent news documents. The sentiment is relative to
the associated stock, and must not be interpreted as general article polarity
or investment advice. The crawler's code configures the DeepSeek model name
`deepseek-v4-flash` for its annotation call; model/version availability and
outputs may change over time. Summaries and labels are machine-generated and
have not been independently validated for this release.

The VN30 constituent membership is not point-in-time reconstructed. Do not
claim that the records represent the constituents as of each article date.
Search-engine coverage, publisher access, parsing, and the finite collection
window can introduce selection and missing-data bias. Article publication
times retain the source-provided timezone (commonly UTC+07:00); collection times
are UTC ISO 8601 timestamps.

## Reproduce the export

The raw review file is an internal input and is not included. Given an authorized
copy of it, run from the repository root:

```powershell
python datasets/vn30-news-v1/prepare_release.py --input path/to/vn30_stock_articles_review.jsonl
```

This regenerates the CSV, JSONL, and manifest. The manifest records the source
file hash and output hashes. No network access or database credentials are
needed to transform that input.

## Citation

See `CITATION.cff`. Replace the placeholder author with the actual research
team's preferred citation identity before depositing the package in a public
repository or data archive. Cite the dataset and cite original news sources
when discussing or quoting individual articles.

## License and access

The CC BY 4.0 license applies only to Stockrium's original annotations,
selection, and arrangement, to the extent those rights exist. Third-party
material is excluded from that grant. For a public research deposit, include
the repository URL and a permanent version/DOI in the paper after publication;
do not cite this working directory as a permanent archive.
