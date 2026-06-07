# Lovers Point Pacific Grove Whale Carcass 2026

This case study records an AI1SAD operational replay for the deceased whale and temporary beach-access closure at Lovers Point, Pacific Grove, Monterey County, California.

The replay uses three separated runs:

- initial carcass-response scenario
- drift-corridor planning scenario
- hypothetical nearby-sighting sensitivity scenario

## Verified Event Record

| Field | Value |
| --- | --- |
| Location | Lovers Point, Pacific Grove, Monterey County, California |
| Replay coordinates | `36.625, -121.916` approximate operational point |
| Initial police notification | approximately `12:55 p.m. PDT` on `2026-06-03` |
| Event | deceased whale floating near shoreline |
| Authority response | temporary Lovers Point beach-access closure |
| Official concern | marine mammal carcasses can attract sharks, particularly larger predatory species |
| Closure monitoring | continued through at least `2026-06-05` |

## Taxonomy Handling

Official city follow-up identifies a humpback whale stranding. Earlier conflicting identification, if present, is retained only as source-attributed historical metadata and is not presented as settled fact.

## Replay Results

| Run | Warning Score | Activity Hazard Score | Surveillance Priority Score | Interpretation |
| --- | ---: | ---: | ---: | --- |
| Initial carcass response | `23.73` low | `12` low | `28.16` moderate | Nearshore carcass and closure context raise surveillance review modestly; no shark sightings are included. |
| Drift-corridor planning | `23.73` low | `12` low | `28.16` moderate | Drift direction remains unavailable because no tide/current fixture is available for this case. |
| Hypothetical nearby sighting sensitivity | `23.73` low | `12` low | `39.16` moderate | A clearly hypothetical nearby sighting adds an `11.0` point surveillance-priority lift. |

## Drift Handling

The drift-corridor planning run is labeled operational planning only. It does not invent:

- drift direction
- drift speed
- down-current path
- tide/current values

The `future_down_current_drift_corridor` recommendation remains a future pattern until tide/current support exists for this case.

## Missing Signal Sources

The verified runs mark missing sources rather than filling values:

- drift direction
- tide/current fixture
- weather observations
- ocean observations
- SST anomaly
- vessel activity
- human exposure estimates
- recent interactions
- sighting reports

## Operational Pattern

Recommended patterns:

- `carcass_event_buffer_zone`
- `shoreline_parallel_sweep`
- `kelp_edge_focus_scan`
- `future_down_current_drift_corridor`

Active regional pack: `california`.

## Artifacts

- [Replay JSON](../assets/case_studies/lovers_point_pacific_grove_whale_carcass_2026_replay.json)
- [Factor Summary JSON](../assets/case_studies/lovers_point_pacific_grove_whale_carcass_2026_factor_summary.json)
- [Heatmap SVG](../assets/case_studies/lovers_point_pacific_grove_whale_carcass_2026_heatmap.svg)

## Operational Caveat

This replay is a bounded operational-surveillance artifact. It is not a safety guarantee and does not replace official beach, wildlife, weather, or emergency guidance.
