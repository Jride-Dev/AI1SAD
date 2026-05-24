# Human Exposure Provider

Phase 9D adds a controlled human-exposure adapter for crowded beaches, weekends, holidays, tourist seasons, parking pressure, and regional beach-use patterns.

This provider is static/offline first. It does not scrape live websites and does not use paid crowd APIs.

## Signal Types

- `human_exposure`
- `beach_crowd_pressure`
- `parking_pressure`
- `tourism_season`
- `weekend_exposure`
- `holiday_exposure`
- `event_exposure`

## Static Profiles

Initial profiles:

- Clearwater Beach
- South Beach Miami
- Daytona Beach
- New Smyrna Beach
- Virginia Beach
- Rehoboth Beach
- Hampton Beach
- Hurghada
- Sharm El-Sheikh
- Rottnest Island

Each profile includes:

- baseline exposure level
- peak season months
- weekend multiplier
- holiday multiplier
- parking/crowd notes
- `source_notes`
- confidence
- pack association

## Model Behavior

Human exposure is an opportunity/exposure signal, not shark presence.

Exposure alone must not create high warning states. It can amplify warning or surveillance context when paired with other signals such as:

- rainfall/runoff
- SST suitability
- shark sightings
- activity hazard
- species seasonal overlap

The warning engine uses a bounded `human_exposure_amplifier` factor only when another relevant context is active.

The surveillance engine uses exposure to prioritize communication, lookout, patrol, or drone coverage only when paired with sightings, activity context, recent interactions, or environmental signals.

The alert engine can include exposure context in a surveillance-priority alert, but crowding alone is not treated as a shark warning.

## Freshness

Static exposure signals are short-lived Signal records with `data_freshness`. Stale exposure signals lower confidence through provider freshness status.

## Future Work

Future live integrations should be reviewed before use. Potential sources might include official beach attendance, parking, event calendars, or tourism reports, but no scraping or paid APIs are enabled in Phase 9D.
