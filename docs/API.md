# API

AI1SAD estimates environmental and surveillance-relevant shark encounter conditions. It does not predict individual attacks or guarantee safety outcomes.

Base URL for local development: `http://127.0.0.1:8000`

All public data routes live under `/api/v1` and filter MongoDB records with `visibility="public"`. Incident list and stats routes exclude duplicate source rows by default.

## Health

`GET /health`

Sample response:

```json
{
  "status": "ok",
  "database": "AI1SAD"
}
```

## List Incidents

`GET /api/v1/incidents`

Query parameters:

- `limit`: 1 to 500, default `100`
- `offset`: default `0`
- `year`: exact incident year
- `country`: uppercase country filter, for example `USA`
- `region`: state, province, or broad region
- `activity`: lowercase activity
- `fatal`: `true` or `false`
- `species`: case-insensitive partial species search
- `include_duplicates`: default `false`

Sample response:

```json
{
  "count": 8173,
  "limit": 2,
  "offset": 0,
  "results": [
    {
      "id": "09279a98bd075069e0551714",
      "canonical_key": "match:49b85848d0e8c90df469",
      "date": {"text": "22nd-23rd March", "year": 2026, "month": 3, "day": 22},
      "incident_type": "Unprovoked",
      "country": "AUSTRALIA",
      "region": "NSW",
      "location": {"name": "Little Avalon Beach", "geo": null},
      "activity": "surfing",
      "sex": "M",
      "age": "30+",
      "injury_summary": "Graze injuries R leg and ankle",
      "fatal": false,
      "species": {"common": null, "scientific": null},
      "source": {"name": "gsaf_latest_xls", "row_number": 1, "source_record_id": null},
      "duplicate": {"is_duplicate": false, "duplicate_of": null},
      "visibility": "public"
    }
  ]
}
```

## Get Incident

`GET /api/v1/incidents/{id}`

Returns one public incident by document ID. Private or restricted records return `404`.

Sample response:

```json
{
  "id": "96b3746fc46ef9af764f18d7",
  "canonical_key": "case:2018.06.25",
  "country": "USA",
  "region": "California",
  "activity": "paddling",
  "fatal": false,
  "visibility": "public"
}
```

## Stats

`GET /api/v1/stats/yearly`

Sample response:

```json
[
  {"key": 2026, "incidents": 25, "fatalities": 6, "fatality_rate_percent": 24.0},
  {"key": 2025, "incidents": 67, "fatalities": 15, "fatality_rate_percent": 22.39}
]
```

`GET /api/v1/stats/by-country`

`GET /api/v1/stats/by-region`

`GET /api/v1/stats/by-activity`

`GET /api/v1/stats/by-species`

Each grouped stats endpoint supports `limit`, from 1 to 500, default `250`.

Sample grouped response:

```json
[
  {"key": "USA", "incidents": 2365, "fatalities": 226, "fatality_rate_percent": 9.56}
]
```

`GET /api/v1/stats/fatality-rate`

Sample response:

```json
{
  "incidents": 8173,
  "fatalities": 1541,
  "fatality_rate_percent": 18.85
}
```

## Nearby Locations

`GET /api/v1/locations/nearby`

Query parameters:

- `lat`: latitude, required
- `lon`: longitude, required
- `radius_km`: radius in kilometers, default `50`, maximum `1000`
- `limit`: 1 to 250, default `50`

Sample request:

`GET /api/v1/locations/nearby?lat=-33.86&lon=151.2&radius_km=25`

Sample response:

```json
[
  {
    "_id": "AUSTRALIA|NSW|near sydney",
    "visibility": "public",
    "country": "AUSTRALIA",
    "region": "NSW",
    "name": "near sydney",
    "geo": {"type": "Point", "coordinates": [151.2, -33.86666667]},
    "incident_count": 1
  }
]
```

## Sources

`GET /api/v1/sources`

Query parameters:

- `limit`: 1 to 250, default `100`

Sample response:

```json
[
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
]
```

## Environmental Risk Signals

Risk endpoints return first-pass shark encounter-risk estimates. They do not predict attacks.

`GET /api/v1/risk/location`

Query parameters:

- `lat`, `lon`: location coordinates
- `radius_km`: historical incident search radius, default `25`
- `recent_rainfall_mm_24h`: recent rainfall/runoff proxy
- `river_mouth_distance_km`: distance to nearest river mouth, inlet, estuary, or outflow
- `sea_surface_temp_c`: sea surface temperature
- `fishing_activity`: 0 to 1
- `baitfish_prey_indicator`: 0 to 1
- `water_visibility_m`: estimated visibility in meters
- `human_water_activity`: 0 to 1
- `month`: 1 to 12

Sample response:

