# AI1SAD

All-in-1 Shark Attack Database connecting gathered public shark-incident information around the world.

AI1SAD is a FastAPI + MongoDB Atlas project for serving privacy-preserving shark incident records. The API is designed for public analysis, dashboards, and research workflows while keeping raw source files, victim-identifying fields, private notes, and restricted material out of public responses.

## What The API Provides

- Public incident search and lookup
- Yearly, country, region, activity, species, and fatality-rate stats
- Nearby location lookup using MongoDB geospatial indexes
- Public source metadata
- Seed scripts for turning cleaned local data into MongoDB Atlas collections

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a local `.env` file. Do not commit it.

```text
MONGODB_URI=<your-mongodb-atlas-connection-string>
MONGODB_DATABASE=AI1SAD
SHARK_ATTACK_API_TITLE=AI1SAD Shark Attack Data API
```

Build and seed the MongoDB collections:

```powershell
python scripts/build_complete_database.py
python scripts/seed_mongodb_collections.py --replace
```

Run the API:

```powershell
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation.

## API Endpoints

- `GET /health`
- `GET /api/v1/incidents`
- `GET /api/v1/incidents/{id}`
- `GET /api/v1/stats/yearly`
- `GET /api/v1/stats/by-country`
- `GET /api/v1/stats/by-region`
- `GET /api/v1/stats/by-activity`
- `GET /api/v1/stats/by-species`
- `GET /api/v1/stats/fatality-rate`
- `GET /api/v1/locations/nearby`
- `GET /api/v1/sources`

See [docs/API.md](docs/API.md) for parameters and sample responses.

## MongoDB Collections

- `incidents`
- `sources`
- `species`
- `locations`
- `ingestion_runs`
- `data_quality_reports`
- `private_notes`

Public API routes read only public-safe collections and always filter returned records with `visibility="public"`. Internal collections have no public route.

## Safety And Privacy Warning

Raw shark incident files can contain victim names, investigator/source notes, PDF links, exact locations, and restricted-source material. Keep raw files local. Never commit `.env`, `data/raw`, `data/raw/external`, `data/processed`, `reports`, `data/private`, MongoDB exports, or private notes.

The API must not expose:

- Victim names
- Private notes
- Investigator or source notes
- Restricted records
- PDF or href links
- Exact street addresses
- Raw geocode caches

## Validation

```powershell
python -m unittest discover -s tests -p "test_*.py"
```
