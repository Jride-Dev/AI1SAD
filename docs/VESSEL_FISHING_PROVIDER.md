# Vessel And Fishing Provider

Phase 9F adds a controlled vessel, fishing, pier, marina, reef-fishing, spearfishing, and boating-pressure provider.

The provider is static/manual/offline first. It does not call Global Fishing Watch, AIS, MarineTraffic, harbor cameras, social media, or paid vessel/crowd APIs.

## Signal Types

- `vessel_activity`
- `fishing_activity`
- `commercial_fishing_pressure`
- `recreational_fishing_pressure`
- `spearfishing_activity`
- `pier_fishing_pressure`
- `marina_boat_pressure`
- `dive_boat_activity`
- `liveaboard_activity`

## Static Examples

Initial examples are intentionally small and regional:

- Florida piers, inlets, and recreational fishing context
- Western Australia reef and spearfishing context
- Red Sea liveaboard, dive boat, and tourism corridor context
- South Africa fishing and seal-colony coastline context
- Hawaii nearshore recreational fishing context

These records are operational context signals, not live vessel detections.

## Normalized Signal Shape

`app/providers/vessel_fishing.py` emits Signal-shaped records through the signal broker:

```json
{
  "signal_type": "spearfishing_activity",
  "activity_type": "spearfishing_activity",
  "location": {"geo": {"type": "Point", "coordinates": [115.515, -31.983]}},
  "timestamp": "2026-05-24T12:00:00Z",
  "expires_at": "2026-05-25T12:00:00Z",
  "confidence": 0.62,
  "source": {
    "provider": "vessel_fishing_static",
    "dataset": "static_manual_vessel_fishing_signals"
  },
  "risk_relevance": {
    "score": 0.852,
    "factors": ["spearfishing_activity", "reef_fishing_context", "white_shark_search_context"]
  },
  "visibility": "public",
  "value": 0.88,
  "units": "index",
  "data_freshness": {"status": "fresh"},
  "pack_id": "western_australia"
}
```

Provider-specific fields include `signal_id`, `signal_name`, `duration_hours`, `distance_km`, `source_notes`, and `pack_id`.

## Expiration And Decay

- Active fishing, spearfishing, commercial fishing, and recreational fishing: short high-impact window, usually 24 hours.
- Dive boat, liveaboard, and general vessel activity: medium context window, usually 72 hours.
- Pier and marina baseline pressure: longer lower-impact context, usually 168 hours.

Replay decay includes explicit vessel/fishing signal types. Active spearfishing decays faster than pier or marina baseline context.

## Scoring Rules

Vessel and fishing signals are bounded.

General `warning_score` receives only a capped vessel/fishing contribution. Vessel activity alone should not create high warning states.

Fishing and spearfishing primarily affect:

- `activity_hazard_score`
- `surveillance_priority_score`
- alert routing for drone, lookout, patrol, and beach-management review

Fishing plus biological event context plus human exposure can strongly raise surveillance priority because it changes where safety teams should look first.

## Privacy And Safety

Only public vessel/fishing signals should enter public APIs. Private marina notes, unreviewed reports, exact sensitive operational locations, restricted vessel sources, and raw provider payloads must remain private.

AI1SAD estimates environmental and surveillance-relevant shark encounter conditions. It does not predict individual attacks or guarantee safety outcomes.
