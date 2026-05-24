# Schema

The MongoDB Atlas phase uses public API collections, internal ingestion/quality collections, provider-freshness collections, current-condition collections, and event-intelligence collections. Public responses are served with `visibility="public"` filters and exclude private notes, restricted records, raw source notes, exact addresses, and sensitive source content.

## incidents

Scrubbed, API-facing incident records.

```json
{
  "_id": "96b3746fc46ef9af764f18d7",
  "record_id": "96b3746fc46ef9af764f18d7",
  "canonical_key": "case:2018.06.25",
  "visibility": "public",
  "date": {"text": "25-Jun-18", "year": 2018, "month": 6, "day": 25},
  "incident_type": "Boating",
  "country": "USA",
  "region": "California",
  "location": {
    "name": "Oceanside, San Diego County",
    "geo": {"type": "Point", "coordinates": [-117.3795, 33.1959]}
  },
  "activity": "paddling",
  "sex": "F",
  "age": "57",
  "injury_summary": "No injury to occupant, outrigger canoe and paddle damaged",
  "fatal": false,
  "species": {"common": "white shark", "scientific": null},
  "source": {
    "name": "local_legacy_attacks_csv",
    "path": "data/raw/attacks.csv",
    "row_number": 1,
    "source_record_id": "2018.06.25"
  },
  "duplicate": {"is_duplicate": false, "duplicate_of": null},
  "created_at": "2026-05-23T00:00:00+00:00",
  "updated_at": "2026-05-23T00:00:00+00:00"
}
```

Excluded from `incidents`: victim names, investigator/source notes, PDF links, href links, private notes, exact street addresses, restricted raw content, and raw geocode caches.

## sources

Public source metadata.

```json
{
  "_id": "gsaf_latest_xls",
  "name": "gsaf_latest_xls",
  "visibility": "public",
  "source_url": "https://www.sharkattackfile.net/spreadsheets/GSAF5.xls",
  "path": "data/raw/external/gsaf/GSAF5_latest.xls",
  "rows_raw": 7088,
  "rows_normalized": 7088,
  "records_loaded": 7088
}
```

## species

Species rollups derived from scrubbed incidents.

```json
{
  "_id": "white shark",
  "common": "white shark",
  "scientific_names": ["Carcharodon carcharias"],
  "visibility": "public",
  "incident_count": 612
}
```

## locations

Location rollups derived from scrubbed incidents. `geo` is omitted when no valid coordinate exists.

```json
{
  "_id": "AUSTRALIA|NSW|near sydney",
  "visibility": "public",
  "country": "AUSTRALIA",
  "region": "NSW",
  "name": "near sydney",
  "geo": {"type": "Point", "coordinates": [151.2, -33.86666667]},
  "incident_count": 1
}
```

## ingestion_runs

Internal ingestion metadata. No public API route exposes this collection.

```json
{
  "_id": "seed_2026-05-23T00:00:00+00:00",
  "visibility": "internal",
  "started_at": "2026-05-23T00:00:00+00:00",
  "completed_at": "2026-05-23T00:00:00+00:00",
  "records_seen": 40309,
  "records_loaded": 40309,
  "source_count": 6
}
```

## data_quality_reports

Internal quality summary. No public API route exposes this collection.

```json
{
  "_id": "latest_data_quality_report",
  "visibility": "internal",
  "created_at": "2026-05-23T00:00:00+00:00",
  "summary": {
    "total_normalized_records": 40309,
    "unique_records_after_dedupe": 8173,
    "duplicate_records": 32136
  }
}
```

## private_notes

Private analyst notes. No public API route exposes this collection.

```json
{
  "_id": "schema_placeholder",
  "visibility": "private",
  "incident_id": null,
  "note": "Private notes are never exposed by public API routes.",
  "created_at": "2026-05-23T00:00:00+00:00"
}
```

## risk_observations

Environmental risk-signal observations and model outputs. Public history routes filter by `visibility="public"` and never expose private notes.

