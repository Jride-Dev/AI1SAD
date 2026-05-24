# Open-Meteo Provider

Phase 9A activates Open-Meteo as the first live weather provider for AI1SAD.

Open-Meteo is used for recent hourly weather lookback only. It does not require an API key for the current integration, and no paid provider config is committed.

## Data Fetched

For a requested latitude/longitude and lookback window, AI1SAD requests hourly:

- `rain`
- `temperature_2m`
- `wind_speed_10m`

The provider normalizes:

- `rainfall_24h_mm`
- `rainfall_48h_mm`
- `rainfall_72h_mm`
- `temperature_c`
- `wind_speed_kmh`
- `provider_timestamp`

## Signal Normalization

Open-Meteo output is normalized through the signal broker into public Signal-shaped documents:

- `weather_rainfall`
- `weather_temperature`
- `weather_wind_speed`

The rainfall signal carries `value=rainfall_72h_mm` and also includes the 24/48/72-hour rainfall totals.

## API Usage

Warning endpoint:

```text
GET /api/v1/warnings/location?lat=27.7&lon=-80.2&use_open_meteo=true
```

Alert evaluation endpoint:

```text
POST /api/v1/alerts/evaluate?use_open_meteo=true
```

When enabled, live rainfall can increase the warning score used by alert evaluation. This remains an environmental warning score, not attack probability.

## Caching

Open-Meteo responses are cached in process for a short TTL so repeated calls for the same rounded coordinate/lookback window do not hammer the provider.

The API warning snapshot cache still applies separately unless `bypass_cache=true` is used.

## Provider Health

Successful requests write:

- `provider_runs`
- `provider_health.status="healthy"`
- `last_success`
- `records_ingested`

Failed requests write:

- `provider_failures`
- `provider_health.status="degraded"`
- `last_error`

Provider failures must not crash public warning or alert routes. Confidence is reduced or missing/stale provider information is returned.
