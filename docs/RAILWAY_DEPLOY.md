# Railway Deployment

This guide describes a controlled AI1SAD backend demo deployment on Railway.

## Start Command

Use:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

The same command appears in `docs/assets/railway_config.json`.

## Environment Variables

Minimum demo environment:

```text
DEMO_MODE=true
MONGODB_DATABASE=AI1SAD
ADMIN_EVENTS_ENABLED=false
ADMIN_SURVEILLANCE_ENABLED=false
ADMIN_ALERTS_ENABLED=false
API_ACCESS_ENABLED=false
```

Live MongoDB-backed environment:

```text
MONGODB_URI=<mongodb-atlas-uri>
MONGODB_DATABASE=AI1SAD
DEMO_MODE=false
```

## MongoDB Atlas Notes

- Store `MONGODB_URI` in Railway variables, not in the repository.
- Use a dedicated Atlas database/user for the demo environment.
- Keep IP access, credentials, and rotation policies managed outside the repo.
- Seed only public, privacy-reviewed demo data.

## Admin Writes

Admin write endpoints are disabled by default. In demo mode they remain disabled even if an admin environment variable is accidentally set to `true`.

## Provider Scope

This phase does not add providers, scraping, paid APIs, billing, or authentication. Existing live provider adapters remain opt-in where already implemented.

## Smoke Checks

After deploy:

```text
GET /health
GET /api/v1/demo/status
GET /api/v1/demo/scenarios
GET /api/v1/explain/replay?scenario_id=queensland_spearfishing_reef_tiger_bull_2026
```
