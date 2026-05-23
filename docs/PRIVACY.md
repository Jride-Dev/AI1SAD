# Privacy

The public API is designed around data minimization.

## Public Route Rules

Every public endpoint filters by:

```json
{"visibility": "public"}
```

Incident list and stats routes also exclude duplicate source rows unless the caller explicitly requests duplicates.

## Never Exposed

The API must never expose:

- Victim names
- Private notes
- Investigator/source notes
- Restricted-source content
- PDF links
- Href links
- Exact street addresses
- Raw geocode caches

`private_notes`, `ingestion_runs`, and `data_quality_reports` are internal collections and have no public API routes.

## Restricted Records

Records marked `visibility="private"` or `visibility="restricted"` are intentionally invisible through public API endpoints. Single-record lookup returns `404` for non-public records.