```json
{
  "location": {"name": null, "geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
  "score": 55.0,
  "band": "elevated",
  "warning_score": 67.0,
  "warning_band": "elevated",
  "confidence": 0.72,
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
  "factors": [
    {
      "factor": "recent_rainfall_runoff",
      "value": 50,
      "points": 15,
      "max_points": 15,
      "rationale": "Recent rainfall is treated as a runoff and turbidity proxy."
    }
  ],
  "regional_profile": {
    "region_key": "florida",
    "name": "Florida",
    "local_summer_high_exposure_months": [5, 6, 7, 8, 9],
    "known_high_attention_months": [3, 4, 10],
    "dominant_species": ["blacktip shark", "spinner shark", "bull shark", "tiger shark"]
  },
  "dominant_contributing_factors": [
    {"factor": "recent_rainfall_runoff", "value": 50, "points": 15, "max_points": 15}
  ],
  "disclaimer": "This is a first-pass shark encounter-risk estimate for research and planning. It is not an attack prediction, safety guarantee, or substitute for local lifeguard, weather, beach-closure, or wildlife guidance."
}
```

`GET /api/v1/risk/nearby`

Returns risk estimates for nearby public location rollups using the same optional environmental-signal parameters.

`GET /api/v1/risk/factors`

Returns factor definitions, maximum weights, risk bands, assumptions, and the disclaimer.

`GET /api/v1/risk/history`

Returns public `risk_observations` near a coordinate. Private observations are excluded.

`GET /api/v1/risk/explain`

Returns the same scored response as `/risk/location`, emphasizing factor-level explanations.

The warning score is the base rule score plus nearest regional profile multipliers. The API does not use one global summer definition; for example, Australia uses Southern Hemisphere summer months while Hawaii has an October Sharktober multiplier.

## Current Condition Warnings

`GET /api/v1/warnings/location`

Returns a warning score from recent/current observations near a coordinate.

Query parameters include `lat`, `lon`, `radius_km`, `lookback_hours`, `month`, `river_mouth_distance_km`, `use_open_meteo`, `use_noaa_nws`, and `bypass_cache`. By default, stored `warning_snapshots` may be reused until their regional TTL expires. Use `bypass_cache=true` for forced recomputation during debugging or ingestion QA.

Public response fields include:

- `warning_score`
- `warning_band`
- `activity_context_score`
- `activity_context_band`
- `confidence`
- `lookback_hours`
- `dominant_factors`
- `data_sources_used`
- `missing_data_sources`
- `cached`
- `disclaimer`

Example:

```json
{
  "warning_score": 81,
  "warning_band": "high",
  "confidence": 0.76,
  "lookback_hours": 72,
  "dominant_factors": [
    {
      "factor": "rainfall_intensity_score",
      "value": 82,
      "points": 15,
      "contribution": 0.1852,
      "rationale": "Rainfall in the previous 72 hours."
    },
    {
      "factor": "river_mouth_proximity_score",
      "value": 0.8,
      "points": 15,
      "contribution": 0.1852,
      "rationale": "Nearest river mouth, inlet, estuary, or outflow."
    }
  ],
  "data_sources_used": ["weather_observations", "biological_events"],
  "missing_data_sources": ["ocean_observations:stale", "vessel_activity"],
  "cached": false,
  "disclaimer": "This warning score estimates current shark encounter conditions from available signals. It is not an attack prediction, safety guarantee, or substitute for local lifeguard, weather, beach-closure, wildlife, or emergency guidance."
}
```

`GET /api/v1/warnings/explain`

Returns the same warning payload with factor-level explanations.

`GET /api/v1/warnings/events`

Returns public biological events near a coordinate. Private events and private notes are excluded.

`POST /api/v1/admin/events/manual`

Disabled by default. Enable only in trusted deployments with `ADMIN_EVENTS_ENABLED=true`.

## Surveillance Prioritization

`GET /api/v1/surveillance/search-zones`

Returns prioritized drone/search zones for coastal safety teams.

Query parameters:

- `lat`
- `lon`
- `radius_km`
- `mission_type`
- `lookback_hours`
- `activity_context`: optional, such as `swimming`, `surfing`, `spearfishing`, `diving`, or `fishing`
- `suspected_species`: optional
- `river_mouth_distance_km`: optional
- `month`: optional

Example response:

