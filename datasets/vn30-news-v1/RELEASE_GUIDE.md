# Release and DOI guide

This package is prepared as dataset version `1.0.0`. Follow these steps after
committing the package and pushing it to the public GitHub repository.

## Before release

1. Confirm the repository is public and contains the complete
   `datasets/vn30-news-v1/` folder, including the CSV/JSONL, README, dictionary,
   manifest, license, citation file, and export script.
2. Review the dataset's rights and access terms. The package excludes article
   bodies and images, but contains publisher headlines and metadata; make sure
   sharing these fields and annotations is permitted for your intended venue.
3. Confirm author names, order, email addresses, and affiliations in
   `CITATION.cff`. CFF records authors and contact details, but does not express
   the corresponding-author role consistently across citation tools. The
   paper/submission system should identify all three corresponding authors as
   requested.
4. Check `manifest.json` checksums after the final data changes. If any released
   data changes, rerun the exporter and increment the version/tag.

## Create a GitHub release

1. Push the final commit to the default branch.
2. In the repository on GitHub, open **Releases** → **Draft a new release**.
3. Create/select tag `vn30-news-v1.0.0` (or use `v1.0.0` if that matches the
   repository's established tag convention) and target the commit containing
   this package.
4. Set release title to `Stockrium VN30 News Dataset v1.0.0`. Describe the
   included files, record count (8,927 article-to-stock associations), date
   range (2024-01-01 to 2026-07-29), and known caveats from `README.md`.
5. Publish the release. GitHub releases are tied to a tag and provide a
   version-specific archive of the repository at that tag.

## Archive that release on Zenodo and obtain a DOI

1. Sign in at Zenodo and connect the GitHub account that owns the repository.
2. In Zenodo's GitHub integration, enable archiving for the dataset repository.
   Check that the correct repository is enabled.
3. Zenodo archives GitHub releases. If this release was published before
   enabling the repository, use Zenodo's GitHub page to trigger/import the
   release archive as its current interface allows.
4. Open the resulting Zenodo record. Review the title, authors, affiliations,
   publication date, version, description, keywords, and license. Confirm all
   three authors and their email details are correct. If Zenodo did not import
   the CFF metadata as expected, edit the record metadata before publishing.
5. Publish the record and copy its **version-specific DOI**. Zenodo may also
   show a concept DOI that resolves to all versions; cite the version DOI in a
   paper that used this exact v1.0.0 snapshot. Do not cite an unpublished draft
   record as the archival DOI.
6. Save the Zenodo record URL and DOI in the paper and project records. Keep
   `CITATION.cff`'s version and release date consistent with the archived
   snapshot; make a new tagged version and DOI if the released data is revised.

Zenodo and GitHub screens may change. Consult the official current instructions
for [enabling a repository](https://help.zenodo.org/docs/github/enable-repository/),
[archiving a GitHub release](https://help.zenodo.org/docs/github/archive-software/github-upload/),
and [creating a GitHub release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).

## Paper-ready text

Replace the bracketed DOI with the version-specific DOI after publication:

> The Stockrium VN30 News Dataset (version 1.0.0) is publicly available at
> [repository URL] and archived at Zenodo ([version DOI]). The release contains
> 8,927 article-to-stock associations covering 6,850 unique article URLs and 30
> stock symbols, with publication dates from 1 January 2024 to 29 July 2026.
> It includes source links, stock-specific machine-generated sentiment labels,
> and Vietnamese summaries; full article text and images are not redistributed.

Suggested reference template:

> Le, Q. H., Nguyen, V. K., & Nguyen, T. M. T. (2026). *Stockrium VN30 News
> Dataset* (Version 1.0.0) [Data set]. Zenodo. https://doi.org/[version DOI]

Check the target journal's citation style and replace the placeholder DOI before
submission.
