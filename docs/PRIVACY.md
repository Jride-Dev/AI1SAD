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

`risk_observations` can include provider-derived environmental signals. Public risk endpoints return only observations marked `visibility="public"` and exclude `private_notes` or restricted fields from projections.

Current-condition warning endpoints query only public weather, ocean, vessel, biological, human-exposure, regional-profile, and warning-snapshot data. Manual biological events must be reviewed before they are marked public.

Surveillance endpoints query only public recent interactions, public sighting reports, public reef/habitat features, public regional profiles, and public current-condition signals. They must never expose private notes, exact addresses, victim names, unreviewed operational records, or restricted source details. Spearfishing, diving, fishing, surfing, and swimming are activity context fields for search planning; public language must not label them as automatic provocation or infer shark intent.

Signal broker endpoints query only public normalized signals, public species season profiles, public migration windows, and public provider-health summaries. Provider failures must not expose raw credentials, tokens, restricted response bodies, private source notes, or unreviewed sensitive ecological data.

## Raw Data

Raw and external source files stay local and are ignored by Git. They can include names and restricted fields needed for auditing, but those fields are not copied into API-facing public responses.

Environmental provider credentials, weather/ocean API keys, and external data-provider config must stay in `.env` or the deployment secret store only.