```json
{
  "disclaimer": "This drone/search prioritization score supports coastal safety planning. It does not predict individual shark attacks, infer shark intent, classify a person as provoking an animal, or replace local lifeguard, aviation, wildlife, beach-closure, weather, or emergency guidance.",
  "zones": [
    {
      "zone_id": "drone_search:25.000:-80.000:72:fishing",
      "priority_score": 74,
      "priority_band": "elevated",
      "surveillance_priority_score": 74,
      "warning_score": 12,
      "activity_context_score": 38,
      "center": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
      "radius_km": 2.5,
      "polygon": null,
      "recommended_pattern": "river-mouth parallel transects",
      "dominant_factors": [
        {
          "factor": "recent_interactions_nearby",
          "value": 1,
          "points": 14,
          "contribution": 0.1892,
          "rationale": "Recent public fatal/nonfatal interactions near the mission area increase search priority."
        }
      ],
      "confidence": 0.73,
      "data_sources_used": ["recent_interactions", "sighting_reports", "regional_risk_profiles"],
      "disclaimer": "This drone/search prioritization score supports coastal safety planning. It does not predict individual shark attacks, infer shark intent, classify a person as provoking an animal, or replace local lifeguard, aviation, wildlife, beach-closure, weather, or emergency guidance."
    }
  ]
}
```

Score meanings:

- `warning_score`: environmental/live-condition risk.
- `surveillance_priority_score`: where safety/drone teams should look first.
- `activity_hazard_score` or `activity_context_score`: risk introduced by what the human is doing in context.

None of these are attack probability.

`GET /api/v1/surveillance/explain`

Returns the same payload as `search-zones`, emphasizing factor-level explanations.

`GET /api/v1/surveillance/recent-interactions`

Returns public recent interaction records near a coordinate.

`GET /api/v1/surveillance/sightings`

Returns public sighting reports near a coordinate.

`POST /api/v1/admin/surveillance/interaction`

Disabled by default. Enable only in trusted deployments with `ADMIN_SURVEILLANCE_ENABLED=true`.

`POST /api/v1/admin/surveillance/sighting`

Disabled by default. Enable only in trusted deployments with `ADMIN_SURVEILLANCE_ENABLED=true`.

## Alerts

AI1SAD estimates environmental and surveillance-relevant shark encounter conditions. It does not predict individual attacks or guarantee safety outcomes.

`GET /api/v1/alerts/active`

Returns active public alerts whose `expires_at` is still in the future.

Sample response:

```json
{
  "results": [
    {
      "_id": "alert_horseshoe_reef_replay",
      "visibility": "public",
      "status": "active",
      "alert_type": "surveillance_priority",
      "level": "urgent_surveillance",
      "title": "High surveillance-priority zone",
      "summary": "Safety teams should prioritize this area for drone, lookout, or patrol review even if the general warning score is low.",
      "location": {"geo": {"type": "Point", "coordinates": [115.5153234, -31.9826564]}},
      "recommended_action": "Prioritize drone/search coverage for this zone and review local safety guidance before water activity.",
      "dominant_factors": [{"factor": "WA reef spearfishing white shark context", "contribution": 0.58}],
      "confidence": 0.48,
      "expires_at": "2026-05-24T18:00:00Z",
      "data_freshness": {"environmental": {"status": "missing"}},
      "disclaimer": "AI1SAD estimates environmental and surveillance-relevant shark encounter conditions. It does not predict individual attacks or guarantee safety outcomes."
    }
  ]
}
```

`GET /api/v1/alerts/location`

Query parameters:

- `lat`
- `lon`
- `radius_km`
- `limit`

Returns active public alerts near a coordinate. Private/internal alert records are excluded with `visibility="public"` filtering.

`GET /api/v1/alerts/{alert_id}`

Returns one public alert by id or `404` for private, restricted, missing, or internal-only records.

`POST /api/v1/alerts/evaluate`

Evaluates a warning/surveillance/activity payload and returns proposed alerts without persisting them. This endpoint is useful for replay validation and local operator tooling.

Optional query parameters:

- `use_open_meteo=true`: fetch live Open-Meteo rainfall/weather signals and let live rainfall influence the warning score used for alert evaluation.
- `use_noaa_nws=true`: fetch live NOAA/NWS U.S. weather alerts and let relevant alert context influence the warning score used for alert evaluation. Outside-U.S. coordinates return provider status `not_applicable`.
- `lookback_hours`: live weather lookback window, default `72`.

Sample request:

```json
{
  "lat": -31.9826564,
  "lon": 115.5153234,
  "warning_score": 0,
  "activity_hazard_score": 58,
  "surveillance_priority_score": 99.3,
  "confidence": 0.48,
  "dominant_factors": [
    {"factor": "WA reef spearfishing white shark context", "points": 58}
  ],
  "data_freshness": {"environmental": {"status": "missing"}}
}
```

Possible alert types:

- `general_warning`
- `surveillance_priority`
- `activity_hazard`
- `biological_event`
- `sighting_cluster`
- `post_incident_surveillance`

Possible alert levels:

- `advisory`
- `watch`
- `warning`
- `urgent_surveillance`

