# Shark Attack Data API

GitHub-ready FastAPI project for serving privacy-preserving shark attack incident records from local raw data.

The project keeps original source files under `data/raw`, keeps hidden or sensitive working material under `data/private`, and exports only sanitized public records to `data/public`.

## Quickstart

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/inspect_source.py
python scripts/export_public.py
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation.

## Data Pipeline

1. Put original source files in `data/raw`.
2. Use `python scripts/inspect_source.py` to inspect columns, counts, duplicate headers, and raw file inventory.
3. Use `python scripts/export_public.py` to create:
   - `data/public/incidents_public.csv`
   - `data/public/shark_attacks.sqlite`
4. Start the API with `uvicorn app.main:app --reload`.

The export excludes victim names, investigator/source notes, PDF links, private notes, exact street addresses, and restricted-source content.

## API Endpoints

- `GET /health`
- `GET /incidents`
- `GET /incidents/{incident_id}`
- `GET /stats/yearly`
- `GET /stats/countries`
- `GET /stats/activities`
- `GET /stats/fatality-rate`
- `GET /species`
- `GET /locations`

See [docs/API.md](docs/API.md) for details.

## Repository Layout

```text
app/                  FastAPI application
scripts/              Inspection, cleaning, normalization, and export scripts
tests/                Basic privacy and normalization tests
data/raw/             Original source files, preserved locally and ignored by Git
data/private/         Sensitive or hidden local-only files; ignored by Git
data/public/          Generated sanitized public artifacts
docs/                 API, schema, source, and ethics documentation
```

## Validation

```powershell
python -m unittest discover -s tests -p "test_*.py"
python scripts/inspect_source.py --raw-dir data/raw --source attacks.csv
python scripts/export_public.py
```

If your OneDrive folder blocks process-level writes, run the same scripts with output paths outside OneDrive, then copy the artifacts back through your normal file manager.
