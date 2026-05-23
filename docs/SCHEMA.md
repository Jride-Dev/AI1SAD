# Schema

The MongoDB Atlas phase uses seven collections.

## incidents

API-facing scrubbed incident records.

Important fields:

- `_id`: stable public source-row ID
- `canonical_key`: dedupe key shared by duplicate source rows
- `visibility`: `public`, `private`, or `restricted`
- `date`: `text`, `year`, `month`, `day`
- `incident_type`
- `country`
- `region`
- `location.name`
- `location.geo`: GeoJSON point with `[longitude, latitude]`
- `activity`
- `sex`
- `age`
- `injury_summary`
- `fatal`
- `species.common`
- `species.scientific`
- `source.name`
- `source.path`
- `source.row_number`
- `source.source_record_id`
- `duplicate.is_duplicate`
- `duplicate.duplicate_of`

Excluded from this collection: victim names, investigator/source notes, PDF links, href links, private notes, exact street addresses, and restricted raw content.

## sources

Public source metadata:

- `_id`
- `name`
- `visibility`
- `source_url`
- `path`
- `rows_raw`
- `rows_normalized`
- `records_loaded`

## species

Species rollups:

- `_id`
- `common`
- `scientific_names`
- `visibility`
- `incident_count`

## locations

Location rollups:

- `_id`
- `visibility`
- `country`
- `region`
- `name`
- `geo`
- `incident_count`

## ingestion_runs

Internal ingestion metadata. Public API routes do not expose this collection.

## data_quality_reports

Internal quality summaries. Public API routes do not expose this collection.

## private_notes

Private and restricted notes. Public API routes never query this collection.

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

