# Alert Levels

AI1SAD estimates environmental and surveillance-relevant shark encounter conditions. It does not predict individual attacks or guarantee safety outcomes.

Alert levels are operational labels for review, monitoring, and communication. They are not attack-probability categories.

## Levels

`advisory`

Conditions deserve awareness, but the signal is limited, uncertain, or event-specific.

`watch`

Conditions support increased attention by lifeguards, beach managers, drone teams, researchers, or API users.

`warning`

Environmental/live-condition signals are elevated enough to support active operational review.

`urgent_surveillance`

Search-zone priority is high enough that drone, lookout, or patrol teams should consider prioritizing the area even if the general environmental warning is low.

## Alert Types

- `general_warning`: environmental/live-condition warning score is elevated above baseline.
- `surveillance_priority`: search-zone priority is high for safety teams.
- `activity_hazard`: human activity context increases encounter hazard.
- `biological_event`: carcass, prey, stranding, fish kill, or related biological signal is active.
- `sighting_cluster`: multiple recent public sightings are active near the area.
- `post_incident_surveillance`: a recent interaction supports time-limited post-incident monitoring.

## Confidence

Confidence is lowered when data sources are stale, missing, conflicting, or low quality. Alerts should expire rather than silently assume old data is still current.
