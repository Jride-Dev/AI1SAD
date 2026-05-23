# API

Base URL for local development: `http://127.0.0.1:8000`

## Health

`GET /health`

Returns API status and configured SQLite path.

## Incidents

`GET /incidents`

Query parameters:

- `limit`: 1 to 500, default `100`
- `offset`: default `0`
- `year`: exact year
- `country`: normalized uppercase country, for example `USA`
- `activity`: normalized lowercase activity, for example `surfing`
- `fatal`: `true` or `false`
- `species`: partial lowercase search

Returns paginated public incident records.

`GET /incidents/{incident_id}`

Returns a single public incident record.

## Statistics

`GET /stats/yearly`

Returns yearly incident counts, fatality counts, and fatality rate.

`GET /stats/countries`

Query parameters:

- `limit`: 1 to 250, default `50`

Returns grouped country counts.

`GET /stats/activities`

Query parameters:

- `limit`: 1 to 250, default `50`

Returns grouped activity counts.

`GET /stats/fatality-rate`

Returns the overall fatality rate across public records.

## Species

`GET /species`

Query parameters:

- `limit`: 1 to 250, default `100`

Returns normalized species labels and incident counts.

## Locations

`GET /locations`

Query parameters:

- `country`: optional uppercase country filter
- `limit`: 1 to 500, default `100`

Returns grouped public location labels. Exact addresses are redacted by the export pipeline.

