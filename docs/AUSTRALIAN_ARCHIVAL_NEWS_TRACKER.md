# Australian Archival News Tracker

Phase 26C implements a local/manual metadata-first tracker for Australian newspaper and public-record research. It supports the AI1SAD Shark-Human Incident Registry by tracking source metadata, citations, uncertainty, duplicate publication paths, rights state, and review status before any incident-registry promotion.

Target full working-version launch remains September 7, 2026.

## Scope

Phase 26C adds:

- `app/services/archival_news_tracker.py`
- `tests/test_archival_news_tracker.py`
- a metadata-only `ArchivalSourceRecord` model
- a public-safe archival source output helper
- a registry `SourceLink` conversion helper for archival citations
- a local JSON/CSV CLI importer for manually prepared metadata files
- Windows `.bat` and `.exe` launchers for the local importer
- opt-in internal MongoDB persistence for accepted metadata records and import reports
- duplicate/reprint/later-retelling metadata
- source-conflict metadata for date, location, species, injury, behavioral interpretation, rights, and reliability disagreements
- explicit no-side-effect reporting

The tracker captures source metadata before full text. AI1SAD treats archival articles and public-record references as source evidence, not final truth.

The tracker does not:

- scrape Trove or other archive pages
- use the Trove API
- bulk-download article bodies
- accept or store full article text, raw OCR dumps, downloaded HTML, or copyrighted article bodies
- reproduce copyrighted article text in public outputs
- expose archival records through a public API route
- create warnings, alerts, replay facts, scoring changes, drone observations, or public feed entries
- assign confirmed shark intent
- default to mistaken identity
- promote archival species mentions into official public species confirmation

## Local Manual CLI

Phase 26C can be used locally with manually prepared `.json` or `.csv` metadata files:

```powershell
F:\Python310\python.exe -m app.services.archival_news_tracker `
  --input data/imports/archival_news/raw/example_archival_sources.json `
  --staging data/imports/archival_news/staging/latest_archival_sources.json `
  --report data/imports/archival_news/reports/latest_archival_import_report.json
```

The default output paths are:

- staging: `data/imports/archival_news/staging/latest_archival_sources.json`
- report: `data/imports/archival_news/reports/latest_archival_import_report.json`

Local raw inputs, staging outputs, and reports under `data/imports/archival_news/` are ignored by git except `.gitkeep` placeholders.

JSON input may be a single record, a list of records, or an object with `records` or `sources`. CSV input uses the same field names as the model. Semicolon-separated CSV values are accepted for list fields such as `claim_tags`, `related_source_ids`, `people_mentioned`, `provenance_notes`, and `normalization_warnings`. The `conflicts` CSV field may contain a JSON array.

The CLI writes:

- normalized metadata-only `records`
- registry-compatible `registry_source_links`
- `public_records`
- an import report with `records_written`, `rejected_rows`, row-level errors, and no-side-effect flags

Rows that attempt blocked capture modes or article-body storage are rejected and reported. The CLI returns a nonzero exit code when any row is rejected.

## Windows Launcher

For a double-clickable Windows workflow, use:

```powershell
.\run_archival_news_import.exe --prompt-mongo
```

The executable is a small wrapper around `run_archival_news_import.bat`; the batch file delegates to `run_archival_news_import.ps1` and keeps the console open after double-click runs so errors and report paths remain visible. A successful import opens the local AI1SAD registry viewer so the case record and linked-source counts are visible. Use `--no-viewer` for automated runs.

The importer and viewer have separate jobs: the importer accepts manually prepared archival source metadata, while `AI1SAD_Registry.exe` displays actual internal incident-registry cases. Importing the blank CSV template correctly writes zero records; it is a field template, not incident data.

The launcher defaults to Mongo persistence. It accepts the same input/output options as the Python CLI, plus credential prompt helpers:

```powershell
.\run_archival_news_import.exe `
  --input data\imports\archival_news\raw\example_archival_sources.json `
  --prompt-mongo
```

Credential prompt behavior:

- If `.env` or `MONGODB_URI` is already present, the launcher lets the Python app use that configuration.
- With `--prompt-mongo`, or when no `.env`/`MONGODB_URI` exists, it prompts for MongoDB Atlas host, username, and password.
- The password is read as a secure prompt and used to build `MONGODB_URI` in memory for the child Python process only.
- The launcher does not write MongoDB credentials, generated URIs, or passwords to repository files.

Rebuild the executable from the wrapper source with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build_archival_news_import_exe.ps1
```

## Optional Mongo Persistence

When `MONGODB_URI` and `MONGODB_DATABASE` are configured, the same CLI can persist accepted metadata records and an internal import report:

```powershell
F:\Python310\python.exe -m app.services.archival_news_tracker `
  --input data/imports/archival_news/raw/example_archival_sources.json `
  --staging data/imports/archival_news/staging/latest_archival_sources.json `
  --report data/imports/archival_news/reports/latest_archival_import_report.json `
  --mongo
```

The `--mongo` option writes accepted records to the internal `archival_sources` collection and a sanitized report to `archival_import_reports`. Records are stored with `visibility: internal`, `public_visibility: restricted`, `metadata_only: true`, and `article_body_stored: false`.

Rejected rows are not inserted into `archival_sources`. Rejection reports store row numbers, source ids when supplied, and error messages only; they do not copy rejected full-article text into MongoDB.

## Source Targets

Initial source targets include:

- Trove / National Library of Australia
- State Library of Queensland
- State Library of New South Wales
- State Library Victoria
- State Library of Western Australia
- State Library of South Australia
- National Archives of Australia
- Australian local newspapers and regional archives
- surf lifesaving club histories
- coroner/inquest references where legally accessible
- government fisheries / shark control reports
- historical court/inquest reporting
- maritime accident archives

