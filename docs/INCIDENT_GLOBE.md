# Incident Globe

## Scope

The Incident Globe is a local AI1SAD geographical explorer for shark-human incident records from 2000 through 2026. It combines the normalized scrubbed incident database with reviewed exact-match attribution from the private Sharks Happen source lane. The first release provides decade layers for the 2000s, 2010s, and 2020-2026.

Open the frontend at `http://localhost:5174/incident-globe`. The supporting read-only endpoint is `GET /api/v1/incidents-globe`.

## Current Build

The October 4, 2026 build contains:

| Measure | Count |
| --- | ---: |
| Deduplicated records | 3,398 |
| Records with validated coordinates | 1,927 |
| Source-provided coordinates | 452 |
| Contextual CSV2GEO coordinates | 1,475 |
| Records retained without a validated map point | 1,471 |
| Explicit invalid/no-shark-involvement rows excluded | 174 |
| Sharks Happen rows considered in the period | 422 |
| Reviewed exact Sharks Happen matches attached | 96 |
| Standalone Sharks Happen source records | 326 |

Unresolved locations remain visible in totals and filtering but are not placed on the globe. AI1SAD does not reuse coordinates from broad or ambiguous location text. The original cache keyed coordinates by location alone, which allowed names such as Chatham Island, Portland, North Beach, and Black Point to resolve to unrelated countries or inland places. The replacement contextual cache keys location, region, and country together. CSV2GEO results require relevance of at least `0.75`, containment within the stated Natural Earth country boundary, and no more than `25 km` distance from the Natural Earth coastline. Source-provided coordinates are not rewritten by this check.

## Interaction

- Select the 2000s, 2010s, or 2020-2026 decade layer.
- Filter by `Provoked`, `Unprovoked`, `Unknown`, or `Conflicted`.
- Toggle `Fatal`, `Fatal and consumed/body not recovered`, `Non-fatal`, and `No injury` markers.
- Hover over a mapped marker for a compact summary.
- Select a marker to open an incident infographic with event fields, coordinate confidence, source attribution, links, and any approved media references.
- Drag to rotate, use the mouse wheel or zoom controls to change scale, and toggle automatic rotation.
- Markers use front-face rendering and globe depth testing so points on the far hemisphere cannot appear through or around the Earth surface.

The globe uses NASA's [Blue Marble](https://visibleearth.nasa.gov/images/57723/the-blue-marble) imagery as its Earth texture. Contextual coordinate validation uses [Natural Earth](https://www.naturalearthdata.com/) 1:10m country and coastline geometry; those reference files are validation inputs rather than browser assets.

## Classification Rules

Provocation is preserved from source incident-type labels. Conflicting source labels produce `conflicted`; missing or noncommittal labels produce `unknown`. The globe does not infer provocation from activity, injury, or presumed shark behavior.

Outcome categories are conservative:

- `fatal`: the record is marked fatal without evidence meeting the consumed/body-not-recovered rule.
- `fatal_consumed`: the record is fatal and a source explicitly supports consumed, swallowed, or body-not-recovered context.
- `non_fatal`: a non-fatal incident with injury or without an explicit no-injury statement.
- `no_injury`: the source explicitly reports no injury.

An attempted-consumption claim alone does not classify a case as fatal and consumed. These labels summarize source claims; they do not claim shark intent.

## Provenance And Duplicate Handling

Canonical normalized records are grouped with their duplicate source rows so one event can show all retained source attributions. A Sharks Happen record is attached to an existing event only when the importer marked it as an exact candidate. Likely candidates remain separate pending human review. Every infographic lists the available dataset or source-channel attribution; a case-specific URL appears only when the source record contains one.

The local projection is generated with:

```powershell
F:\Python310\python.exe -m app.services.incident_globe --mongo
```

This writes ignored local data to `data/public/incident_globe_2000_2026.json` and replaces the internal MongoDB `incident_globe` projection when MongoDB is enabled.

The original coordinate-review queue is `data/review/incident_globe_all_geocode_review_2026-10-03.csv`. The full-history sanitized vendor input is `data/review/incident_globe_csv2geo_1900_2026_upload_2026-10-03.csv`, the raw vendor result is `data/review/incident_globe_csv2geo_1900_2026_result_2026-10-03.csv`, and the validated cache is `data/review/incident_globe_context_geocodes_1900_2026.csv`. They contain location metadata and internal query IDs only; victim names, injuries, private analyst notes, credentials, and restricted registry data were not submitted. Every vendor result retains its validation status and provenance.

## Safety, Privacy, And Limits

- The projection is built from the scrubbed incident database and does not expose victim names or private analyst notes.
- Raw Sharks Happen workbook content and private fields remain outside the response.
- The feature does not change warning scoring, create alerts, create observations, alter replay artifacts, or determine species.
- Explicit invalid/no-shark-involvement rows are excluded. Questionable records remain source-attributed rather than silently discarded.
- No rights-cleared per-case image collection is currently available. The infographic supports approved media references but does not invent, scrape, or hotlink images.
- Mapped points come from source-provided coordinates or validated contextual results. Coordinate source and confidence remain visible in the infographic.
- Relevance, country-boundary, and coastline checks prevent broad classes of wrong placement but do not prove street-level or offshore precision. Rejected results remain available for human review.
- Fatal records are plotted only when a source or contextual coordinate passes the same validation boundary; outcome severity never relaxes coordinate requirements.
- Incident density is not a risk rate and does not account for water-use exposure, reporting differences, or population.

## Validation

Validation completed October 4, 2026:

- focused Incident Globe and contextual-geocoding tests: `10 passed`
- full backend tests: `342 passed`, with two existing FastAPI startup-event deprecation warnings
- frontend tests: `31 passed`
- frontend production build: passed
- Local projection rebuild: `3,398` records; `1,927` mapped, `1,471` unresolved, and `1,475` contextual coordinates accepted
- Full-history vendor validation: `1,914` unique contexts accepted; `1,115` low relevance, `562` country mismatch, `466` missing/invalid, `142` too far inland, and `43` unknown country boundary results rejected
- Chatham Island regression: the 21-Jul-2001 Massachusetts record resolves to `41.68227, -70.01460`, with `0.98` relevance and `0.58 km` coastline distance
- live production verification: API and browser render `3,398` total, `1,927` mapped, and `1,471` unresolved; the API reports `1,475` contextual map points and `93` mapped fatal records
- MkDocs strict build, README local-link check, changed-file secret scan, prohibited-language scan, and Git whitespace check: passed

## Next Handoff

The next bounded globe work is human review of rejected contextual results, rights review for case media, and publication of the already-prepared pre-2000 decade layers. Historical publication must preserve source independence and may not auto-merge likely duplicate candidates. The project roadmap retains the target full working-version launch date of September 7, 2026.
