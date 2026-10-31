# Incident Globe

## Scope

The Incident Globe is an AI1SAD geographical explorer for shark-human incident records from 1990 through 2026. It combines the normalized scrubbed incident database with reviewed exact-match attribution from the private Sharks Happen source lane and reviewed registry cases explicitly marked for public visibility. The current release provides non-overlapping layers for 1990-1999, the 2000s, the 2010s, and 2020-2026.

Open the frontend at `http://localhost:5174/incident-globe`. The supporting read-only endpoint is `GET /api/v1/incidents-globe`.

## Current Build

The October 30, 2026 build contains:

| Measure | Count |
| --- | ---: |
| Deduplicated records | 4,090 |
| Records with validated coordinates | 2,704 |
| Source-provided coordinates | 531 |
| Contextual CSV2GEO coordinates | 1,776 |
| Contextual GeoNames coordinates | 396 |
| Reviewed public-registry named-beach centroids | 1 |
| Records retained without a validated map point | 1,386 |
| Explicit invalid/no-shark-involvement rows excluded | 205 |
| Sharks Happen rows considered in the period | 516 |
| Reviewed exact Sharks Happen matches attached | 110 |
| Standalone Sharks Happen source records | 406 |
| 1990-1999 records | 691 |
| 1990-1999 mapped / unresolved | 452 / 239 |

Unresolved locations remain visible in totals and filtering but are not placed on the globe. AI1SAD does not reuse coordinates from broad or ambiguous location text. The original cache keyed coordinates by location alone, which allowed names such as Chatham Island, Portland, North Beach, and Black Point to resolve to unrelated countries or inland places. The replacement contextual cache keys location, region, and country together. CSV2GEO results require relevance of at least `0.75`, containment within the stated Natural Earth country boundary, and no more than `25 km` distance from the Natural Earth coastline. The offline GeoNames pass requires stated-country agreement, supplied-region corroboration, exact or tightly bounded fuzzy matching, an allowed populated-place or coastal feature, rejection of near-tied candidates, and a coastline limit of `5 km` for ordinary places, `10 km` for parks, or `25 km` for large islands/bays/atolls. Reviewed ambiguous names are recorded separately and remain off-map. Source-provided coordinates are not rewritten by these checks.

## Interaction

- Select the 1990s, 2000s, 2010s, or 2020-2026 decade layer. The 1990s layer ends at 1999, so year 2000 appears only in the 2000s.
- Filter by `Provoked`, `Unprovoked`, `Unknown`, or `Conflicted`.
- Toggle `Fatal`, `Fatal and consumed/body not recovered`, `Non-fatal`, and `No injury` markers.
- Hover over a mapped marker for a compact summary.
- Select a marker to open an incident infographic with event fields, coordinate confidence, source attribution, links, and any approved media references.
- Open `Browse records` to inspect every unresolved incident without assigning it a guessed pin. The drawer follows the active decade, outcome, and provocation filters; summarizes named-locality, region-only, country-only, and no-location records; supports text, country, and region filtering; and opens the same source infographic as a mapped marker.
- Drag to rotate, use the mouse wheel or zoom controls to change scale, and toggle automatic rotation.
- Markers use front-face rendering and globe depth testing so points on the far hemisphere cannot appear through or around the Earth surface.

The globe uses NASA's [Blue Marble](https://visibleearth.nasa.gov/images/57723/the-blue-marble) imagery as its Earth texture. Contextual coordinate validation uses [Natural Earth](https://www.naturalearthdata.com/) 1:10m country and coastline geometry; those reference files are validation inputs rather than browser assets. The bounded offline resolver uses [GeoNames country dumps](https://download.geonames.org/export/dump/) and [feature codes](https://www.geonames.org/export/codes.html) under CC BY 4.0; the downloaded gazetteers remain ignored local build inputs, while accepted coordinates retain GeoNames provider and feature provenance.

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

Reviewed registry records enter the globe only when `public_visibility` is `public`. The adapter emits a victim-name-free record and only source links explicitly approved for public citation. Restricted records remain outside the globe. The Orient Beach case is the first record through this path; its coordinate is a reviewed named-beach centroid, its provocation remains `unknown`, and its recovered-body fatality remains `fatal` rather than `fatal_consumed`.

The API overlays these reviewed public registry records onto the stored MongoDB projection with an exact date/country/location duplicate guard. A later MongoDB rebuild containing the same case therefore does not produce a second marker. This keeps current reviewed cases available even when a local Atlas maintenance connection is unavailable; MongoDB remains the bulk historical projection.

The local projection is generated with:

```powershell
F:\Python310\python.exe -m app.services.incident_globe --mongo
```

