# Source Comparison Workflow

This project compares and consolidates local GSAF-style files, public GitHub mirrors, the Australian Shark-Incident Database, and the live GSAF spreadsheet.

Hal's privately supplied Sharks Happen workbook is maintained as an additional independent source lane. It is compared with the consolidated database but is not automatically folded into its canonical records.

## Sources

| Source | Status | Notes |
| --- | --- | --- |
| `data/raw/attacks.csv` | Local | Legacy GSAF-style source with 6,302 rows. |
| `GSAF5.xls` | Downloaded | Live spreadsheet from Shark Attack File. |
| `cjabradshaw/AustralianSharkIncidentDatabase` | Cloned | Structured Australia incident data with coordinates/species fields. |
| `N-Enzer/SharkAttackAnalysis` | Cloned | GSAF/Kaggle-style `attacks.csv`, includes blank trailing rows. |
| `ordovas/pandas-project` | Cloned | GSAF/Kaggle-style raw and cleaned CSV files. |
| `teajay/global-shark-attacks` | Pending auth | Kaggle CLI/API auth is needed for automated download. |
| Florida Museum ISAF | Reference | Used for provenance and ethics context; detailed individual records are restricted. |

## Build Command

```powershell
python scripts/build_complete_database.py
```

Outputs are written to `data/processed`:

- `complete_incidents_scrubbed.csv`
- `complete_incidents_scrubbed.jsonl`
- `complete_incidents_scrubbed.sqlite`

Reports are written to `reports`:

- `source_comparison_summary.json`
- `source_inventory.json`

## Current Local Build

The latest local build normalized 40,309 source rows into 8,173 unique scrubbed records after duplicate matching.

## Sharks Happen Comparison

The October 2, 2026 local import retained `864` substantive Sharks Happen rows. Comparison against the `40,309` normalized source rows found `162` exact candidates, `435` likely candidates, and `267` unmatched rows. Eight workbook rows participate in possible within-source repeat groups. These classifications are review aids, not adjudications: no records were merged, deleted, promoted, or marked false.

The review queue is local at `data/imports/sharks_happen/reports/latest_duplicate_review.csv`. It includes the source row, top candidate, score, matched fields, conflicts, and possible within-workbook duplicate ids. The workbook and review queue are ignored because they include victim names and license/redistribution status has not been established.

Quality checks from the generated report:

- Year range: 1500 to 2026
- Unique countries: 213
- Missing year: 147 unique records
- Missing country: 54 unique records
- Missing public location: 1,741 unique records
- Invalid fatal values: 0
- Records with source-provided coordinates: 1,196
- Invalid coordinate values: 0

## Privacy Rules

The complete processed database is scrubbed:

- No victim names
- No investigator/source notes
- No per-case PDF or href links
- Street-address-like strings redacted from public locations
- Raw source files remain ignored by Git
