# Alert Engine

AI1SAD estimates environmental and surveillance-relevant shark encounter conditions. It does not predict individual attacks or guarantee safety outcomes.

The alert engine converts three deterministic scores into operator-facing alerts:

- `warning_score`: environmental/live-condition warning.
- `surveillance_priority_score`: where drone, lookout, or patrol teams should look first.
- `activity_hazard_score`: hazard introduced by the human activity context.

The engine is intentionally rule based. It should remain explainable before any statistical or machine-learning layer is added.

## Alert Creation Rules

High `surveillance_priority_score` can create an alert even when `warning_score` is low. This is the Horseshoe Reef pattern: low general environmental warning, high search priority because spearfishing, reef habitat, and regional white shark suitability stack together.

High `activity_hazard_score` creates activity-specific alerts for contexts such as spearfishing, diving with catch, fishing near reef/dropoff, or swimming near bait activity.

Recent sightings, carcasses, biological events, and incidents create time-limited alerts. Expired public signals are ignored. Private/internal signals are ignored for public alert output.

Stale data reduces confidence. If all available freshness inputs are stale or expired, the engine suppresses newly generated alerts rather than pretending current conditions are known.

Quiet-day baselines suppress weak alerts when scores do not rise meaningfully above background conditions.

## Required Public Alert Fields

Each public alert includes:

- `title`
- `summary`
- `location` and `zone`
- `recommended_action`
- `dominant_factors`
- `confidence`
- `expires_at`
- `data_freshness`
- `disclaimer`

Private notes, restricted records, raw provider secrets, victim names, and internal analyst fields must not be exposed.

## Examples

### Horseshoe Reef

Low `warning_score`, high `surveillance_priority_score`. The alert level can be `urgent_surveillance` because the operational question is where safety teams should look first, not whether AI1SAD predicts an attack.

### Florida Inlet Rainfall

Rainfall/runoff, inlet proximity, crowded beach exposure, fishing/surf activity, and regional bull/blacktip context can produce a `general_warning` or `surveillance_priority` alert depending on the score split.

### Hawaii October

Hawaii October tiger shark regional seasonality can elevate a watch-level alert when combined with human exposure, sightings, or biological signals.

### Red Sea Carcass/Shipping Anomaly

A public carcass or biological event signal near shipping/tourism activity can create a biological-event advisory. Confidence should reflect source quality and freshness.
