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

## Public API

`GET /api/v1/provider-health` returns provider rollups and recent failures with credentials, private notes, and restricted details excluded.

## Failure Rules

- Provider failures must not crash warning or surveillance endpoints.
- Open-Meteo failures must not crash warning or alert-evaluation endpoints.
- Failed providers should lower confidence through missing or stale data freshness.
- Error summaries must not include API keys, passwords, tokens, or full raw response dumps.
- Placeholder providers should fail closed with clear messages until terms, credentials, and data contracts are reviewed.
