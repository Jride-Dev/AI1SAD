# Sharks Happen Source Intake

## Purpose

AI1SAD treats Hal's `Sharks Happen Stats.xlsx`, associated with `@sharkshappen` on YouTube, as an independent source. It is not subordinate to GSAF, government reporting, or any single institutional dataset. Each source can contribute claims, corroboration, and conflicts; no source is silently converted into final truth.

The importer is local and bounded. It does not scrape YouTube, fetch external data, create public endpoints, or infer missing facts.

## Current Import

The supplied workbook contains `864` substantive case rows. The remaining worksheet rows are count-only placeholders or formula/summary rows and are excluded.

The October 2, 2026 import produced:

- `864` private source records
- `162` exact cross-source duplicate candidates
- `435` likely cross-source duplicate candidates
- `267` unmatched rows
- `8` rows participating in possible within-workbook repeats
- `27` unparsed/irregular date values retained with warnings
- `0` automatic merges
- `0` automatic registry promotions

All `864` records were upserted into the configured MongoDB `sharks_happen_sources` collection. One internal run summary was inserted into `sharks_happen_import_reports`.

## Run The Import

Place the private workbook at:

```text
data/imports/sharks_happen/raw/Sharks Happen Stats.xlsx
```

Then run:

```powershell
F:\Python310\python.exe -m app.services.sharks_happen_importer --input "data/imports/sharks_happen/raw/Sharks Happen Stats.xlsx" --mongo
```

Outputs:

- staging JSON: `data/imports/sharks_happen/staging/latest_sharks_happen_sources.json`
- import report: `data/imports/sharks_happen/reports/latest_sharks_happen_import_report.json`
- duplicate-review CSV: `data/imports/sharks_happen/reports/latest_duplicate_review.csv`

These paths are ignored by Git. The workbook, victim names, raw claims, and candidate review data must remain private unless rights and public-release rules are reviewed separately.

## Duplicate Comparison

Comparison uses the existing local `data/processed/complete_incidents_scrubbed.sqlite`, currently containing `40,309` normalized source rows from GSAF-style datasets and the Australian Shark-Incident Database.

Candidates are scored using available date, country, area/location, activity, source species label, and explicit fatality fields. The review output preserves matched and conflicting fields. Blank fatality values do not become `false`; blank species values do not become a species identification. Abbreviations such as `GW` remain raw source labels.

An `exact_candidate` requires an exact full date, matching normalized country, and a high location similarity. A `likely_candidate` requires a bounded score plus matching year and location/area support. Both labels require human review. `unmatched` means no candidate crossed the current threshold; it does not mean the incident did not happen.

## Provenance And Safety Boundaries

- Values are claims from the supplied workbook, not AI1SAD-confirmed facts.
- GSAF and government records remain independent source claims, not automatic authorities.
- Concerns about institutional bias can be recorded as review context only when evidence supports them.
- The source has no per-row citation URL or publication-reference columns, so independent corroboration remains necessary.
- Source species labels are not promoted to official species status.
- No behavior or shark intent is inferred.
- No warnings, alerts, public feeds, replay facts, scoring changes, provider signals, or drone observations are created.
- No duplicate candidate is automatically merged, deleted, or promoted.

## Known Limitations

- Many source species labels are blank or abbreviated.
- Shark-size text is absent from many rows, so the workbook's over-six-foot scope cannot be independently verified for every row from workbook fields alone.
- Fatality is blank or uncertain on many rows and remains unknown.
- Irregular date strings require later review.
- Duplicate matching does not use victim names against the scrubbed comparison database because victim names are intentionally absent there.
- Candidate thresholds favor review recall and can produce false positives; the CSV queue is the human adjudication surface.

## Handoff

Review exact candidates first, then likely candidates with conflicting fields. Any future promotion into an AI1SAD registry case must preserve this source link alongside corroborating and conflicting sources. This source addition does not begin Phase 26D. The roadmap's target full working-version launch date remains September 7, 2026.
