# Cromwell's Beach Hawaii 2026 Replay

This replay is timeline-separated for operational review. It does not predict attacks and does not infer shark intent.

## Verified Incident Record

- Location: Cromwell's Beach near Diamond Head, Honolulu, Oahu, Hawaii
- Coordinates: `21.255, -157.810`
- Date: `2026-05-30`
- Sensitivity window (HST): `2026-05-30T06:15:00-10:00` through `2026-05-30T06:30:00-10:00`
- EMS response reported around `06:30 a.m. HST`
- Outcome: non-fatal serious lower-extremity injuries
- Species context: unidentified shark, reported size `6 to 8 feet`

Public reporting references:
- [Hawaii News Now coverage](https://www.hawaiinewsnow.com/)
- [KITV coverage](https://www.kitv.com/)
- [Honolulu Ocean Safety alerts](https://www.honolulu.gov/)

## Replay Structure

This case study includes four runs:

1. Pre-incident replay (swimming across channel variant)
2. Pre-incident replay (surfing or paddling out variant)
3. Quiet-day comparison baseline (same location/season/time context)
4. Post-incident surveillance update (includes later confirmed warnings)

A fifth view is included as a clearly hypothetical sensitivity run:

- hypothetical earlier public sighting ingestion before `~06:30 HST`

Supporting artifacts:

- [Replay report JSON](../assets/case_studies/cromwells_beach_hawaii_2026_replay.json)
- [Factor summary JSON](../assets/case_studies/cromwells_beach_hawaii_2026_factor_summary.json)
- [Heatmap SVG](../assets/case_studies/cromwells_beach_hawaii_2026_heatmap.svg)

## Timeline Separation Rules Applied

Pre-incident runs exclude:

- post-incident confirmed shark warning near Cromwell's swim area/surf break
- Ala Moana Bowls warning around `~07:20 a.m. HST`

Post-incident update includes:

- confirmed shark warning near Cromwell's area after incident time
- separate Ala Moana Bowls warning as a later nearby sighting cluster
- `reported_behavior="aggressive"` only as source-attributed report text

## Scores

| Run | warning_score | activity_hazard_score | surveillance_priority_score | Band |
| --- | ---: | ---: | ---: | --- |
| Pre (swimming across channel) | `0.0` | `0` | `15.0` | low |
| Pre (surfing or paddling out) | `0.0` | `0` | `18.0` | low |
| Post-incident update | `0.0` | `0` | `40.0` | moderate |
| Hypothetical earlier sighting | `0.0` | `0` | `29.0` | moderate |

## Quiet-Day and Post Comparison

- Quiet-day baseline warning score: `15.33` (low)
- Pre-incident warning delta above quiet-day: `-15.33`
- Post-incident surveillance delta vs strongest pre-incident variant: `+22.0`
- Hypothetical earlier-sighting surveillance delta vs strongest pre-incident variant: `+11.0`

## Operational Interpretation

- Before `~06:30 a.m. HST`, AI1SAD showed **low** surveillance attention, not a high-warning state.
- The pre-incident signal stack was **weak-to-moderate with limited confidence**, mainly due to missing live sources.
- Missing sources that limited confidence: weather observations, vessel activity, biological events, recent interactions, and verified sighting reports.
- After incident-time public warnings and nearby verified reports were ingested, surveillance priority rose from moderate to elevated.
- In the hypothetical earlier-ingestion run, surveillance priority increased earlier than the strict pre-incident baseline, but still did not become a standalone attack-probability statement.

Recommended surveillance pattern in these runs: `surf-zone ladder search`.

## Disclaimer

AI1SAD estimates environmental and surveillance-relevant shark encounter conditions. It does not predict individual attacks, does not infer shark intent, and is not a substitute for local lifeguard, maritime, wildlife, weather, or emergency guidance.
