# Source Comparison Workflow

This project compares and consolidates local GSAF-style files, public GitHub mirrors, the Australian Shark-Incident Database, and the live GSAF spreadsheet.

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
