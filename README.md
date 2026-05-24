# AI1SAD
## All in 1 Shark Attack Data

AI1SAD is a global shark encounter warning and environmental risk analysis platform.

The project combines:
- Historical shark incident data
- Environmental/ocean conditions
- Regional seasonality
- Weather and rainfall patterns
- Vessel and fishing activity
- Biological event signals
- Human exposure estimates

AI1SAD does not predict individual shark attacks.

Instead, it estimates stacked environmental and behavioral conditions historically associated with elevated shark encounter risk.

## Project Status

AI1SAD is in active development. The current repo includes:

- A FastAPI application backed by MongoDB Atlas
- Public shark incident endpoints with privacy filtering
- Regional encounter-risk profiles
- Current-condition warning signals
- Deterministic warning-score explanations
- Surveillance search-zone prioritization for coastal safety planning
- Provider-based signal broker for normalized environmental/ecology/activity inputs
- Seed and ingestion scripts for normalized public data

## Safety And Privacy

AI1SAD is not an attack-prediction system and must not be presented as one. Scores estimate environmental and behavioral conditions associated with elevated shark encounter likelihood.

Public API responses must not expose:

- Victim names
- Private notes
- Restricted-source content
- Exact street addresses
- MongoDB credentials or provider API keys
- Unreviewed operational or surveillance notes

All public endpoints are expected to filter MongoDB records with `visibility="public"`.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` with local settings and secrets. Do not commit `.env`.

Required environment variables:

```text
MONGODB_URI=<your-mongodb-atlas-connection-string>
MONGODB_DATABASE=AI1SAD
SHARK_ATTACK_API_TITLE=AI1SAD Shark Attack Data API
ADMIN_EVENTS_ENABLED=false
ADMIN_SURVEILLANCE_ENABLED=false
```

Run the API:

```powershell
uvicorn app.main:app --reload
```

Run tests:

```powershell
python -m pytest -q
```

## API Areas

- `/api/v1/incidents`
- `/api/v1/stats/yearly`
- `/api/v1/stats/by-country`
- `/api/v1/stats/by-region`
- `/api/v1/stats/by-activity`
- `/api/v1/stats/by-species`
- `/api/v1/stats/fatality-rate`
- `/api/v1/locations/nearby`
- `/api/v1/sources`
- `/api/v1/risk/location`
- `/api/v1/warnings/location`
- `/api/v1/surveillance/search-zones`
- `/api/v1/signals/location`
- `/api/v1/provider-health`

Admin ingestion endpoints are disabled by default.

## Data And Ingestion

Raw and private source material should stay out of public API responses. Keep original files under `data/raw` and sensitive material under ignored/private paths.

Useful scripts include:

- `scripts/load_mongodb.py`
- `scripts/seed_regional_risk_profiles.py`

## Documentation

- [API](docs/API.md)
- [Schema](docs/SCHEMA.md)
- [Privacy](docs/PRIVACY.md)
- [Data Quality](docs/DATA_QUALITY.md)
- [Data Sources](docs/DATA_SOURCES.md)
- [Current Data Sources](docs/CURRENT_DATA_SOURCES.md)
- [Risk Model](docs/RISK_MODEL.md)
- [Regional Risk Profiles](docs/REGIONAL_RISK_PROFILES.md)
- [Surveillance Engine](docs/SURVEILLANCE_ENGINE.md)
- [Signal Broker](docs/SIGNAL_BROKER.md)
- [Species Season Profiles](docs/SPECIES_SEASON_PROFILES.md)
- [Provider Health](docs/PROVIDER_HEALTH.md)
- [Ethics And Limitations](docs/ETHICS_AND_LIMITATIONS.md)
