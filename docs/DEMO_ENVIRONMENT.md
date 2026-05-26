# Demo Environment

AI1SAD demo mode is intended for controlled public demonstrations where the project should be inspectable without exposing private records or enabling write operations.

## Enable Demo Mode

```text
DEMO_MODE=true
```

Demo mode is not authentication, billing, or production access control. It is a deployment safety profile for public demos.

For the public launch checklist, see [Public Demo Launch](PUBLIC_DEMO_LAUNCH.md).

## Demo Endpoints

`GET /api/v1/demo/status`

Returns demo status, database configuration state, write-disable state, and the public disclaimer.

`GET /api/v1/demo/scenarios`

Returns safe scenario summaries for:

- Horseshoe Reef
- Queensland Spearfishing
- Florida crowded beach/inlet
- Hawaii October tiger shark context
- Red Sea anomaly context

The frontend uses these summaries with local public coordinates to populate the operational map selector when the backend does not provide coordinates directly.

## Response Labeling

When demo mode is enabled, selected public API responses include:

```json
{
  "demo": {
    "demo_mode": true,
    "demo_label": "AI1SAD controlled public demo"
  }
}
```

## Data Safety

Demo responses must not include:

- victim names
- private notes
- internal rules
- restricted source details
- credentials
- raw provider secrets

## Frontend Demo Mode

The frontend can run without backend secrets using mock mode:

```powershell
cd frontend
npm install
npm run dev
```

To point it at a demo backend:

```powershell
$env:VITE_AI1SAD_USE_MOCKS="false"
$env:VITE_AI1SAD_API_BASE_URL="https://<demo-backend>"
npm run dev
```

In demo mode, the operational map can render:

- demo scenario points
- replay heatmap cells
- surveillance zones
- active alert markers
- warning, activity hazard, and surveillance score markers

If the backend is unavailable, mock data preserves all map states without requiring secrets, private data, or live providers.

The dashboard shows a demo banner when demo mode is enabled:

```text
AI1SAD Demo Environment
Outputs are operational intelligence examples, not individual attack predictions.
```

Set `VITE_AI1SAD_DEMO_MODE=true` for public demo frontend builds. Use `VITE_AI1SAD_USE_MOCKS=true` for a standalone demo shell, or `VITE_AI1SAD_USE_MOCKS=false` with `VITE_AI1SAD_API_BASE_URL` for a hosted backend.

## Provider Failure Behavior

Public demo routes should not expose raw provider failures, stack traces, credentials, or response bodies. Missing or stale provider data should appear as freshness/confidence context where implemented.

## Safety Boundary

AI1SAD does not predict individual attacks, infer shark intent, issue beach closures, or guarantee safety. Demo mode preserves that language.
