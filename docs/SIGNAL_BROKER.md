# Signal Broker

Phase 5 adds a provider-based signal broker that normalizes weather, ocean, vessel/fishing, biological, migration, tourism, and event-intelligence inputs into one `signals` collection.

The broker is deterministic. It does not create attack predictions. It prepares auditable, public-safe signals for warning and surveillance scoring.

## Normalized Signal Shape

```json
{
  "signal_type": "weather_rainfall",
  "species": "bull shark",
  "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
  "timestamp": "2026-05-23T06:00:00Z",
  "expires_at": "2026-05-23T18:00:00Z",
  "confidence": 0.8,
  "source": {
    "provider": "open_meteo",
    "dataset": "open_meteo_archive"
  },
  "data_freshness": {
    "status": "fresh",
    "age_hours": 1.2,
    "max_age_hours": 6
  },
  "risk_relevance": {
    "score": 0.8,
    "factors": ["rainfall_runoff"]
  },
  "visibility": "public",
  "value": 42.5,
  "units": "mm"
}
```

## Signal Types

Initial signal types include:

- `weather_rainfall`
- `ocean_sst`
- `sst_anomaly`
- `vessel_activity`
- `fishing_activity`
- `biological_event`
- `ecology_event`
- `migration_window`
- `prey_presence`
- `tourism_exposure`
- `human_exposure`

## Provider Interfaces

Provider interfaces live under `app/providers/`:

- `base.py`
- `open_meteo.py`
- `noaa_coastwatch.py`
- `noaa_nws.py`
- `obis_seamap.py`
- `noaa_stranding.py`
- `global_fishing_watch.py`
- `news_events.py`
- `manual_events.py`

Paid, credentialed, or policy-sensitive providers are placeholders until credentials, terms, rate limits, and public-use rules are reviewed. API keys must stay in `.env` or deployment secrets.

## Freshness

Each signal carries `data_freshness`. Stale signals may still influence scoring, but they reduce confidence and appear in `missing_data_sources` as stale provider data.

Missing expected providers appear as `status: "missing"` in public freshness summaries. Missing data must not be silently interpreted as normal conditions.

## Public Access

Public signal endpoints filter by `visibility="public"` and exclude private notes or restricted content.

Warning and surveillance engines can consume active normalized signals alongside legacy observation collections.
