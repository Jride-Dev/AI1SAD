# Surveillance Prioritization Engine

Phase 4 adds a deterministic drone/search-zone prioritization engine for coastal safety planning.

AI1SAD does not predict individual shark attacks. This layer ranks zones where a safety team may choose to focus drone, lookout, patrol, or follow-up search effort based on public recent interactions, verified sightings, habitat features, environmental warning signals, regional species profiles, and human activity context.

## What It Does

The engine accepts a mission location, radius, mission type, lookback window, optional activity context, optional suspected species, month, and river-mouth distance. It returns prioritized zones with:

- `zone_id`
- `priority_score`
- `priority_band`
- `center`
- `radius_km`
- optional `polygon`
- `recommended_pattern`
- `dominant_factors`
- `confidence`
- `data_sources_used`
- `disclaimer`

Every dominant factor includes points, rationale, and contribution so the score can be audited.

## Score Split

AI1SAD keeps these outputs separate:

- `warning_score`: environmental/live-condition risk from weather, ocean, biological, vessel, and exposure signals.
- `surveillance_priority_score`: where safety or drone teams should look first.
- `activity_hazard_score`: risk introduced by what the human is doing in context.

The surveillance engine can return a high `surveillance_priority_score` because activity and habitat make a zone important to search, while `warning_score` remains low because live environmental signals are absent or quiet.

Do not call these attack probability.

## First-Pass Factors

- Recent fatal/nonfatal public interaction nearby
- Verified public shark sightings nearby
- Reef, dropoff, channel, or habitat feature proximity
- River-mouth/runoff proximity where regionally relevant
- Activity context such as swimming, surfing, spearfishing, diving, or fishing
- Regional species suitability
- Current weather/ocean warning signals
- Human exposure level

## Regional Species Behavior

The engine uses nearest public `regional_risk_profiles` and deterministic region rules:

- Western Australia: white shark, reef/dropoff, spearfishing, and diving context can increase reef-zone priority.
- New South Wales: bull shark, river-mouth, and runoff context receive stronger river-zone weighting.
- Hawaii: tiger shark October/Sharktober context increases attention.
- Florida: blacktip/bull shark surf, fishing, river-mouth, and runoff context increase priority.

These rules prioritize search effort. They do not claim shark intent or individual animal behavior.

## Spearfishing Context

Spearfishing is treated as activity context because it affects search geometry and environmental overlap. It must not be labeled automatic provocation. Public responses should describe the activity neutrally.

For Western Australia, spearfishing plus reef/dropoff habitat plus known or suspected white shark suitability strongly increases `activity_hazard_score` and `surveillance_priority_score`. The environmental `warning_score` remains tied to live environmental/current-condition signals.

## Confidence And Uncertainty

Confidence decreases when important public data sources are absent or stale. Missing recent interactions, sighting reports, reef features, regional profiles, or current warning signals should reduce confidence rather than silently assuming normal conditions.

Confidence is not a measure that an attack will occur. It is a model-quality signal for how complete and timely the public inputs are.

## Privacy

Public surveillance endpoints filter by `visibility="public"` and exclude private notes, restricted records, raw source notes, exact addresses, credentials, and sensitive source content.

Admin interaction and sighting endpoints are disabled by default and should only be enabled in trusted deployments with reviewed ingestion controls.
