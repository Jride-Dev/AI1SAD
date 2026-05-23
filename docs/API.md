# API

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

