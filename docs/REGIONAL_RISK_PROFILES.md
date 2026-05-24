# Regional Shark Encounter Warning Profiles

Phase 3A adds regional warning profiles so the risk model does not rely on one global summer calendar.

Each profile includes:

- Local summer/high-exposure months
- Known high-attention months
- Dominant species
- Species weights
- Species-specific risk factors
- Environmental multipliers
- Human exposure multipliers
- Warning cache TTL
- Notes and citations fields

## Seeded Profiles

| Region | Local High-Exposure Months | High-Attention Months | Special Handling |
| --- | --- | --- | --- |
| Florida | May-Sep | Mar, Apr, Oct | Weekend and non-summer tourist/beach exposure multipliers |
| Hawaii | May-Sep | Oct | October Sharktober multiplier |
| New South Wales, Australia | Dec-Feb | Jan-Mar | Southern Hemisphere summer; Jan-Feb high-exposure handling |
| Western Australia | Dec-Feb | Jan-Mar | Southern Hemisphere summer; Jan-Feb high-exposure handling |
| California | Jun-Sep | Aug-Oct | Late-summer/fall white-shark attention period |
| South Africa | Dec-Feb | Dec-Feb | Southern Hemisphere summer profile |
| Red Sea | May-Sep | Jun-Oct | Oceanic whitetip anomalies, feeding-event sensitivity, and shipping influence |

## Regional Species Engine

Profiles include species weights and species/environment trigger notes. This keeps Florida bull/blacktip/spinner logic separate from Hawaii tiger shark logic, NSW bull/whaler/white shark logic, South Africa white/bronze whaler logic, and Red Sea oceanic whitetip sensitivity.

The current model remains deterministic and explainable. Species weights are profile data used for explanations and future factor weighting; they are not an ML classifier and should not be read as individual-attack probabilities.

## Cache TTL

Warning snapshots are cached by region with `warning_cache_ttl_minutes`. Fast-changing regions can use 30-minute cache windows, while broader/default regions can use 45-60 minute windows. Cached responses are public warning payloads only and still carry disclaimers, confidence, dominant factors, and missing/stale data indicators.

## How Profiles Are Applied

`GET /api/v1/risk/location` finds the nearest public profile by profile center coordinates. The base rule score is calculated first, then regional multipliers adjust the warning score.

Returned fields:

- `score`: base score
- `band`: base score band
- `warning_score`: regional-adjusted score
- `warning_band`: regional-adjusted band
- `confidence`: first-pass confidence value
- `regional_profile`: public profile summary
- `dominant_contributing_factors`: largest contributions after regional adjustment

## Safety Note

Regional warning profiles estimate encounter conditions only. They do not predict attacks and should not override official beach, lifeguard, weather, wildlife, or emergency guidance.
