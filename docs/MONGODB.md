# MongoDB Loading

MongoDB credentials must stay in a local `.env` file or process environment. Do not commit real connection strings.

Required local environment:

```text
MONGODB_URI=<your-mongodb-atlas-connection-string>
MONGODB_DATABASE=AI1SAD
```

Build the cleaned local data first:

```powershell
python scripts/build_complete_database.py
```

Dry-run the Mongo loader:

```powershell
python scripts/load_mongodb.py --dry-run
```

Load the current scrubbed dataset:

```powershell
python scripts/load_mongodb.py --replace-collection
```

Persist manually prepared archival source metadata:

```powershell
python -m app.services.archival_news_tracker --input data/imports/archival_news/raw/example_archival_sources.json --mongo
```

Or use the Windows launcher:

```powershell
.\run_archival_news_import.exe --prompt-mongo
```

The launcher can prompt for Atlas host, MongoDB database username, and password, then build `MONGODB_URI` in memory for that run. It does not write credentials to `.env` or any repository file. If `.env` or `MONGODB_URI` is already configured, the launcher uses the existing app configuration instead.

The archival tracker writes accepted metadata-only records to `archival_sources` and sanitized import reports to `archival_import_reports`. Rejected rows are not inserted as source records, and rejected full-article text is not copied into MongoDB.

Persist the private Sharks Happen workbook and its duplicate review metadata:

```powershell
python -m app.services.sharks_happen_importer --input "data/imports/sharks_happen/raw/Sharks Happen Stats.xlsx" --mongo
```

The importer upserts source-attributed rows into `sharks_happen_sources` and writes run summaries to `sharks_happen_import_reports`. Victim names and raw workbook claims remain internal. Duplicate matches are candidates for human review; persistence does not merge records or promote them into registry incidents.

Default collections:

- `incidents_scrubbed`: one scrubbed source row per document, including duplicate markers.
- `dataset_builds`: latest build summary, source inventory, and privacy metadata.
- `archival_sources`: internal metadata-only archival source records.
- `archival_import_reports`: internal archival metadata import summaries.
- `sharks_happen_sources`: private, source-attributed Sharks Happen workbook rows with normalization warnings and duplicate-review candidates.
- `sharks_happen_import_reports`: internal Sharks Happen import and comparison summaries.
- `incident_globe`: scrubbed, derived 1990-2026 presentation records used by the read-only Incident Globe endpoint. The collection stores source attribution and optional supported coordinates, but excludes private victim names and raw private source claims.

Build or replace the local artifact and MongoDB globe projection with:

```powershell
F:\Python310\python.exe -m app.services.incident_globe --mongo
```

The projection is rebuildable and is not an upstream source of truth. Likely duplicate candidates are not merged into canonical events.

The loader does not include victim names, investigator/source notes, PDF links, href links, or private raw fields.

The archival tracker does not scrape Trove, use the Trove API, store full article bodies, create public archival endpoints, create warnings or alerts, alter scoring, modify replay artifacts, create public feed entries, or create drone observations.
