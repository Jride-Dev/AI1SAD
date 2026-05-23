# API

Base URL for local development: `http://127.0.0.1:8000`

All public data routes live under `/api/v1` and always filter MongoDB records with `visibility="public"`. Incident list and stats routes also exclude duplicate source rows by default.

## Incidents

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

`GET /api/v1/incidents/{id}`

Returns one public incident by document ID. Private or restricted records return `404`.

## Statistics

- `GET /api/v1/stats/yearly`
- `GET /api/v1/stats/by-country`
- `GET /api/v1/stats/by-region`
- `GET /api/v1/stats/by-activity`
- `GET /api/v1/stats/by-species`
- `GET /api/v1/stats/fatality-rate`

Grouped stats return incident count, fatality count, and fatality rate percentage.

## Locations

`GET /api/v1/locations/nearby`

Query parameters:

- `lat`: latitude
- `lon`: longitude
- `radius_km`: radius in kilometers, default `50`
- `limit`: 1 to 250, default `50`

Uses MongoDB 2dsphere indexes. Only public locations are returned.

## Sources

`GET /api/v1/sources`

Returns public source metadata only. Private source notes and restricted content are not exposed.

