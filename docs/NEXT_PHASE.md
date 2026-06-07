# Next Phase

## Phase 25: Live Sightings & Surf-Line Observation Ingestion Adapter

## Objective

Add a reviewed, source-attributed ingestion path for live or manually pre-fetched shark sightings, surf-line observations, and lifeguard/patrol reports so AI1SAD can improve operational awareness without changing scoring weights to fit one incident.

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

## Phase 24 Completion Note

Phase 24 adds static/offline Hawaii water clarity and turbidity baseline support:

- NOAA CoastWatch as a future ocean-color source candidate
- PacIOOS water-quality products as future Hawaii-first source candidates
- Hawaii beach water-quality datasets as future policy-reviewed candidates
- bounded warning/surveillance/explainability/alert/replay integration
- Cromwell replay regression coverage

Live clarity/turbidity ingestion is still future work.

## Planned Scope

1. Add a sightings/observation ingestion schema that preserves source timestamps
2. Support reviewed manual/offline inputs first, then pre-fetched official feeds where policy allows
3. Add clear source classes for lifeguard, public report, official advisory, drone/patrol, and receiver/telemetry candidate records
4. Keep strict replay chronology and prevent post-event reports from contaminating pre-incident runs
5. Add public/private filtering so raw notes and restricted details are not exposed publicly
6. Add focused tests and Cromwell/Recife/WA replay regression checks

## Official/Public Source Candidates

- Hawaii lifeguard or ocean-safety logs where policy/terms allow
- Official beach advisories and state/local public safety notices
- Reviewed manual observations from patrol, drone, or public-report workflows
- Future telemetry or receiver detections where provider terms and privacy rules allow

All source integration should begin as reviewed manual/offline ingestion first, with source timestamps, received timestamps, confidence labels, and public/private visibility retained.

## Bounded Behavior Rules

- Unverified public reports must remain lower confidence until reviewed.
- Observations must be evaluated against event time in replay mode, not wall-clock time.
- Stronger effects require recency, source confidence, proximity, or stacking with activity, prey, SST, weather, tide/current, visibility, or exposure signals.
- Do not infer species or behavior beyond source-attributed wording.
- No scoring-weight tuning around Cromwell's or any single case.

## Recommended Execution Order

1. Observation schema and confidence labels
2. Manual/offline provider adapter
3. Signal broker integration
4. Warning/surveillance/alert/explainability bounded wiring
5. Replay timeline-safety integration
6. Tests and docs
7. Validation sweep

## Validation Expectations

- focused sightings/observation ingestion tests
- focused Cromwell timeline-regression tests
- focused Recife and WA replay chronology tests
- full backend test suite
- mkdocs build
- secret scan
- prohibited-language scan

Frontend tests/build can remain skipped if frontend files are unchanged.

## Review Gate

Do not commit until review.

## Current Interruption Note

Phase 24 is reviewed and committed locally. Begin Phase 25 only when explicitly requested.
