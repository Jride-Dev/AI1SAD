# Hawaii Tide And Current Provider

AI1SAD includes a static/offline Hawaii tide and nearshore water-movement adapter for bounded operational context. It does not make live PacIOOS or NOAA CO-OPS calls at runtime.

Provider module: `app/providers/hawaii_tide_current.py`

## Purpose

Represent baseline water-movement context for surveillance planning:

- tide state context
- tide-window context
- nearshore current direction context
- nearshore current speed context
- channel-flow context
- tidal-exchange context

These are static baseline profiles, not live ocean observations.

## Source Direction

Preferred Hawaii-first source order:

1. PacIOOS South Shore Oahu ROMS
2. PacIOOS Oahu ROMS
3. PacIOOS Main Hawaiian Islands ROMS
4. NOAA CO-OPS supporting tide/current station data

The adapter stores this source order as metadata so future ingestion can replace static baselines with source-dated live or pre-fetched records.

## Signal Types

- `tide_state_context`
- `tide_window_context`
- `nearshore_current_context`
- `current_direction_context`
- `current_speed_context`
- `channel_flow_context`
- `tidal_exchange_context`

## Explainability Factors

When active, public explanations can surface:

- `tide_state_context`
- `channel_flow_context`
- `current_speed_context`
- `current_convergence_context`
- `nearshore_model_resolution`
- `forecast_freshness`
- `station_coverage_gap`
- `regional_fallback_used`

Resolution, freshness, coverage-gap, convergence, and fallback fields are metadata/explainability context. They do not turn static profiles into live observations.

## Bounded Behavior

- Tide/current context alone must not create high warning.
- Channel-flow context may modestly raise surveillance attention.
- Stronger operational attention requires stacked activity, sightings, biological events, SST, weather, or exposure context.
- Static water-movement baselines reduce confidence because they are not live conditions.
- Cromwell's Beach remains a regression case, not a tuning target.

## Operational Caveat

Static PacIOOS/NOAA source metadata is an implementation guide and baseline context only. Operators should confirm live tide/current conditions through official sources before field decisions.