```json
{
  "_id": "risk_2026_05_23_public_beach",
  "visibility": "public",
  "observed_at": "2026-05-23T00:00:00+00:00",
  "location": {
    "name": "Public Beach",
    "geo": {"type": "Point", "coordinates": [-80.0, 25.0]}
  },
  "signals": {
    "historical_incident_count": 4,
    "recent_rainfall_mm_24h": 50,
    "river_mouth_distance_km": 0.5,
    "sea_surface_temp_c": 26,
    "fishing_activity": 0.7,
    "baitfish_prey_indicator": 0.5,
    "water_visibility_m": 2,
    "human_water_activity": 0.8,
    "month": 7
  },
  "risk": {
    "score": 55.0,
    "band": "elevated",
    "model_version": "rule_based_v1"
  },
  "disclaimer": "Encounter-risk estimate; not an attack prediction."
}
```

## regional_risk_profiles

Regional calendar and environmental-rule profiles used by the warning-score layer.

```json
{
  "_id": "hawaii",
  "region_key": "hawaii",
  "name": "Hawaii",
  "visibility": "public",
  "center": {"name": "Hawaii", "geo": {"type": "Point", "coordinates": [-157.8, 21.3]}},
  "local_summer_high_exposure_months": [5, 6, 7, 8, 9],
  "known_high_attention_months": [10],
  "dominant_species": ["tiger shark", "reef shark", "galapagos shark"],
  "species_specific_risk_factors": {"tiger shark": ["fall seasonal attention", "turtle/prey movement"]},
  "environmental_multipliers": {"sharktober": 1.25, "high_attention": 1.2},
  "human_exposure_multipliers": {"weekend": 1.08, "beach_exposure": 1.08},
  "notes": "October receives a Hawaii-specific Sharktober seasonal multiplier.",
  "citations": ["Hawaii DLNR shark safety context", "GSAF public incident records"]
}
```

## Indexes

Incident indexes:

- `visibility + date.year`
- `visibility + country`
- `visibility + region`
- `visibility + activity`
- `visibility + species.common`
- `visibility + fatal`
- `canonical_key`
- `source.name`
- `location.geo` as `2dsphere`

Location indexes:

- `visibility + country + region`
- `geo` as `2dsphere`

Risk observation indexes:

- `visibility + observed_at`
- `location.geo` as `2dsphere`
- `visibility + risk.band`

Regional risk profile indexes:

- `visibility + region_key`
- `center.geo` as `2dsphere`

## weather_observations

Current/recent weather observations.

```json
{
  "_id": "weather_public_beach_2026_05_23",
  "visibility": "public",
  "provider": "open_meteo",
  "observed_at": "2026-05-23T00:00:00+00:00",
  "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
  "rainfall_mm": 12.4,
  "rainfall_72h_mm": 38.7,
  "air_temp_c_latest": 28.2
}
```

## ocean_observations

Current/recent ocean observations and products.

```json
{
  "_id": "ocean_public_beach_2026_05_23",
  "visibility": "public",
  "provider": "noaa_coastwatch",
  "observed_at": "2026-05-23T00:00:00+00:00",
  "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
  "sea_surface_temp_c": 26.4,
  "sst_anomaly_c": 1.2,
  "water_visibility_m": 2.5
}
```

## vessel_activity

Fishing/vessel activity proxies.

```json
{
  "_id": "vessel_public_beach_2026_05_23",
  "visibility": "public",
  "provider": "global_fishing_watch",
  "observed_at": "2026-05-23T00:00:00+00:00",
  "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
  "activity_index": 0.7
}
```

## biological_events

Manual or provider-derived biological events. Stale events expire from warning scoring.

```json
{
  "_id": "bio_whale_carcass_2026_05_23",
  "visibility": "public",
  "provider": "manual_events",
  "event_type": "whale_carcass",
  "description": "Public reviewed carcass report",
  "observed_at": "2026-05-23T00:00:00+00:00",
  "expires_at": "2026-06-01T00:00:00+00:00",
  "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}}
}
```

## human_exposure_estimates

Human beach/water activity estimates.

```json
{
  "_id": "exposure_public_beach_2026_05_23",
  "visibility": "public",
  "provider": "manual_or_model",
  "observed_at": "2026-05-23T00:00:00+00:00",
  "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
  "exposure_index": 0.8
}
```

## warning_snapshots

Stored public warning outputs for caching and auditability. Documents expire through `expires_at` and a MongoDB TTL index. Region profiles can configure cache lifetime with `warning_cache_ttl_minutes`.

