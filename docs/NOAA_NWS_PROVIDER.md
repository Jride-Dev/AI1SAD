# NOAA/NWS Provider

Phase 9B activates NOAA/NWS as a no-key U.S. weather-alert provider.

The integration uses the National Weather Service API for active alerts at a latitude/longitude. It is U.S.-only; outside supported U.S. coordinates, AI1SAD returns provider status `not_applicable` and does not call the provider.

## Data Fetched

AI1SAD requests:

```text
https://api.weather.gov/alerts/active?point={lat},{lon}
```

Supported alert contexts include:

- flood alerts
- thunderstorms
- rip current statements
- coastal flood advisories
- high surf advisories
- marine weather warnings when available

## Signal Types

NOAA/NWS alerts normalize into Signal-shaped records with these signal types:

- `weather_alert`
- `flood_alert`
- `thunderstorm_alert`
- `coastal_flood_alert`
- `rip_current_alert`
- `high_surf_alert`
- `marine_warning`

Each signal includes public-safe metadata such as alert event, headline, severity, urgency, certainty, provider timestamp, expiration, confidence, source, risk relevance, and data freshness.

## API Usage

Warning endpoint:

```text
GET /api/v1/warnings/location?lat=27.7&lon=-80.2&use_noaa_nws=true
```

Alert evaluation endpoint:

```text
POST /api/v1/alerts/evaluate?use_noaa_nws=true
```

Relevant NOAA/NWS alerts can increase the warning score and influence alert generation. This is weather-alert context, not attack prediction.

## Caching

NOAA/NWS responses are cached in process for a short TTL by rounded coordinate so repeated identical requests do not hammer the provider.

## Provider Health

Successful U.S. requests write:

- `provider_runs`
- `provider_health.status="healthy"`
- `last_success`
- `records_ingested`

Outside-U.S. requests write:

- `provider_runs.status="not_applicable"`
- `provider_health.status="not_applicable"`

Failed requests write:

- `provider_failures`
- `provider_health.status="degraded"`
- `last_error`

Provider failures must not crash public warning or alert-evaluation routes, and exception details must not leak into public API responses.