This writes ignored local data to `data/public/incident_globe_1990_2026.json` and replaces the internal MongoDB `incident_globe` projection when MongoDB is enabled.

The original coordinate-review queue is `data/review/incident_globe_all_geocode_review_2026-10-03.csv`. The full-history sanitized vendor input is `data/review/incident_globe_csv2geo_1900_2026_upload_2026-10-03.csv`, the raw vendor result is `data/review/incident_globe_csv2geo_1900_2026_result_2026-10-03.csv`, and the validated cache is `data/review/incident_globe_context_geocodes_1900_2026.csv`. They contain location metadata and internal query IDs only; victim names, injuries, private analyst notes, credentials, and restricted registry data were not submitted. Every vendor result retains its validation status and provenance.

`scripts/resolve_incident_globe_geonames.py` reproduces the offline GeoNames pass. `data/review/incident_globe_geonames_rejections.csv` preserves reviewed ambiguity decisions rather than hard-coding guessed coordinates. GeoNames receives no AI1SAD incident data because its country files are downloaded and searched locally.

## Safety, Privacy, And Limits

- The projection is built from the scrubbed incident database and does not expose victim names or private analyst notes.
- Public registry projection is allowlisted by record visibility; restricted registry cases are excluded.
- Raw Sharks Happen workbook content and private fields remain outside the response.
- The feature does not change warning scoring, create alerts, create observations, alter replay artifacts, or determine species.
- Explicit invalid/no-shark-involvement rows are excluded. Questionable records remain source-attributed rather than silently discarded.
- No rights-cleared per-case image collection is currently available. The infographic supports approved media references but does not invent, scrape, or hotlink images.
- Mapped points come from source-provided coordinates or validated contextual results. Coordinate source and confidence remain visible in the infographic.
- Relevance, country, region, ambiguity, feature-type, and coastline checks prevent broad classes of wrong placement but do not prove street-level or offshore precision. Rejected results remain available for source enrichment and human review.
- `147` incident records have blank location text and cannot be safely geocoded. Other ambiguous or underspecified records remain unresolved; the resolver does not substitute country or region centroids.
- Unresolved does not mean excluded: all `1,386` unresolved records remain visible in filtered totals and in the searchable ledger. Location-resolution labels describe only the available geographic detail and do not raise coordinate confidence.
- Fatal records are plotted only when a source or contextual coordinate passes the same validation boundary; outcome severity never relaxes coordinate requirements.
- Incident density is not a risk rate and does not account for water-use exposure, reporting differences, or population.

## Validation

Validation completed October 30, 2026:

- focused GeoNames and Incident Globe tests: `22 passed`
- full backend tests: `358 passed`, with two existing FastAPI startup-event deprecation warnings
- frontend tests: `32 passed`
- frontend production build: passed
- local browser verification: the unresolved ledger exposed all `1,386` records, reported `1,240` named-locality, `92` region-only, `53` country-only, and `1` no-location record, and opened a source-attributed unmapped incident infographic at the mobile breakpoint
- local and MongoDB projection rebuild: `4,090` records; `2,704` mapped, `1,386` unresolved, `1,776` CSV2GEO coordinates, and `396` GeoNames coordinates
- Orient Beach public-registry projection: one mapped `fatal` record, `unknown` provocation, unconfirmed species, four reviewed public citations, and no restricted Glenfield projection
- 1990-1999 layer: `691` records; `452` mapped and `239` unresolved
- Full-history vendor validation: `1,914` unique contexts accepted; `1,115` low relevance, `562` country mismatch, `466` missing/invalid, `142` too far inland, and `43` unknown country boundary results rejected
- Chatham Island regression: the 21-Jul-2001 Massachusetts record resolves to `41.68227, -70.01460`, with `0.98` relevance and `0.58 km` coastline distance
- MongoDB projection rebuild: `4,090` records inserted
- live production API: `4,090` records, `2,704` mapped, and `1,386` unresolved
- live production fatal-2020s query: exactly one Orient Beach registry marker at `27.91513, -33.02495`, with `fatal` outcome, `unknown` provocation, no species value, and four source citations
- MkDocs strict build, README local-link check (`62` checked, `0` missing), changed-file secret scan, prohibited-language scan, Git whitespace check, and frontend production build: passed

## Next Handoff

The next bounded globe work is source-backed promotion from the unresolved ledger into reviewed coordinates, rights review for case media, and publication of the already-prepared pre-1990 decade layers. Historical publication must preserve source independence and may not auto-merge likely duplicate candidates or replace broad location evidence with a precise-looking point. The project roadmap retains the target full working-version launch date of September 7, 2026.
