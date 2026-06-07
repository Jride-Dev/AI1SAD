# Hawaii Signal Gap Analysis (Cromwell's Beach 2026)

This document reviews why the strict pre-incident Cromwell's Beach replay remained low, and what Hawaii-focused signal coverage improvements are most likely to improve operational surveillance awareness.

Scope limits:

- no scoring-weight changes
- no attack-probability claims
- no shark-intent claims
- no speculative signals treated as historical fact

## Case Scope

- Case: Cromwell's Beach near Diamond Head, Honolulu, Oahu
- Date: 2026-05-30
- Pre-incident sensitivity window: approximately 06:15-06:30 HST
- Replay variants:
  - `swimming_across_channel`
  - `surfing_or_paddling_out`
- Timeline guardrail:
  - post-incident Cromwell's confirmation and later Ala Moana Bowls reports are excluded from pre-incident runs

## Why Pre-Incident Stayed Low

The strict pre-incident runs had very limited live/verified early-morning signals. Habitat/activity context was present, but high-value short-latency observational layers were mostly missing. In this configuration, AI1SAD remained in a bounded low surveillance band before incident-time reports were ingested.

## Pre-Incident Input Audit

Status keys used below:

- `available`
- `unavailable`
- `stale`
- `not_applicable`
- `low_confidence`
- `missing_provider`
- `future_provider_candidate`

| Signal Layer | Status | Notes |
| --- | --- | --- |
| Rainfall / runoff | `available` + `low_confidence` | Engine supports weather/rainfall context, but this replay run had no strong, high-confidence local weather observations in-window. |
| SST / anomaly | `available` + `unavailable` | Adapter exists, but replay input was missing SST/anomaly observations for this pre-incident window. |
| NOAA/NWS alerts | `available` + `unavailable` | Provider exists for U.S. alerts; no decisive pre-incident alert signal was active in this replay input. |
| Surf conditions | `missing_provider` | No dedicated live surf-state ingestion adapter yet (period/height/energy by spot/time). |
| Channel / reef-edge habitat | `available` | Baseline habitat context (reef/dropoff/channel) supported and used. |
| Tidal state | `static_baseline_support` | Phase 23 adds static/offline tide-window context; no live tide-state ingestion is enabled yet. |
| Current direction | `static_baseline_support` | Phase 23 adds static/offline nearshore current-direction/speed and channel-flow context; no live current feed is enabled yet. |
| Water clarity / turbidity | `static_baseline_support` | Phase 24 adds static/offline Oahu visibility baselines; no live clarity/turbidity ingestion is enabled yet. |
| Human exposure | `available` + `low_confidence` | Static exposure profiles exist, but no high-resolution time-of-day local occupancy feed in this run. |
| Early-morning surf/swim overlap | `available` + `low_confidence` | Activity variant is modeled, but overlap intensity by minute/spot is not live-ingested. |
| Shark sightings | `available` + `unavailable` | Sighting field supported, but strict pre-incident run intentionally had no verified pre-06:30 ingestion. |
| Baitfish presence | `available` + `unavailable` + `low_confidence` | Biological adapter exists, but no verified in-window baitfish event signal in this case input. |
| Turtle migration / nesting context | `available` + `low_confidence` | Supported as bounded biological context when present; not a strong active driver in this replay input. |
| Biological events (general) | `available` + `unavailable` | Provider exists (static/manual), but no active verified event supplied for this pre-incident window. |
| Vessel/fishing context | `available` + `unavailable` | Provider exists (static/manual), but no active nearby vessel/fishing signal in this pre-incident input. |
| Hawaii seasonal species profiles | `available` | Regional pack context exists and contributed bounded contextual points only. |

## Signal-Gap Matrix

