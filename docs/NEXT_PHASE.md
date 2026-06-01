# Next Phase

## Phase 23: Tide, Current & Nearshore Water-Movement Adapter

## Objective

Add bounded, static/offline-first tide and nearshore water-movement context so AI1SAD can improve operational surveillance interpretation without changing scoring weights to fit one incident.

Hawaii-first direction:

- prioritize Oahu and south-shore Hawaii operational context first
- keep Cromwell's as one regression case only, not a weight-tuning target

## Constraints

- Do not tune scoring weights
- Do not add attack-probability language
- Do not infer shark intent
- Do not add live scraping
- Do not change auth/billing
- Do not commit until review

## Planned Scope

1. Add tide/current provider adapter (static/offline profiles first)
2. Add signal types for:
   - tide state/window context
   - nearshore current direction/speed context
   - channel flow context
3. Keep contributions bounded and stack-dependent
4. Add explainability factors and confidence freshness caveats
5. Add focused tests and replay regression checks
6. Update provider and regional-pack docs

## Official/Public Source Candidates

- PacIOOS South Shore Oahu ROMS
- PacIOOS Oahu ROMS
- PacIOOS Main Hawaiian Islands ROMS
- NOAA CO-OPS

All source integration should begin as static/offline baseline ingestion first, with source dates and freshness caveats retained.

## Bounded Behavior Rules

- Tide/current context alone must not create high warning.
- Channel-flow context may modestly raise surveillance attention.
- Stronger effects require stacked activity, sightings, prey, SST, weather, or exposure signals.
- Historic/static current layers must be labeled as baseline context, not live operational conditions.
- No scoring-weight tuning around Cromwell's or any single case.

## Recommended Execution Order

1. Provider schema and static profiles
2. Signal broker integration
3. Warning/surveillance bounded context wiring
4. Alert/explainability updates
5. Replay scenario integration (timeline-safe)
6. Tests and docs
7. Validation sweep

## Validation Expectations

- focused tide/current adapter tests
- focused Cromwell timeline-regression tests
- full backend test suite
- mkdocs build
- secret scan
- prohibited-language scan

Frontend tests/build can remain skipped if frontend files are unchanged.

## Review Gate

Do not commit until review.
