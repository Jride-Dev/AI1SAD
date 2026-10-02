# Incident Globe

## Scope

The Incident Globe is a local AI1SAD geographical explorer for shark-human incident records from 2000 through 2026. It combines the normalized scrubbed incident database with reviewed exact-match attribution from the private Sharks Happen source lane. The first release provides decade layers for the 2000s, 2010s, and 2020-2026.

Open the frontend at `http://localhost:5174/incident-globe`. The supporting read-only endpoint is `GET /api/v1/incidents-globe`.

## Current Build

The October 2, 2026 build contains:

| Measure | Count |
| --- | ---: |
| Deduplicated records | 3,398 |
| Records with usable coordinates | 1,915 |
| Records retained without a map point | 1,483 |
| Explicit invalid/no-shark-involvement rows excluded | 174 |
| Sharks Happen rows considered in the period | 422 |
| Reviewed exact Sharks Happen matches attached | 96 |
| Standalone Sharks Happen source records | 326 |

Unresolved locations remain visible in totals and filtering but are not placed on the globe. AI1SAD does not invent coordinates from broad or ambiguous location text.

## Interaction

- Select the 2000s, 2010s, or 2020-2026 decade layer.
- Filter by `Provoked`, `Unprovoked`, `Unknown`, or `Conflicted`.
- Toggle `Fatal`, `Fatal and consumed/body not recovered`, `Non-fatal`, and `No injury` markers.
- Hover over a mapped marker for a compact summary.
- Select a marker to open an incident infographic with event fields, coordinate confidence, source attribution, links, and any approved media references.
- Drag to rotate, use the mouse wheel or zoom controls to change scale, and toggle automatic rotation.

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

## Safety, Privacy, And Limits

- The projection is built from the scrubbed incident database and does not expose victim names or private analyst notes.
- Raw Sharks Happen workbook content and private fields remain outside the response.
- The feature does not change warning scoring, create alerts, create observations, alter replay artifacts, or determine species.
- Explicit invalid/no-shark-involvement rows are excluded. Questionable records remain source-attributed rather than silently discarded.
- No rights-cleared per-case image collection is currently available. The infographic supports approved media references but does not invent, scrape, or hotlink images.
- A mapped point may be approximate. Coordinate confidence and provenance are shown in the infographic.
- Incident density is not a risk rate and does not account for water-use exposure, reporting differences, or population.

## Next Handoff

The next bounded globe work is human-reviewed coordinate resolution for the 1,483 unresolved records, rights review for case media, and expansion to pre-2000 decades. That work must preserve source independence and may not auto-merge likely duplicate candidates. The project roadmap retains the target full working-version launch date of September 7, 2026.
