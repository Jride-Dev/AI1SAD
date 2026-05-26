# Public Demo Launch

This checklist prepares AI1SAD for a controlled public demo. It does not add billing, authentication, new providers, scraping, or scoring changes.

AI1SAD estimates environmental and surveillance-relevant shark encounter conditions. It does not predict individual attacks or guarantee safety outcomes.

## Recommended Demo Mode

Use demo mode for a public launch:

```text
DEMO_MODE=true
```

In demo mode:

- admin writes are disabled
- selected public responses include demo labeling
- demo scenarios expose only public summaries
- private notes, internal rules, restricted source details, credentials, and raw provider secrets must not be exposed
- provider failures should lower confidence or fall back safely rather than crash public routes
- scoring behavior remains unchanged

## Required Environment Variables

Minimum controlled demo backend:

```text
DEMO_MODE=true
MONGODB_DATABASE=AI1SAD
ADMIN_EVENTS_ENABLED=false
ADMIN_SURVEILLANCE_ENABLED=false
ADMIN_ALERTS_ENABLED=false
API_ACCESS_ENABLED=false
```

MongoDB-backed public demo:

```text
MONGODB_URI=<stored-in-hosting-secret-store>
MONGODB_DATABASE=AI1SAD
DEMO_MODE=true
```

Do not commit `.env`, MongoDB connection strings, provider credentials, API keys, passwords, tokens, or private data.

## Optional Environment Variables

```text
SHARK_ATTACK_API_TITLE=AI1SAD Shark Attack Data API
API_FREE_RATE_LIMIT_PER_MINUTE=60
```

Frontend demo deployment:

```text
VITE_AI1SAD_DEMO_MODE=true
VITE_AI1SAD_USE_MOCKS=false
VITE_AI1SAD_API_BASE_URL=https://<demo-backend>
```

For a standalone frontend demo without a backend, keep mock mode enabled:

```text
VITE_AI1SAD_DEMO_MODE=true
VITE_AI1SAD_USE_MOCKS=true
```

## Railway Backend Checklist

- Confirm start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Store `MONGODB_URI` only in Railway variables if using Atlas.
- Keep `DEMO_MODE=true` for public demo deployments.
- Keep all admin write flags false.
- Keep `API_ACCESS_ENABLED=false` unless real key storage is deployed later.
- Seed only public, privacy-reviewed demo data.
- Run smoke checks after deploy.

## MongoDB Atlas Notes

- Use a dedicated demo database/user.
- Use least-privilege credentials.
- Rotate credentials outside the repository.
- Do not seed victim names, private notes, exact addresses, restricted-source material, or internal analyst records into public collections.
- Public API routes should continue filtering by `visibility="public"`.

## Frontend Checklist

- Demo banner appears when demo mode is enabled.
- Map loads with mock data if the backend is unavailable.
- Scenario selector includes Horseshoe Reef, Queensland, Florida, Hawaii, and Red Sea.
- "Why this zone?" panels load explanation fields from API/mock responses.
- Low warning and high surveillance priority are labeled as activity/habitat-specific surveillance priority.
- Frontend does not calculate model scores.

## MkDocs GitHub Pages Checklist

- `mkdocs build` succeeds.
- `site/` remains ignored.
- Public docs include disclaimer, demo environment, deployment readiness, Railway deploy, operational mapping, and usage policy pages.
- No secrets, private data, or restricted source content appear in generated docs.

## Public Launch Smoke Checks

Run:

```powershell
python scripts/smoke_demo.py --base-url https://<demo-backend>
```

The script checks:

- `GET /health`
- `GET /api/v1/demo/status`
- `GET /api/v1/demo/scenarios`
- `GET /api/v1/explain/location`

Manual checklist:

- health endpoint works
- demo scenarios load
- map loads
- explanations load
- alerts demo loads
- docs site builds
- no secrets exposed
- no private/internal signals exposed

## Safety Boundary

The public demo is an operational intelligence demonstration. It is not an individual attack prediction system, beach closure authority, shark-intent inference system, or substitute for local lifeguards, emergency services, wildlife agencies, marine agencies, weather offices, or beach managers.
