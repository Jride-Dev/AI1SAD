# Deployment Readiness

Phase 13 prepares AI1SAD for a controlled public demo deployment. It does not add billing, authentication, new providers, scraping, or scoring changes.

## Current Deployment Shape

- FastAPI entrypoint: `app.main:app`
- API router: `app.api_v1:router`
- Railway-style start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Frontend: React + Vite shell under `frontend/`
- Documentation: MkDocs Material portal under `docs/`

`docs/assets/railway_config.json` documents the Railway deployment command currently used for the backend service.

## Required Environment Variables

For a live backend connected to MongoDB Atlas:

```text
MONGODB_URI=<mongodb-atlas-uri>
MONGODB_DATABASE=AI1SAD
```

For a controlled demo without database writes:

```text
DEMO_MODE=true
ADMIN_EVENTS_ENABLED=false
ADMIN_SURVEILLANCE_ENABLED=false
ADMIN_ALERTS_ENABLED=false
API_ACCESS_ENABLED=false
```

## Optional Environment Variables

```text
SHARK_ATTACK_API_TITLE=AI1SAD Shark Attack Data API
API_FREE_RATE_LIMIT_PER_MINUTE=60
```

Live Open-Meteo and NOAA/NWS usage remains opt-in per request where implemented. No new providers are enabled by this phase.

## Demo Mode Rules

When `DEMO_MODE=true`:

- admin write settings resolve to disabled
- responses can include a `demo` label
- demo endpoints expose only safe public scenario summaries
- private notes, internal rules, restricted source details, and credentials must not be exposed
- billing and authentication remain disabled
- scoring behavior remains unchanged

## Health

`GET /health` works with minimal environment variables. In demo mode or without `MONGODB_URI`, it returns an operational status without attempting a MongoDB ping.

## Validation Checklist

- `F:\Python310\python.exe -m pytest -q`
- `npm run build` from `frontend/`
- `F:\Python310\python.exe -m mkdocs build`
- secret scan for MongoDB URIs, passwords, tokens, API keys, and secrets
- verify `site/`, `frontend/dist/`, and `frontend/tsconfig.tsbuildinfo` are ignored

## Safety Boundary

AI1SAD estimates environmental and surveillance-relevant shark encounter conditions. It does not predict individual attacks or guarantee safety outcomes.
