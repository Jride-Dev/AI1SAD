# Schema

The MongoDB Atlas phase uses seven collections. Public responses are served from `incidents`, `locations`, and `sources` with `visibility="public"` filters.

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

