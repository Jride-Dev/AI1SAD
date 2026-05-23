# Privacy

AI1SAD is built around data minimization. Shark incident records can involve injured or deceased people, family members, witnesses, and sensitive source material, so the public API exposes only scrubbed records.

## Visibility Rule

Every public endpoint must include a MongoDB filter equivalent to:

```json
{"visibility": "public"}
```

Single-incident lookup also filters by `visibility="public"`. If a document exists but is marked `private`, `restricted`, or `internal`, the API returns `404`.

Incident list and stats endpoints additionally exclude duplicate source rows by default:

```json
{"duplicate.is_duplicate": false}
```

## Excluded Fields

The public API must never expose:

- Victim names
- Private notes
- Investigator/source notes
- Restricted-source content
- PDF filenames or links
- Href links
- Exact street addresses
- Raw geocode caches
- MongoDB credentials or internal API keys

## Internal Collections

These collections have no public routes:

- `private_notes`
- `ingestion_runs`
- `data_quality_reports`

`sources` is public only for high-level source metadata; it must not include private source notes or restricted per-record links.

## Raw Data

Raw and external source files stay local and are ignored by Git. They can include names and restricted fields needed for auditing, but those fields are not copied into API-facing public responses.

