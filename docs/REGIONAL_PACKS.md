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

Phase 9E adds static/manual biological-event examples associated with regional packs:

- Hawaii pack: turtle-season / tiger shark context.
- Florida pack: baitfish / blacktip overlap context.
- South Africa pack: seal colony / white shark context.
- Red Sea pack: carcass or dumping anomaly context.
- Western Australia pack: reef/prey context.

These biological signals are controlled offline examples and reviewed manual inputs. They are not live animal detections or scraped reports.

Phase 9F adds static/manual vessel and fishing examples associated with regional packs:

- Florida pack: piers, inlets, and recreational fishing context.
- Western Australia pack: reef and spearfishing context.
- Red Sea pack: liveaboard, dive boat, and tourism corridor context.
- South Africa pack: fishing and seal-colony coastline context.
- Hawaii pack: nearshore recreational fishing context.

These vessel/fishing signals are controlled offline examples. They are not live AIS, MarineTraffic, Global Fishing Watch, or harbor-camera detections.

Phase 20 adds static/manual kelp forest habitat examples associated with regional packs:

- Central California / U.S. East Coast-style demo pack context: kelp edge, pinniped prey association, surfing/diving overlap.
- Monterey Bay / Central Coast demo context: moderate kelp and nearshore recreation overlap.
- South Africa pack: False Bay / Seal Island kelp-edge and pinniped context.
- Western Australia pack: sparse reef/kelp context near reef and spearfishing workflows.
- Core pack: a clearly synthetic golden-rule kelp bed profile for bounded QA.

These kelp signals are controlled offline habitat examples. They are not live canopy detections, animal detections, satellite feeds, or scraped map layers.

Phase 22 adds static/manual Hawaii habitat baseline examples associated with the Hawaii pack:

- Cromwell's Beach / Diamond Head nearshore baseline context
- Kaikoo / Hale Mano channel baseline context
- Waikiki / Ala Moana south-shore baseline context
- Oahu reef-channel demo baseline context
- Oahu shallow-reef edge demo baseline context
- Oahu sandy-bottom quiet-day baseline context

These Hawaii habitat signals are historic/static structural baselines. They are not live observations and must be interpreted as bounded context only.

## Hawaii Pack Coverage Gaps

The Cromwell's Beach replay analysis shows that Hawaii operational awareness is currently limited most by early observational ingestion gaps and missing ocean-state layers, not by pack-weight tuning.

High-value next additions for the Hawaii pack:

- finer reef-channel habitat mapping
- tide/current context adapter
- turbidity/clarity context adapter
- local live sightings/lifeguard signal ingestion
- time-sliced human exposure timing profiles

Reference: [Hawaii Signal Gap Analysis](HAWAII_SIGNAL_GAP_ANALYSIS.md).

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
