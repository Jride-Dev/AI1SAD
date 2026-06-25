# Biological Events Provider

Phase 9E adds a controlled biological/ecological event provider. It is static/manual/offline first. It does not scrape news, social media, agency feeds, or paid APIs.

## Signal Types

- `biological_event`
- `carcass`
- `whale_carcass`
- `seal_presence`
- `sea_lion_presence`
- `sea_turtle_nesting`
- `sea_turtle_migration`
- `baitfish_presence`
- `fish_kill`
- `seabird_hatchling_event`

## Static Examples

Initial examples are intentionally small and reviewed:

- Hawaii turtle-season / tiger shark context
- Florida baitfish / blacktip overlap context
- South Africa seal colony / white shark context
- Red Sea carcass or dumping anomaly context
- Western Australia reef/prey context

These records are examples of normalized event context, not claims of live animal presence.

## Normalized Signal Shape

`app/providers/biological_events.py` emits Signal-shaped records through the signal broker:

```json
{
  "signal_type": "carcass",
  "event_type": "carcass",
  "species": "oceanic whitetip shark",
  "location": {"geo": {"type": "Point", "coordinates": [38.5, 20.5]}},
  "timestamp": "2026-05-24T12:00:00Z",
  "expires_at": "2026-05-27T12:00:00Z",
  "confidence": 0.7,
  "source": {
    "provider": "biological_events_static",
    "dataset": "static_manual_biological_events"
  },
  "risk_relevance": {
    "score": 0.855,
    "factors": ["carcass", "feeding_event_sensitivity", "nearshore_attractant"]
  },
  "visibility": "public",
  "value": 0.9,
  "units": "index",
  "data_freshness": {"status": "fresh"}
}
```

Provider-specific fields such as `event_id`, `event_name`, `event_impact`, `pack_id`, `source_notes`, and `distance_km` are added for auditability.

## Expiration And Decay

High-impact attractant events use shorter windows:

- carcass, whale carcass, fish kill: 72 hours by default
- baitfish or seabird hatchling event: 96 hours by default
- turtle nesting/migration, seal, or sea-lion context: 720 hours by default
- generic biological event: 168 hours by default

Expired events are excluded from active public signal inputs. Replay decay remains deterministic and type-specific.

Warning scoring evaluates biological-event freshness against the current wall-clock time by default. Strict replay callers pass the scenario timestamp as the evaluation time so historical carcass fixtures do not drift as the calendar advances. This does not extend stale biological events, change scoring weights, move fixture dates, or refresh replay artifacts.

## Scoring Rules

Biological event signals are bounded.

Generic migration, nesting, or prey context acts as low-to-moderate supporting context. It should not create extreme warnings by itself.

High-confidence nearshore carcass or fish-kill events carry stronger warning and surveillance influence, but still remain explainable and time-limited.

Surveillance priority treats carcass and fish-kill signals as stronger operational search context than broad seasonal migration context.

## Privacy And Safety

Only public biological signals should enter public APIs. Private notes, restricted-source details, unreviewed reports, and precise sensitive ecology data must remain private.

AI1SAD estimates environmental and surveillance-relevant shark encounter conditions. It does not predict individual attacks or guarantee safety outcomes.
