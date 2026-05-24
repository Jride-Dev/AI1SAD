# Environmental Risk Signals

Phase 3 adds a first-pass Shark Encounter Risk score. This is encounter-risk estimation, not attack prediction.

The score summarizes environmental conditions that may increase the chance of overlap among sharks, prey, and people. It is not a safety guarantee, beach closure recommendation, or substitute for local lifeguard, weather, wildlife, or emergency guidance.

AI1SAD intentionally starts with deterministic, explainable rules. The order is:

1. Deterministic and explainable warning model.
2. Bayesian/statistical layer after source freshness and validation are stable.
3. ML ensemble only after the public data contracts, labels, uncertainty, and review process are mature.

## Risk Bands

| Score | Band |
| --- | --- |
| 0 to 24.99 | low |
| 25 to 49.99 | moderate |
| 50 to 74.99 | elevated |
| 75 to 100 | high |

## Rule-Based Factors

| Factor | Max Points | Current Rule |
| --- | ---: | --- |
| Historical incident density | 20 | Scales from 0 to 20 based on nearby public incident count, capped at 20 incidents. |
| Recent rainfall/runoff | 15 | 10+ mm adds 5, 25+ mm adds 10, 50+ mm adds 15. |
| River mouth distance | 15 | <=1 km adds 15, <=5 km adds 10, <=10 km adds 5. |
| Sea surface temperature / seasonal suitability | 10 | 20-28 C adds 10; shoulder temperatures add 5; seasonal months can add a small boost. |
| Fishing activity | 10 | User/provider signal from 0 to 1 scaled to 10 points. |
| Baitfish / prey indicator | 10 | User/provider signal from 0 to 1 scaled to 10 points. |
| Water visibility | 10 | <1 m adds 10, <3 m adds 6, <5 m adds 3. |
| Human water activity | 10 | User/provider signal from 0 to 1 scaled to 10 points. |

## Regional Profiles

Phase 3A adds `regional_risk_profiles`. The API detects the nearest public regional profile and applies region-specific calendars and multipliers to produce:

- `score`: base environmental rule score
- `band`: base score band
- `warning_score`: regional-profile-adjusted warning score
- `warning_band`: adjusted warning band
- `confidence`: first-pass confidence value based on whether a regional profile matched
- `dominant_contributing_factors`: largest factor contributions after regional adjustment

Current-condition warning responses also return `dominant_factors`, where every factor includes a numeric `contribution` value. Missing or stale provider data is listed in `missing_data_sources` and reduces `confidence`; it is never silently treated as normal.

Seeded profiles:

- Florida
- Hawaii
- New South Wales, Australia
- Western Australia
- California
- South Africa
- Red Sea

The model does not use one global summer definition. Local summer/high-exposure months are stored per profile.

Special handling:

- Hawaii: October applies a Sharktober multiplier.
- New South Wales and Western Australia: January-February apply Southern Hemisphere high-exposure/high-attention handling.
- Florida: weekend exposure and non-summer tourist/beach exposure can increase the human-exposure warning score.

## Assumptions

- Historical incident density is a coarse proxy for overlap among sharks, humans, habitat, and reporting.
- Rainfall is treated as a runoff and water-clarity proxy until direct runoff/turbidity feeds are added.
- River mouths, inlets, estuaries, and outflows may concentrate nutrients, prey, turbidity, and predator movement.
- Sea surface temperature is only a coarse seasonal suitability signal.
- Fishing and baitfish indicators are treated as local attractant/prey signals.
- Human water activity changes encounter opportunity, not shark behavior by itself.
- Regional profiles are coarse public-warning profiles; they should be refined with local expert review and official regional data.

## Limitations

- This model does not predict attacks.
- It does not know whether beaches are open, guarded, or under local warning.
- It does not include real-time shark tracking, drone sightings, lifeguard reports, or official advisories yet.
- It depends on the quality of supplied environmental signals.
- Historical incident data has reporting bias and does not measure exposure-adjusted risk.

## Future Data Sources

Potential future inputs:

- NOAA sea surface temperature and coastal observations
- Rainfall and river discharge feeds
- Turbidity, water clarity, and sediment plume products
- Tide, moon, swell, and wind data
- Fishing pier, boat ramp, and fishing-pressure proxies
- Baitfish reports, bird-feeding observations, and ecological surveys
- Lifeguard advisories and beach closure feeds
- Local official shark sighting reports

External provider API keys and config must stay in `.env` or deployment secrets only.
