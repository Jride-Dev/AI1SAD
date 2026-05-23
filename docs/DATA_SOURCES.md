# Data Sources

This repository is designed around the local source files provided by the project owner. The source folder preserved at `data/raw` contains:

- `attacks.csv`
- `attacks.xlsx`
- Generated analysis spreadsheets
- Geocode cache files
- Prior local analysis scripts
- A generated map HTML file

Only `attacks.csv` is used by the default export pipeline. Other original files should remain preserved under `data/raw` for reproducibility, but they are not served by the API.

## Raw Data Policy

Raw files are retained locally to make the cleaning process auditable. They may include personal names, source notes, PDF links, and other fields unsuitable for public API responses. For that reason, `data/raw/*` is ignored by Git except for `data/raw/README.md`.

Before publishing the repository, verify that every raw file in `data/raw` can be legally shared. If any file is restricted, move it to `data/private`; that directory is ignored by Git.

## Public Export Policy

The generated public export removes or avoids:

- Victim names
- Private notes
- Investigator/source notes
- PDF and href links
- Exact addresses
- Geocode caches and precise coordinates
- Restricted-source content
