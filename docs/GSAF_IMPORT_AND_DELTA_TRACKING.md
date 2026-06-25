# GSAF Import And Delta Tracking

Phase 26A adds a local import and audit path for downloaded Global Shark Attack File spreadsheets.

GSAF is treated as an upstream source. It is not the final AI1SAD incident model, and imported rows do not overwrite existing AI1SAD incident records.

Target full working-version launch remains September 7, 2026.

## Scope

The importer reads a manually downloaded local GSAF file, normalizes available columns into staging records, computes stable row fingerprints, compares those fingerprints with a local baseline, and writes internal JSON artifacts.

The importer does not:

- create warnings or public alerts
- create replay facts or modify replay outputs
- change scoring weights
- create public feed entries
- create drone observations
- scrape websites or fetch live GSAF data
- redistribute raw GSAF rows in public outputs
- replace the AI1SAD incident database

## Local File Layout

Expected local paths are:

```text
data/imports/gsaf/raw/
data/imports/gsaf/staging/
data/imports/gsaf/reports/
```

These folders are for local/manual intake. Raw spreadsheets, staging JSON, report JSON, and baseline JSON remain local and ignored by Git. Only `.gitkeep` scaffolding is tracked.

Place a downloaded file at a path such as:

```text
data/imports/gsaf/raw/latest_gsaf.xls
```

Do not commit downloaded GSAF files unless rights and redistribution rules are explicitly approved.

## Entry Point

Run from the repository root:

```powershell
F:\Python310\python.exe -m app.services.gsaf_importer --input data/imports/gsaf/raw/latest_gsaf.xls --report data/imports/gsaf/reports/latest_import_report.json
```

Optional outputs:

```powershell
F:\Python310\python.exe -m app.services.gsaf_importer `
  --input data/imports/gsaf/raw/latest_gsaf.xlsx `
  --staging data/imports/gsaf/staging/latest_staging.json `
  --report data/imports/gsaf/reports/latest_import_report.json `
  --baseline data/imports/gsaf/staging/gsaf_baseline_fingerprints.json
```

Add `--update-baseline` only when the current import should become the new comparison baseline.

## Supported Formats

The importer supports:

- `.csv` through Python's standard CSV reader
- `.xlsx` through the existing `pandas` and `openpyxl` dependencies
- `.xls` through the existing `pandas` and `xlrd` dependencies

Phase 26A did not add a new dependency for `.xls` support.

If a local environment lacks the declared Excel reader packages, install the existing `requirements.txt` dependencies rather than adding a new parser.

## Staging Fields

Each normalized staging record preserves source provenance and conservative AI1SAD candidates:

- `source_name`
- `source_file`
- `source_row_number`
- `source_case_number`
- `source_date_raw`
- `date_normalized`
- `year`
- `country`
- `area`
- `location`
- `activity`
- `sex`
- `age`
- `injury`
- `fatal_y_n`
- `time_raw`
- `species_raw`
- `investigator_or_source_raw`
- `pdf_case_link_raw`
- `original_type_raw`
- `ai1sad_incident_type_candidate`
- `ai1sad_behavioral_hypothesis_candidate`
- `ai1sad_behavioral_hypothesis_provisional`
- `ai1sad_behavior_confidence`
- `normalization_warnings`
- `row_fingerprint`
- `match_key`
- `imported_at`

Precise dates are normalized only when the source provides a parseable full date. Vague values such as month-only, season-only, reported dates, uncertain dates, or year-only values remain in `source_date_raw`, leave `date_normalized` empty, and add a warning.

## Behavioral Hypotheses

Behavior candidates are provisional staging hints only. They are not confirmed shark intent and are not public warning facts.

Current conservative candidates include:

- `attempted_predation_event`
- `territorial_displacement`
- `accidental_contact`
- `predatory_probe`
- `competitive_food_response`
- `scavenging_context`
- `mistaken_identity_candidate`
- `unknown_insufficient_evidence`
- `object_contact_or_investigative_bite`

The importer does not default to mistaken identity.

Questionable, invalid, unverified, or unconfirmed source rows remain `unknown_insufficient_evidence` with `unknown` confidence.

Spearfishing, fishing, bait, catch, or stringer context may map to `competitive_food_response` with provisional confidence. Injury text that suggests consumption, missing body, or repeated engagement may map to `attempted_predation_event`, still provisional and low-confidence.

Allowed confidence labels are:

- `unknown`
- `weak`
- `plausible`
- `probable`

Phase 26A does not emit confirmed behavior classifications.

## Delta Tracking

The baseline file is:

```text
data/imports/gsaf/staging/gsaf_baseline_fingerprints.json
```

The importer compares the current staging records with the baseline and reports:

- `total_rows`
- `new_rows`
- `changed_rows`
- `unchanged_rows`
- `possibly_removed_rows`
- `duplicate_case_numbers`
- `malformed_rows`
- `date_parse_warnings`
- `species_parse_warnings`
- `behavior_mapping_warnings`

Rows are matched by case number when available. If a case number is missing, the importer uses a fallback key based on date, country, area, location, activity, and injury.

Fingerprints are based on normalized source fields, not row order or import time.

## Privacy And Rights

GSAF raw files can contain sensitive personal details, source notes, and license-unclear text. AI1SAD stores local staging and audit artifacts for internal review only until rights and public release rules are confirmed.

Public docs should describe the import workflow and use synthetic examples only. Do not paste raw GSAF rows into public docs or public API output.

## Phase 26B Handoff

The next planned phase is Phase 26B: AI1SAD Shark-Human Incident Registry Schema.

Phase 26B should design the richer AI1SAD registry model and decide how reviewed upstream records become first-class internal incidents. It should not be started automatically from Phase 26A.