`POST /api/v1/admin/alerts/acknowledge`

Disabled by default. Enable only in trusted deployments with `ADMIN_ALERTS_ENABLED=true`.

`POST /api/v1/admin/alerts/resolve`

Disabled by default. Enable only in trusted deployments with `ADMIN_ALERTS_ENABLED=true`.

## Regional Packs

Regional packs are a soft entitlement system. Core model access is not blocked when a regional pack is unavailable or not enabled.

`GET /api/v1/packs`

Returns public pack metadata.

`GET /api/v1/packs/{pack_id}`

Returns one public pack.

`GET /api/v1/packs/{pack_id}/species`

Returns the pack dominant species and any public pack species profiles.

`GET /api/v1/packs/{pack_id}/signals`

Returns environmental, human exposure, surveillance, and alert signal/rule keys for a pack.

`GET /api/v1/packs/{pack_id}/replays`

Returns replay scenario ids associated with a pack.

`GET /api/v1/access/entitlements`

Returns soft entitlement state. Query `enabled_packs=florida,hawaii` can be used in local/dev calls to simulate enabled packs.

Warning, surveillance, replay, and alert-evaluation responses include:

- `active_pack`
- `pack_features_used`
- `pack_notice`
- `available_pack` when a regional pack matches the location

Sample pack notice:

```json
{
  "active_pack": "core",
  "available_pack": "western_australia",
  "pack_features_used": ["core_warning", "core_surveillance"],
  "pack_notice": "A higher-resolution regional pack is available for this location. Core remains available; regional packs are soft-gated and not hard billing enforcement."
}
```

## Signal Broker

`GET /api/v1/signals/location`

Returns active public normalized signals near a coordinate, plus freshness summaries for expected providers.

`GET /api/v1/signals/species`

Returns active public normalized signals for a species name.

`GET /api/v1/signals/active`

Returns active public normalized signals across the database.

`GET /api/v1/provider-health`

Returns provider health rollups and recent provider failures without credentials or private notes.

`GET /api/v1/regions/{region}/season-profile`

Returns public species season profiles for a region.

`GET /api/v1/species/{species}/risk-profile`

Returns public species season profiles, migration windows, and active signals for a species.

## Replay Validation

`GET /api/v1/replay/run`

Runs a built-in replay scenario by query string. Defaults to `florida_summer_heavy_rain`.

Example:

`GET /api/v1/replay/run?scenario_id=wa_spearfishing_reef_white`

`POST /api/v1/replay/run`

Runs a custom replay scenario from a JSON request body. This is useful for deterministic local validation and should not be treated as live prediction.

`GET /api/v1/replay/compare`

Compares a built-in replay scenario with the quiet-day baseline.

Example:

`GET /api/v1/replay/compare?scenario_id=south_africa_white_shark_surf_seal_colony`

`GET /api/v1/replay/heatmap`

Generates a surveillance-priority heatmap by default. Each cell includes:

- `surveillance_priority_score`
- `surveillance_priority_band`
- `warning_score`
- `warning_band`
- `activity_hazard_score`
- `activity_hazard_band`

`GET /api/v1/replay/scenarios`

Lists built-in replay scenarios.

Compatibility/helper routes:

- `GET /api/v1/replay/run/{scenario_id}`
- `GET /api/v1/replay/run-all`
- `GET /api/v1/replay/decay-analysis/{scenario_id}`
- `GET /api/v1/replay/compare-quiet-day/{scenario_id}`

## Explainability

AI1SAD explanations describe why a warning, surveillance priority, replay, or alert output was produced. They do not predict individual shark attacks.

`GET /api/v1/explain/location`

Returns a combined warning/surveillance explanation for a coordinate. Query parameters mirror the warning and surveillance routes, including `lat`, `lon`, `radius_km`, `lookback_hours`, `activity_context`, `suspected_species`, `river_mouth_distance_km`, `month`, and `enabled_packs`.

`GET /api/v1/explain/surveillance`

Returns an explanation for the top surveillance zone generated for a coordinate and mission context.

`GET /api/v1/explain/replay`

Returns a replay explanation for a built-in scenario. Query parameter: `scenario_id`.

`GET /api/v1/explain/alert/{alert_id}`

Returns an explanation for a public active/stored alert. Private alerts and private notes are not exposed.

Explanation responses include:

- `location`
- `active_pack`
- `warning_score`
- `activity_hazard_score`
- `surveillance_priority_score`
- `dominant_factors`
- `factor_contributions`
- `confidence_breakdown`
- `data_freshness`
- `missing_data_sources`
- `regional_rules_triggered`
- `suppression_reasons`
- `recommended_action`
- `recommended_surveillance_pattern`
- `metadata`
- `disclaimer`
