# Hawaii Water Clarity Provider

AI1SAD includes a static/offline Hawaii water-clarity and turbidity adapter for bounded visibility context. It does not make live NOAA, PacIOOS, beach water-quality, camera, or scraping calls at runtime.

Provider module: `app/providers/hawaii_water_clarity.py`

## Purpose

Represent baseline visibility context for surveillance planning:

- water clarity context
- turbidity context
- sediment/runoff visibility context
- surf-zone visibility context

These are static baseline profiles, not live water-quality, turbidity, ocean-color, or beach observations.

## Source Direction

Preferred Hawaii-first source candidates:

1. NOAA CoastWatch / ocean-color products where applicable
2. PacIOOS water-quality or visibility-relevant products where available
3. Hawaii beach water-quality or turbidity datasets where policy and redistribution terms allow
4. Static reef-channel and runoff visibility notes from reviewed baseline packs

The adapter stores these source candidates as metadata so future ingestion can replace static baselines with source-dated pre-fetched records.

## Static Profiles

Phase 24 adds Oahu-focused static profiles:

- Cromwell's Beach / Diamond Head visibility baseline
- Waikiki / Ala Moana visibility baseline
- Oahu sandy-bottom clearer quiet-day visibility baseline

Each profile includes region, island, location name, coordinates, clarity class, turbidity class, runoff visibility context, surf-zone visibility context, source metadata, source date, baseline-only metadata, pack association, confidence, and public/private visibility.

## Signal Types

- `water_clarity_context`
- `turbidity_context`
- `sediment_runoff_visibility_context`
- `surf_zone_visibility_context`

## Explainability Factors

When active, public explanations can surface:

- `water_clarity_context`
- `turbidity_context`
- `sediment_runoff_visibility_context`
- `surf_zone_visibility_context`
- `visibility_activity_stack_context`
- `visibility_signal_stack_context`
- `baseline_visibility_freshness`
- `hawaii_water_clarity_baseline_context`

These factors are bounded visibility context and must not be described as live observations unless a future adapter ingests source-timestamped records.

## Bounded Behavior

- Water clarity or turbidity context alone must not create high warning.
- Reduced visibility may lower confidence or raise surveillance attention modestly.
- Stronger operational attention requires stacked activity, sightings, biological events, SST, weather, or exposure context.
- Static visibility baselines reduce confidence because they are not live conditions.
- Cromwell's Beach remains a regression case, not a tuning target.

## Operational Caveat

Static clarity/turbidity source metadata is an implementation guide and baseline context only. Operators should confirm live water quality, runoff, and visibility conditions through official sources before field decisions.
