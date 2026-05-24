# Regional Packs

Regional packs make AI1SAD modular. Core remains available everywhere, while optional regional packs add higher-resolution species, seasonality, environmental, surveillance, alert, and replay context.

Regional packs are not hard billing enforcement in this phase. They are a soft entitlement layer used to show which regional intelligence is active and when a higher-resolution pack exists.

## Initial Packs

- `core`: global baseline warning, surveillance, replay, and alert behavior.
- `florida`: bull/blacktip/spinner context, inlet/runoff rules, weekend and beach exposure handling.
- `hawaii`: tiger shark and October/Sharktober context.
- `western_australia`: white shark, reef/dropoff, spearfishing/diving context, Horseshoe Reef replay support.
- `new_south_wales`: bull/whaler/white shark context with Southern Hemisphere summer and river-mouth/runoff rules.
- `south_africa`: white shark and bronze whaler context with seal-colony/surf replay support.
- `red_sea`: oceanic whitetip anomalies, carcass/feeding-event sensitivity, shipping/tourism event intelligence.
- `us_east_coast`: nearshore baitfish, summer exposure, beach/surf/fishing context.

Phase 9D adds static human-exposure profiles that can be associated with regional packs:

- Florida pack: Clearwater Beach, South Beach Miami, Daytona Beach, New Smyrna Beach.
- U.S. East Coast pack: Virginia Beach, Rehoboth Beach, Hampton Beach.
- Red Sea pack: Hurghada, Sharm El-Sheikh.
- Western Australia pack: Rottnest Island.

These profiles are controlled static signals, not live scraped crowd estimates.

## Pack Metadata

Each pack defines:

- covered regions
- dominant species
- seasonal windows
- environmental signals
- human exposure signals
- surveillance rules
- alert rules
- replay scenarios
- docs links
- required access tier

## Response Fields

Warning, surveillance, replay, and alert-evaluation responses include:

- `active_pack`: the pack currently applied.
- `pack_features_used`: feature keys from the active pack.
- `pack_notice`: present when Core is active but a higher-resolution regional pack is available.
- `available_pack`: present when the location matches a regional pack.

Core functionality is not blocked when a regional pack is unavailable or not enabled.

## API

- `GET /api/v1/packs`
- `GET /api/v1/packs/{pack_id}`
- `GET /api/v1/packs/{pack_id}/species`
- `GET /api/v1/packs/{pack_id}/signals`
- `GET /api/v1/packs/{pack_id}/replays`
- `GET /api/v1/access/entitlements`
