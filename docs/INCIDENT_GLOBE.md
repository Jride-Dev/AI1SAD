# Incident Globe

## Scope

The Incident Globe is a local AI1SAD geographical explorer for shark-human incident records from 2000 through 2026. It combines the normalized scrubbed incident database with reviewed exact-match attribution from the private Sharks Happen source lane. The first release provides decade layers for the 2000s, 2010s, and 2020-2026.

Open the frontend at `http://localhost:5174/incident-globe`. The supporting read-only endpoint is `GET /api/v1/incidents-globe`.

## Current Build

The October 3, 2026 build contains:

| Measure | Count |
| --- | ---: |
| Deduplicated records | 3,398 |
| Records with source-provided coordinates | 452 |
| Records retained without a reviewed map point | 2,946 |
| Unreviewed location-only cache coordinates withheld | 1,463 |
| Explicit invalid/no-shark-involvement rows excluded | 174 |
| Sharks Happen rows considered in the period | 422 |
| Reviewed exact Sharks Happen matches attached | 96 |
| Standalone Sharks Happen source records | 326 |

Unresolved locations remain visible in totals and filtering but are not placed on the globe. AI1SAD does not invent coordinates from broad or ambiguous location text. The original cache keyed coordinates by location text alone, which allowed names such as Chatham Island, Portland, North Beach, and Black Point to resolve to unrelated countries or inland places. Cache rows now require an explicit `ReviewStatus` of `reviewed`, `verified`, or `approved` before they can be plotted, followed by country-envelope validation. Source-provided coordinates are not rewritten by this check.

## Interaction

- Select the 2000s, 2010s, or 2020-2026 decade layer.
- Filter by `Provoked`, `Unprovoked`, `Unknown`, or `Conflicted`.
- Toggle `Fatal`, `Fatal and consumed/body not recovered`, `Non-fatal`, and `No injury` markers.
- Hover over a mapped marker for a compact summary.
- Select a marker to open an incident infographic with event fields, coordinate confidence, source attribution, links, and any approved media references.
- Drag to rotate, use the mouse wheel or zoom controls to change scale, and toggle automatic rotation.
- Markers use front-face rendering and globe depth testing so points on the far hemisphere cannot appear through or around the Earth surface.

The globe uses NASA's [Blue Marble](https://visibleearth.nasa.gov/images/57723/the-blue-marble) imagery as its Earth texture.

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

The complete coordinate-review queue is `data/review/incident_globe_all_geocode_review_2026-10-03.csv` for all 1,463 withheld cache-derived records. The earlier bounded queues remain at `data/review/incident_globe_country_mismatch_review_2026-10-03.csv` and `data/review/incident_globe_australia_coordinate_review_2026-10-03.csv`. Reviewers can fill `reviewed_latitude`, `reviewed_longitude`, `review_status`, and `review_notes`; rejected coordinates and source identifiers remain alongside the blank review fields for provenance.

## Safety, Privacy, And Limits

- The projection is built from the scrubbed incident database and does not expose victim names or private analyst notes.
- Raw Sharks Happen workbook content and private fields remain outside the response.
- The feature does not change warning scoring, create alerts, create observations, alter replay artifacts, or determine species.
- Explicit invalid/no-shark-involvement rows are excluded. Questionable records remain source-attributed rather than silently discarded.
- No rights-cleared per-case image collection is currently available. The infographic supports approved media references but does not invent, scrape, or hotlink images.
- Current mapped points come from source-provided coordinates. Future reviewed cache points must retain their approximate provenance in the infographic.
- Country-envelope checks are deliberately broad and apply after explicit cache review. They prevent obvious cross-country placement errors but do not replace human coordinate review or prove that a remaining point is exact.
- No fatal or fatal-consumed record currently has a source-provided coordinate in this projection. Fatal records remain in totals and filters but stay unplotted until their coordinates are reviewed.
- Incident density is not a risk rate and does not account for water-use exposure, reporting differences, or population.

## Validation

Validation completed October 3, 2026:

- focused Incident Globe tests: `6 passed`
- full backend tests: `338 passed`, with two existing FastAPI startup-event deprecation warnings
- frontend tests: `31 passed`
- frontend production build: passed
- MongoDB projection rebuild: `3,398` records inserted; `452` source-coordinate records mapped, `2,946` unresolved, and `1,463` unreviewed cache coordinates withheld
- Chatham Island regression fixture: the 21-Jul-2001 Massachusetts record cannot use the New Zealand cache coordinate
- live production verification: the API exposes the `1,463`-record withheld-cache count, the Chatham Island record has no coordinates, zero fatal records are plotted, and the browser renders `3,398` total, `452` mapped, and `2,946` unresolved
- MkDocs strict build, README local-link check, changed-file secret scan, prohibited-language scan, and Git whitespace check: passed

## Next Handoff

The next bounded globe work is human-reviewed coordinate resolution for the 2,946 unresolved records, beginning with the 1,463-row cache review queue, rights review for case media, and expansion to pre-2000 decades. That work must preserve source independence and may not auto-merge likely duplicate candidates. The project roadmap retains the target full working-version launch date of September 7, 2026.
