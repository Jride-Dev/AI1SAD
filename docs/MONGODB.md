# MongoDB Loading

MongoDB credentials must stay in a local `.env` file or process environment. Do not commit real connection strings.

Required local environment:

```text
MONGODB_URI=<your-mongodb-atlas-connection-string>
MONGODB_DATABASE=AI1SAD
```

Build the cleaned local data first:

```powershell
python scripts/build_complete_database.py
```

Dry-run the Mongo loader:

```powershell
python scripts/load_mongodb.py --dry-run
```

Load the current scrubbed dataset:

```powershell
python scripts/load_mongodb.py --replace-collection
```

Default collections:

- `incidents_scrubbed`: one scrubbed source row per document, including duplicate markers.
- `dataset_builds`: latest build summary, source inventory, and privacy metadata.

The loader does not include victim names, investigator/source notes, PDF links, href links, or private raw fields.