```json
{
  "visibility": "public",
  "cache_key": "25.000|-80.000|25.0|72|10|0.8",
  "created_at": "2026-05-23T00:00:00+00:00",
  "expires_at": "2026-05-23T00:30:00+00:00",
  "ttl_minutes": 30,
  "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
  "response": {
    "warning_score": 62.5,
    "warning_band": "elevated",
    "confidence": 0.72,
    "lookback_hours": 72,
    "dominant_factors": [
      {"factor": "rainfall_intensity_score", "points": 15, "contribution": 0.24}
    ],
    "data_sources_used": ["weather_observations", "biological_events"]
  }
}
```

Current-condition indexes:

- each observation collection has `visibility + observed_at`
- each geospatial observation collection has a 2dsphere `location.geo` index
- `warning_snapshots` has `visibility + created_at`, `cache_key`, `expires_at` TTL, and `location.geo`

## provider_runs

Successful provider ingestion attempts.

```json
{
  "_id": "open_meteo_2026-05-23T06:21:00Z",
  "provider": "open_meteo",
  "status": "success",
  "started_at": "2026-05-23T06:20:00Z",
  "completed_at": "2026-05-23T06:21:00Z",
  "records_ingested": 483
}
```

## provider_failures

Failed provider attempts. No secrets, API keys, or raw credentials should be stored.

```json
{
  "_id": "open_meteo_failure_2026-05-23T06:22:00Z",
  "provider": "open_meteo",
  "failed_at": "2026-05-23T06:22:00Z",
  "status": "failed",
  "error_type": "timeout",
  "error_summary": "Provider request timed out"
}
```

## provider_health

Latest provider health rollup.

```json
{
  "_id": "open_meteo",
  "provider": "open_meteo",
  "last_success": "2026-05-23T06:21:00Z",
  "records_ingested": 483,
  "status": "healthy"
}
```

## Event Intelligence Collections

The event-intelligence layer uses similarly shaped public/private records:

- `marine_incidents`
- `shipping_events`
- `fish_kill_reports`
- `carcass_reports`
- `beach_closures`

```json
{
  "_id": "carcass_report_2026_05_23_public_beach",
  "visibility": "public",
  "provider": "manual_events",
  "observed_at": "2026-05-23T00:00:00+00:00",
  "expires_at": "2026-05-30T00:00:00+00:00",
  "confidence": "verified",
  "event_type": "whale_carcass",
  "description": "Reviewed public carcass report",
  "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}}
}
```

Provider and event indexes:

- `provider_runs`: `provider + started_at`
- `provider_failures`: `provider + failed_at`
- `provider_health`: unique `provider`
- event intelligence collections: `visibility + observed_at` and `location.geo` as `2dsphere`

## surveillance_zones

Reusable search-zone definitions for public or internal mission planning.

```json
{
  "_id": "zone_florida_public_beach",
  "visibility": "public",
  "name": "Public Beach surf zone",
  "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
  "radius_km": 2.5,
  "polygon": null,
  "recommended_pattern": "surf-zone ladder search"
}
```

## surveillance_missions

Mission records and operational state. No public route currently exposes mission records.

```json
{
  "_id": "mission_2026_05_23_public_beach",
  "visibility": "internal",
  "mission_type": "drone_search",
  "status": "planned",
  "created_at": "2026-05-23T00:00:00+00:00",
  "area": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}}
}
```

## recent_interactions

Recent public fatal/nonfatal interaction context for surveillance prioritization. Records must be scrubbed before they are public.

```json
{
  "_id": "interaction_2026_05_23_public_beach",
  "visibility": "public",
  "observed_at": "2026-05-23T00:00:00+00:00",
  "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
  "fatal": false,
  "species": "bull shark",
  "activity_context": "surfing",
  "summary": "Scrubbed public interaction summary"
}
```

## sighting_reports

Public shark sighting reports. Private notes and unreviewed details must remain hidden.

```json
{
  "_id": "sighting_2026_05_23_public_beach",
  "visibility": "public",
  "observed_at": "2026-05-23T00:00:00+00:00",
  "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
  "species": "blacktip shark",
  "verified": true,
  "confidence": "verified",
  "summary": "Reviewed public sighting report"
}
```

## reef_features

Public habitat features such as reefs, dropoffs, channels, sandbars, or other searchable coastal features.

```json
{
  "_id": "reef_public_beach_outer_edge",
  "visibility": "public",
  "feature_type": "reef",
  "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
  "name": "Outer reef edge"
}
```

