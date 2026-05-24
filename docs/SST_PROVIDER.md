# SST Provider Adapter

Phase 9C prepares AI1SAD for sea-surface temperature and SST anomaly data without committing to a brittle live ocean provider.

The current adapter is offline/test-first. It accepts mocked or pre-fetched SST records and normalizes them into Signal-shaped records. Live NOAA ERDDAP networking is intentionally not enabled yet.

## Signal Types

- `sea_surface_temperature`
- `sst_anomaly`
- `ocean_temperature_context`

## Normalized Fields

Signals include:

- `temperature_c`
- `anomaly_c`
- `timestamp`
- `provider_timestamp`
- `location`
- `confidence`
- `data_freshness`
- `source.provider="noaa_coastwatch"`
- `source.dataset`
- `risk_relevance`
- `visibility="public"`

## Regional Weighting

SST context is weighted as supporting context, not a standalone warning trigger.

- Florida: warm nearshore SST supports blacktip/bull shark context.
- Western Australia: temperate SST supports white shark context.
- Hawaii: warm tropical SST supports tiger shark context.
- Red Sea: warm-water context supports regional oceanic/tiger shark context.

The SST context can influence:

- `warning_score`
- surveillance-priority context
- alert evaluation when SST supports an already elevated surveillance context

It must not be described as attack probability.

## Missing Or Stale Data

Missing SST data does not crash the API. It contributes to missing ocean freshness and lowers confidence through existing freshness rules.

Stale SST signals are marked stale by the signal broker and lower confidence through provider status such as `noaa_coastwatch:stale`.

## Future Live Interface

The live NOAA CoastWatch/ERDDAP interface should only be enabled after dataset IDs, spatial windows, time windows, rate limits, and terms of use are reviewed. Tests should remain mocked.
