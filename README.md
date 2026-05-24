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
- Alert generation for drone operators, lifeguards, beach managers, researchers, and API users
- Regional pack metadata for optional higher-resolution local intelligence
- Provider-based signal broker for normalized environmental/ecology/activity inputs
- Seed and ingestion scripts for normalized public data

## Safety And Privacy

AI1SAD is not an attack-prediction system and must not be presented as one. Scores estimate environmental and behavioral conditions associated with elevated shark encounter likelihood.

AI1SAD estimates environmental and surveillance-relevant shark encounter conditions. It does not predict individual attacks or guarantee safety outcomes.

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
ADMIN_ALERTS_ENABLED=false
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
- `/api/v1/alerts/active`
- `/api/v1/packs`
- `/api/v1/access/entitlements`
- `/api/v1/signals/location`
- `/api/v1/provider-health`

Admin ingestion endpoints are disabled by default.

## API Access

The repository includes placeholder API key validation, rate-limit hooks, and monetization data models for future hosted deployments. Access control is disabled by default for local development.

Initial access tiers are documented in [API Access Tiers](docs/API_ACCESS_TIERS.md):

- Free
- Developer
- Research
- Government/Enterprise

## Data And Ingestion

Raw and private source material should stay out of public API responses. Keep original files under `data/raw` and sensitive material under ignored/private paths.

Useful scripts include:

- `scripts/load_mongodb.py`
- `scripts/seed_regional_risk_profiles.py`
- `scripts/seed_regional_packs.py`

## Documentation

- [API](docs/API.md)
- [API Access Tiers](docs/API_ACCESS_TIERS.md)
- [Usage Policy](docs/USAGE_POLICY.md)
- [Disclaimer](docs/DISCLAIMER.md)
- [Schema](docs/SCHEMA.md)
- [Privacy](docs/PRIVACY.md)
- [Data Quality](docs/DATA_QUALITY.md)
- [Data Sources](docs/DATA_SOURCES.md)
- [Current Data Sources](docs/CURRENT_DATA_SOURCES.md)
- [Open-Meteo Provider](docs/OPEN_METEO_PROVIDER.md)
- [NOAA/NWS Provider](docs/NOAA_NWS_PROVIDER.md)
- [SST Provider Adapter](docs/SST_PROVIDER.md)
- [Human Exposure Provider](docs/HUMAN_EXPOSURE_PROVIDER.md)
- [Risk Model](docs/RISK_MODEL.md)
- [Regional Risk Profiles](docs/REGIONAL_RISK_PROFILES.md)
- [Surveillance Engine](docs/SURVEILLANCE_ENGINE.md)
- [Alert Engine](docs/ALERT_ENGINE.md)
- [Alert Levels](docs/ALERT_LEVELS.md)
- [Human Override](docs/HUMAN_OVERRIDE.md)
- [Regional Packs](docs/REGIONAL_PACKS.md)
- [Pack Entitlements](docs/PACK_ENTITLEMENTS.md)
- [Horseshoe Reef Case Study](docs/CASE_STUDY_HORSESHOE_REEF_2026.md)
- [Signal Broker](docs/SIGNAL_BROKER.md)
- [Species Season Profiles](docs/SPECIES_SEASON_PROFILES.md)
- [Provider Health](docs/PROVIDER_HEALTH.md)
- [Ethics And Limitations](docs/ETHICS_AND_LIMITATIONS.md)

## License

AI1SAD code is licensed under the [Apache License 2.0](LICENSE). Data sources may have separate licenses, terms, and privacy restrictions.