## drone_priority_snapshots

Cached or audited outputs from the surveillance prioritization engine.

```json
{
  "_id": "drone_priority_2026_05_23_public_beach",
  "visibility": "public",
  "created_at": "2026-05-23T00:00:00+00:00",
  "expires_at": "2026-05-23T01:00:00+00:00",
  "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
  "zones": [
    {
      "zone_id": "drone_search:25.000:-80.000:72:fishing",
      "priority_score": 74,
      "priority_band": "elevated"
    }
  ]
}
```

Surveillance indexes:

- `surveillance_zones`, `recent_interactions`, `sighting_reports`, `reef_features`, and `drone_priority_snapshots`: `visibility + observed_at` and `location.geo` as `2dsphere`
- `surveillance_missions`: `visibility + created_at` and `mission_type + status`
- `drone_priority_snapshots`: `expires_at` TTL

## signals

Generic normalized provider signals consumed by warning and surveillance scoring.

```json
{
  "_id": "signal_open_meteo_2026_05_23_public_beach",
  "visibility": "public",
  "signal_type": "weather_rainfall",
  "species": null,
  "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
  "timestamp": "2026-05-23T06:00:00Z",
  "expires_at": "2026-05-23T18:00:00Z",
  "confidence": 0.8,
  "source": {"provider": "open_meteo", "dataset": "open_meteo_archive"},
  "data_freshness": {"status": "fresh", "age_hours": 1.2, "max_age_hours": 6},
  "risk_relevance": {"score": 0.8, "factors": ["rainfall_runoff"]},
  "value": 42.5,
  "units": "mm"
}
```

## ecology_events

Reviewed ecology or biological event records that can be normalized into `signals`.

## species_season_profiles

Regional species seasonality profiles.

```json
{
  "_id": "bull_shark_florida",
  "visibility": "public",
  "region": "Florida",
  "species": "bull shark",
  "active_months": [5, 6, 7, 8, 9],
  "peak_months": [8, 9],
  "risk_factors": ["river mouth", "runoff"]
}
```

## migration_windows

Coarse public species movement windows by region.

## prey_presence_zones

Public prey/baitfish/pinniped/forage indicators by location.

## vessel_activity_snapshots

Normalized vessel or fishing activity snapshots, separate from provider-specific raw payloads.

## tourism_exposure_profiles

Regional tourism and human-exposure profiles for public warning context.

Signal broker indexes:

- `signals`: `visibility + signal_type + timestamp`, `visibility + species + timestamp`, `visibility + expires_at`, and `location.geo` as `2dsphere`
- `ecology_events`: `visibility + event_type + observed_at` and `location.geo`
- `species_season_profiles`: `visibility + region + species`
- `migration_windows`: `visibility + region + species`
- `prey_presence_zones` and `vessel_activity_snapshots`: `visibility + observed_at` and `location.geo`
- `tourism_exposure_profiles`: `visibility + region`

## Monetization And API Access Collections

These collections support future hosted API access. No billing secrets or payment-provider keys belong in MongoDB public responses or committed files.

### users

```json
{
  "_id": "user_123",
  "email": "user@example.com",
  "organization": "Example Research Lab",
  "status": "active",
  "created_at": "2026-05-24T00:00:00Z"
}
```

### api_keys

API keys must be stored as hashes.

```json
{
  "_id": "key_123",
  "user_id": "user_123",
  "key_hash": "sha256_hash_only",
  "tier": "free",
  "status": "active",
  "created_at": "2026-05-24T00:00:00Z"
}
```

### usage_logs

```json
{
  "api_key_id": "key_123",
  "route": "/api/v1/incidents",
  "method": "GET",
  "timestamp": "2026-05-24T00:00:00Z",
  "status_code": 200,
  "tier": "free"
}
```

### billing_tiers

```json
{
  "tier": "developer",
  "monthly_request_limit": 100000,
  "rate_limit_per_minute": 120,
  "allowed_route_groups": ["incidents", "stats", "warnings", "signals"],
  "commercial_use": true
}
```

### rate_limits

```json
{
  "tier": "free",
  "route_group": "default",
  "requests_per_minute": 60
}
```

### subscription_status

```json
{
  "user_id": "user_123",
  "tier": "free",
  "status": "active",
  "current_period_end": null
}
```
