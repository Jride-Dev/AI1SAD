# Provider Health

Live-data systems decay unless provider health is tracked directly.

AI1SAD tracks provider status in:

- `provider_runs`: successful ingestion attempts.
- `provider_failures`: failed ingestion attempts and safe error summaries.
- `provider_health`: latest health rollup per provider.

## Provider Health Shape

```json
{
  "provider": "open_meteo",
  "last_success": "2026-05-23T06:21:00Z",
  "last_error": null,
  "records_ingested": 483,
  "status": "healthy"
}
```

For Open-Meteo live lookups, `records_ingested` counts the normalized weather signals generated for the request. Failures set `status="degraded"` and record a safe `last_error` summary.

For NOAA/NWS live lookups, `records_ingested` counts normalized active weather-alert signals. U.S. requests with no active alerts can still be `healthy` with zero records. Outside-U.S. coordinates are recorded as `not_applicable`, not failures.

For NOAA CoastWatch SST, Phase 9C is offline/test-first. Mocked or pre-fetched SST records normalize into signals and data freshness, but live ERDDAP provider runs are not enabled yet.

For human exposure, Phase 9D uses static/offline profiles. Signals include data freshness and confidence, but no live attendance, parking, web scraping, or paid crowd-provider calls are enabled yet.

For biological events, Phase 9E uses static/manual/offline examples and reviewed event inputs. Signals include data freshness, expiration windows, confidence, source notes, and pack association. No news scraping, social-media scraping, live agency feeds, or paid ecological APIs are enabled yet.

## Public API

`GET /api/v1/provider-health` returns provider rollups and recent failures with credentials, private notes, and restricted details excluded.

## Failure Rules

- Provider failures must not crash warning or surveillance endpoints.
- Open-Meteo failures must not crash warning or alert-evaluation endpoints.
- NOAA/NWS failures or outside-U.S. coordinates must not crash warning or alert-evaluation endpoints.
- Static biological-event provider output should expire stale carcass/fish-kill records instead of silently carrying old high-impact signals forward.
- Failed providers should lower confidence through missing or stale data freshness.
- Error summaries must not include API keys, passwords, tokens, or full raw response dumps.
- Placeholder providers should fail closed with clear messages until terms, credentials, and data contracts are reviewed.
