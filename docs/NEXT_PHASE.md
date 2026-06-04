# Next Phase

## Phase 24: Water Clarity & Turbidity Adapter

## Objective

Add bounded, static/offline-first water clarity and turbidity context so AI1SAD can improve visibility and confidence interpretation without changing scoring weights to fit one incident.

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

## Phase 23 Completion Note

Phase 23 added static/offline Hawaii tide/current baseline support:

- PacIOOS South Shore Oahu ROMS as preferred future nearshore source metadata
- PacIOOS Oahu ROMS fallback metadata
- PacIOOS Main Hawaiian Islands ROMS fallback metadata
- NOAA CO-OPS supporting station metadata
- bounded warning/surveillance/explainability/alert/replay integration
- Cromwell replay regression coverage

Live PacIOOS/NOAA ingestion is still future work.

## Planned Scope

1. Add water clarity/turbidity provider adapter (static/offline profiles first)
2. Add signal types for:
   - water clarity context
   - turbidity context
   - sediment/runoff visibility context
   - surf-zone visibility context
3. Keep contributions bounded and stack-dependent
4. Add explainability factors and confidence freshness caveats
5. Add focused tests and replay regression checks
6. Update provider and regional-pack docs

## Official/Public Source Candidates

- NOAA CoastWatch / ocean color products where applicable
- PacIOOS water-quality or visibility-relevant products where available
- Hawaii beach water-quality or turbidity datasets where policy/terms allow
- Static reef-channel and runoff visibility notes from existing baseline packs

All source integration should begin as static/offline baseline ingestion first, with source dates and freshness caveats retained.

## Bounded Behavior Rules

- Turbidity/clarity context alone must not create high warning.
- Reduced visibility may lower confidence or raise surveillance attention modestly.
- Stronger effects require stacked activity, sightings, prey, SST, weather, or exposure signals.
- Historic/static clarity layers must be labeled as baseline context, not live operational conditions.
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

- focused water clarity/turbidity adapter tests
- focused Cromwell timeline-regression tests
- full backend test suite
- mkdocs build
- secret scan
- prohibited-language scan

Frontend tests/build can remain skipped if frontend files are unchanged.

## Review Gate

Do not commit until review.

## Current Interruption Note

Phase 23 is reviewed, committed, and pushed. A Greater Recife paired replay case study is currently in review and should be completed before Phase 24 begins.
