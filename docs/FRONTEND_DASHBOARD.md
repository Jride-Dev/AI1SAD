# Frontend Dashboard

Phase 10 adds the first AI1SAD interface shell under `frontend/`.

The dashboard is a React + Vite app. It visualizes existing API outputs and intentionally does not duplicate warning, surveillance, replay, alert, provider, regional-pack, or scoring logic in the browser.

## Views

- Live Warning Map
- Surveillance Priority View
- Replay Explorer
- Regional Pack Explorer
- Alerts View
- Provider Health View

## Operational Map

Phase 14 replaces the static map placeholder with an interactive Leaflet map.

The map displays API or mock-output layers for:

- surveillance priority
- warning score
- activity hazard
- active alerts
- replay heatmap cells
- demo scenario points

The map includes a scenario selector for Horseshoe Reef 2026, Queensland Spearfishing 2026, Florida inlet/crowded beach, Hawaii October tiger shark context, and Red Sea anomaly context.

Clicking a zone, heatmap cell, alert, or scenario point opens a "Why this zone?" panel showing coordinates, active pack, score split, dominant factors, factor contributions, confidence breakdown, recommended action, recommended surveillance pattern, and the API disclaimer.

Low-warning/high-surveillance examples are labeled as activity/habitat-specific surveillance priority so users can understand the split without treating it as a contradiction.

## API Client

The frontend client lives in `frontend/src/api/client.ts`.

It wraps existing backend routes:

- `GET /api/v1/warnings/location`
- `GET /api/v1/surveillance/search-zones`
- `GET /api/v1/replay/run`
- `GET /api/v1/packs`
- `GET /api/v1/alerts/active`
- `GET /api/v1/provider-health`
- `GET /api/v1/explain/location`

The wrapper falls back to mock data so the interface can run before the backend is live.

## Explainability Panels

Phase 11 adds explanation panels to the dashboard shell:

- factor contribution cards
- confidence breakdown display
- provider freshness display
- Why this zone? section
- explanation summary text for alerts when provided by the backend

The frontend consumes explanation endpoint responses only. It does not calculate factor contributions, confidence, warning scores, surveillance priority, alert levels, or operational recommendations.

The Leaflet map follows the same rule. It renders backend or mock values but does not implement model scoring.

## Mock Mode

Mock mode is enabled by default.

```powershell
cd frontend
npm install
npm run dev
```

To point the shell at a local backend:

```powershell
$env:VITE_AI1SAD_USE_MOCKS="false"
$env:VITE_AI1SAD_API_BASE_URL="http://localhost:8000"
npm run dev
```

If a backend request fails, the client falls back to mock data instead of crashing.

## Demo Banner

When demo mode is enabled, the dashboard shows:

```text
AI1SAD Demo Environment
Outputs are operational intelligence examples, not individual attack predictions.
```

Use:

```powershell
$env:VITE_AI1SAD_DEMO_MODE="true"
```

The banner is a public-context label only. It does not add authentication, billing, or scoring behavior.

## Boundaries

The frontend must not implement or fork model logic. Scores, warning bands, surveillance priority, alert levels, confidence, provider freshness, and pack notices should come from backend API responses.

This phase does not add:

- authentication
- billing UI
- new model logic
- live scraping
- new providers
- payment processing

## Validation

Frontend validation uses:

```powershell
cd frontend
npm test
npm run build
```