## Implemented Metadata Fields

The Phase 26C model captures:

- `archival_source_id`
- `tracker_schema_version`
- `created_at`
- `updated_at`
- `capture_method`
- `source_platform`
- `source_kind`
- `archive_collection`
- `newspaper_title`
- `publication_date`
- `article_title`
- `article_url`
- `trove_article_id`
- `page_url`
- `page_number`
- `jurisdiction`
- `location_mentioned`
- `shark_attack_case_candidate`
- `people_mentioned`
- `species_mentioned_raw`
- `incident_date_raw`
- `incident_date_normalized`
- `source_text_excerpt_allowed`
- `source_text_excerpt`
- `copyright_status`
- `rights_note`
- `access_note`
- `citation`
- `extraction_status`
- `review_status`
- `linked_ai1sad_case_id`
- `source_confidence`
- `ocr_confidence`
- `ocr_uncertainty_notes`
- `public_citation_allowed`
- `duplicate_group_id`
- `duplicate_relation`
- `duplicate_of_source_id`
- `related_source_ids`
- `claim_tags`
- `conflicts`
- `provenance_notes`
- `normalization_warnings`
- `notes_private`
- `source_fingerprint`
- `metadata_only`
- `article_body_stored`

## Capture Rules

- Store metadata and citations first.
- Use only manual metadata, citation, catalogue, or analyst-note capture methods.
- Reject `scrape`, `web_scrape`, `trove_api`, `archive_api`, `bulk_download`, `article_body_download`, and `ocr_dump` capture modes.
- Reject payload fields that attempt to store full article text, raw OCR text, downloaded HTML, article bodies, or full copyrighted article text.
- Do not bulk-download full article bodies.
- Do not reproduce copyrighted articles in public outputs.
- Preserve OCR uncertainty and include an explicit review status for OCR-derived claims.
- Preserve old terminology as raw source text in metadata fields, but normalize carefully only in separate reviewed fields.
- Treat archival articles as source evidence, not final truth.
- Link multiple articles to the same incident when possible.
- Detect reprints, syndication, duplicates, later retellings, and retrospective anniversary pieces.
- Track conflicting claims instead of flattening them into a single narrative.

## Confidence And Review

Review states:

- `unreviewed`
- `metadata_captured`
- `ocr_needs_review`
- `citation_verified`
- `case_link_candidate`
- `case_link_confirmed`
- `duplicate_or_reprint`
- `rights_review_required`
- `rejected`

Source confidence values:

- `unreviewed`
- `weak`
- `plausible`
- `corroborated`
- `conflicting`
- `contradicted`

OCR confidence values:

- `unknown`
- `low`
- `medium`
- `high`
- `not_applicable`

## Registry Link

`source_link_from_archival_record` converts a reviewed archival metadata record into the Phase 26B `SourceLink` model. The helper maps source kinds into registry source types such as:

- `archival_newspaper`
- `trove_metadata`
- `state_library_record`
- `government_report`
- `coroner_or_inquest`
- `surf_lifesaving_record`

The source link carries citation metadata, source confidence, rights notes, public-citation status, short reviewed excerpts only when explicitly allowed, and linked claim labels such as `incident_date`, `location`, `species_raw`, `case_candidate`, `ocr_review_state`, and `duplicate_or_reprint_context`.

Archival species mentions enter the registry as source claims or internal hypotheses with confidence, limitations, and disclosure review. They must not automatically become `confirmed_public` official species values, and moderate/high species-disclosure risk should suppress speculative public species attribution.

## Public-Safe Output

`public_archival_source_output` excludes private analyst notes and named people from public-safe output. It includes article/page URLs only when `public_citation_allowed` is true. It includes short excerpts only when `source_text_excerpt_allowed` is true and the excerpt was accepted into the metadata record.

Public-safe output always reports:

- `metadata_only: true`
- `article_body_stored: false`
- side-effect flags showing no scraping, Trove API use, article-body download, warning creation, alert creation, replay facts, scoring changes, public feed entries, or drone observations

## Known Limitations

- Phase 26C stores records only through an opt-in internal MongoDB CLI workflow, not through a public API route.
- No source-specific connector, crawler, Trove API client, OCR processor, article downloader, or public release workflow is added.
- Rights review remains manual.
- Case linking remains analyst-reviewed; archival metadata does not automatically promote source claims into AI1SAD case truth.

## Validation Snapshot

Latest Phase 26C local validation:

- Focused archival tracker tests: `12 passed`
- Focused incident registry and local viewer tests: `17 passed`
- Full backend tests: `325 passed, 3 warnings`
- Frontend tests/build: `30 passed`; production build passed
- MkDocs build: passed with the standard Material for MkDocs advisory banner
- README local links/images check: `56` checked, passed
- Secret scan on changed files: no credential patterns matched
- Prohibited-language scan on changed files: guardrail/disclaimer matches only
- Git whitespace check: passed with CRLF normalization warnings only
- Windows launcher smoke test: `.exe --input ... --local-only --no-pause` completed with `records_written: 1`

No replay outputs, scoring weights, provider adapters, frontend dependencies, fixture dates, public endpoints, public feeds, alerts, warnings, drone observations, Trove scraping, Trove API calls, article-body downloads, raw OCR dumps, or copyrighted article redistribution changed.

## Phase 26D Handoff

The next planned phase is Phase 26D: Vic Hislop Corpus and Case-Claim Archive.

Phase 26D should reuse the metadata-first, rights-aware, source-link-first pattern from Phase 26C. Hislop claims must remain source-attributed and reviewable; they must not automatically decide shark intent, create warnings or alerts, modify scoring, alter replay artifacts, create public feed entries, or create drone observations.