| Signal | Current AI1SAD support | Pre-incident availability | Confidence impact | Surveillance usefulness | Recommended next action | Provider/dataset candidate | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Live sightings ingestion | Structured replay/provider fields exist | Low (none ingested pre-window) | High | High | Add low-latency verified sightings adapter with strict timestamps/source attribution | Honolulu Ocean Safety / lifeguard dispatch-compatible feed (if policy/permitted) | high |
| Surf-line / lifeguard observations | Partial manual/context only | Low | High | High | Add structured observation ingest for patrol/lifeguard reports | Lifeguard ops log ingestion adapter (manual/API bridge) | high |
| Tide state | Static/offline baseline adapter | Partial baseline only | Medium | High | Add live or pre-fetched tide-phase/height ingestion after static validation | NOAA CO-OPS, PacIOOS South Shore Oahu ROMS | high |
| Current direction/speed | Static/offline baseline adapter | Partial baseline only | Medium | High | Add live or pre-fetched nearshore current context ingestion | PacIOOS South Shore Oahu ROMS, PacIOOS Oahu ROMS, PacIOOS Main Hawaiian Islands ROMS, NOAA CO-OPS currents | high |
| Turbidity / water clarity | Static/offline baseline adapter | Partial baseline only | Medium | High | Add source-timestamped prefetch after static validation | NOAA CoastWatch, PacIOOS water quality, Hawaii beach water-quality datasets | high |
| Reef-channel habitat mapping | Baseline habitat flags | Partial | Medium | High | Increase granularity from boolean habitat to mapped reef-channel zones | Static Hawaii habitat map pack | high |
| Hawaii human exposure timing | Static profiles | Partial | Medium | High | Add time-sliced exposure curves (weekday/weekend/time-of-day) | Local beach-use schedule/profile dataset | high |
| Biological prey context | Static/manual biology adapter | Low | Medium | Medium | Expand verification workflow and freshness decay for prey-context signals | Curated biological event registry with expiry | medium |
| SST/anomaly freshness | Adapter exists, often offline/mock | Low to partial | Medium | Medium | Improve ingest freshness and coverage checks | NOAA CoastWatch operational ingestion path | medium |
| NOAA/NWS hazard linkage | Provider exists | Partial | Low to medium | Medium | Keep as supporting context; improve alert-to-zone relevance mapping | NOAA/NWS alerts + localized spatial mapping | medium |
| Vessel/fishing context | Static/manual adapter | Low | Low to medium | Medium | Expand nearshore effort proxies where policy-safe | Public harbor/launch schedules or curated local logs | low |
| Turtle seasonal context | Biological context support | Partial | Low | Low to medium | Keep bounded, background-only unless stacked | Hawaii seasonal ecology calendar | low |

## Strongest Likely Gaps (Ranked)

1. Live sightings ingestion
2. Surf-line / lifeguard observation ingestion
3. Tide/current context: static/offline baseline support added in Phase 23; live PacIOOS/NOAA ingestion remains future work.
4. Live water clarity / turbidity context beyond static baselines
5. Reef-channel habitat mapping granularity
6. Hawaii-specific human exposure timing
7. Biological prey-context freshness/verification

## Do Not Tune Yet

This single incident should not be used to retune scoring weights. The disciplined sequence is:

1. improve signal coverage and freshness first
2. run strict timeline-separated replays across a wider Hawaii cohort
3. evaluate calibration only after broader dataset expansion

Calibration should follow improved data coverage, not precede it.

## Future Hawaii Replay Cohort Plan

Target cohort: 10-20 Hawaii replay cases with:

- mixed fatal and non-fatal incidents
- mixed islands and coast types
- mixed activity contexts (swim/surf/dive/fishing/paddle)
- mixed seasons and environmental states
- matched quiet-day controls
- strict hindsight separation in every case

Evaluation outputs for cohort review:

- surveillance band movement timing
- confidence deltas by missing-source class
- false-elevation and missed-elevation patterns
- provider freshness impact on operational interpretation

## Recommended Implementation Roadmap

A. Hawaii habitat mapping adapter  
B. Tide/current adapter: Phase 23 static/offline baseline complete; future work should add source-timestamped ingestion.  
C. Water clarity/turbidity adapter  
D. Live sightings ingestion adapter  
E. Hawaii replay cohort buildout  
F. Calibration review (post-cohort only)

## Phase 22 Status

Phase 22 adds a static/offline Hawaii habitat mapping adapter and baseline Oahu demo profiles for:

- Cromwell's Beach / Diamond Head
- Kaikoo / Hale Mano channel context
- Waikiki / Ala Moana south-shore context
- reef-channel demo baseline
- shallow-reef edge demo baseline
- sandy-bottom quiet-day baseline

These are historic/static habitat baselines with source-date metadata, not live habitat observations.

## Operational Bottom Line

For Cromwell's Beach pre-incident conditions, AI1SAD behaved as a bounded low-confidence, low-surveillance system because key short-latency Hawaii observational layers were unavailable. The highest-value improvement path is better early local signal ingestion and habitat/ocean-state coverage, not weight tuning to one event.
