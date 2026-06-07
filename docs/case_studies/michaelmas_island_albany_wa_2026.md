# Michaelmas Island Albany WA 2026

This case study records an active-event AI1SAD replay for the fatal Michaelmas Island incident near Albany, Western Australia.

The replay uses three separated runs:

- strict pre-incident replay
- quiet-day comparison
- post-incident operational update

The strict pre-incident and quiet-day runs intentionally match because both use the same location, season, spearfishing activity, and offshore structure context without post-incident signals. This avoids making the model look more successful by weakening the comparison baseline.

## Verified Event Record

| Field | Value |
| --- | --- |
| Location | Michaelmas Island, City of Albany, Western Australia |
| Replay coordinates | `-35.050, 118.020` approximate operational point |
| Date | `2026-06-06` |
| Incident time | approximately `11:25 a.m. AWST` |
| Reported to DPIRD | approximately `11:30 a.m. AWST` |
| Victim context | male diver, age 35 |
| Activity | spearfishing with family |
| Outcome | fatal |
| Official wording | suspected `4.5 m` shark |
| Secondary classification | suspected white shark, source-attributed and unconfirmed |

The replay does not treat white-shark taxonomy as confirmed.

## Timeline Separation

The strict pre-incident replay excludes:

- post-incident caution or closure guidance
- contemporaneous or later shark reports unless clearly timestamped earlier
- invented prey migration values
- invented currents, weather, sightings, or habitat values
- Rottnest Island and Queensland fatalities as same-corridor events

Rottnest Island and Queensland may be broader regional/national context in narrative review only. They are not modeled as the same connected coastal corridor, and the replay makes no same-individual assumption.

## Replay Results

| Run | Warning Score | Activity Hazard Score | Surveillance Priority Score | Interpretation |
| --- | ---: | ---: | ---: | --- |
| Strict pre-incident | `0.0` low | `58` elevated | `89.3` high | Existing WA spearfishing/offshore-structure context already creates high surveillance attention without hindsight. |
| Quiet-day comparison | `0.0` low | `58` elevated | `89.3` high | Same location, season, spearfishing activity, and offshore structure baseline; no incident-specific signals. |
| Post-incident operational update | `0.0` low | `70` elevated | `100` high | Fatal recent interaction and caution guidance increase operational focus after the source time. |

## Missing Signal Sources

The strict replay marks missing sources rather than filling values:

- weather observations
- ocean observations
- SST anomaly
- vessel activity
- human exposure estimates
- biological events
- recent interactions
- sighting reports

## Operational Pattern

Recommended patterns:

- `offshore_island_focus_scan`
- `shoreline_return_route_monitoring`
- `spearfishing_activity_buffer`
- `post_incident_focus_area`

Active regional pack: `western_australia`.

## Artifacts

- [Replay JSON](../assets/case_studies/michaelmas_island_albany_wa_2026_replay.json)
- [Factor Summary JSON](../assets/case_studies/michaelmas_island_albany_wa_2026_factor_summary.json)
- [Heatmap SVG](../assets/case_studies/michaelmas_island_albany_wa_2026_heatmap.svg)

## Operational Caveat

This replay is a bounded operational-surveillance artifact. It is not a safety guarantee and does not replace official beach, wildlife, weather, or emergency guidance.
