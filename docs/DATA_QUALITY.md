# Data Quality

The seed workflow starts from scrubbed multi-source outputs built by:

```powershell
python scripts/build_complete_database.py
python scripts/seed_mongodb_collections.py --replace
```

Current local build summary:

- Normalized source rows: 40,309
- Unique deduped records: 8,173
- Duplicate source rows: 32,136
- Year range: 1500 to 2026
- Unique countries: 213
- Invalid fatal values: 0
- Records with coordinates: 1,196
- Invalid coordinate values: 0

Known limitations:

- Some historical records have missing country, year, or location fields.
- Species labels are source-derived and often descriptive rather than taxonomic.
- Incident counts do not equal risk because exposure data is not included.
- Kaggle import still requires authenticated Kaggle access.

