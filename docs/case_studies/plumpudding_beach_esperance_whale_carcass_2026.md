# Plumpudding Beach Esperance Whale Carcass 2026

This case study records a timeline-safe AI1SAD operational replay for the WA SharkSmart Shark ADVICE issued for Plumpudding Beach, west of Esperance, near Butty Head in the Shire of Esperance, Western Australia.

The initial replay uses only the official carcass report context. It does not include a confirmed shark sighting. A second sensitivity run adds a clearly hypothetical nearby sighting to show how timely sighting ingestion would change surveillance priority.

## Verified Event Record

| Field | Value |
| --- | --- |
| Official source | WA SharkSmart Shark ADVICE for Plumpudding Beach, west of Esperance |
| Location | Plumpudding Beach near Butty Head, Shire of Esperance, Western Australia |
| Replay coordinates | `-33.900, 121.650` approximate operational point |
| Event date | `2026-05-29` |
| Earliest source-attributed sighting time | `2026-05-29T14:00:00+08:00` |
| SharkSmart report time | Member-of-public report at approximately 2:30 p.m. |
| SLSWA report | Sighted at 2:00 p.m., approximately 1 metre offshore, logged at 3:04 p.m. |

## Taxonomy Handling

The official alert does not identify the whale species. The replay stores `whale_taxon` as `Kogia sp.` and `possible_species` as `Kogia breviceps` only as provisional context. These fields are not treated as verified species identification.

## Carcass Metadata

| Field | Value |
| --- | --- |
| `estimated_length_m` | not reported |
| `carcass_mass_class` | `small_whale` |
| `decomposition_state` | `not_reported` |
| `distance_to_shore_m` | `1` |
| `drift_direction` | `not_reported` |
| `drift_speed` | `not_reported` |
| `residue_present` | `unknown` |
| `removal_status` | `not_reported` |
| `last_verified_at` | `2026-05-29T15:04:00+08:00` |
| `taxonomy_confidence` | `provisional_unverified` |

## Replay Results

| Run | Warning Score | Activity Hazard Score | Surveillance Priority Score | Interpretation |
| --- | ---: | ---: | ---: | --- |
| Initial report | `19.68` low | `12` low | `24.96` low | Carcass context is present, but missing live signals keep confidence and surveillance priority bounded. |
| Hypothetical nearby sighting sensitivity | `19.68` low | `12` low | `35.96` moderate | A clearly hypothetical verified nearby sighting raises surveillance priority by `11.0` points. |

The initial report remains a low-warning state. The biological event is the dominant signal, but weather, current, SST, vessel, human-exposure, reef, and confirmed sighting sources are missing or not asserted.

## Dominant Factors

Initial report:

- `biological_event_score`: `19.68`
- `biological_event_surveillance_context`: `14.76`
- `activity_hazard_score`: `4.2`
- `regional_sst_species_context`: `3`
- `regional_species_suitability`: `3`

Hypothetical sighting sensitivity:

- `biological_event_surveillance_context`: `14.76`
- `verified_sightings_nearby`: `11`

## Missing Signal Sources

The initial replay marks these sources as missing rather than filling values:

- `weather_observations`
- `ocean_observations`
- `sst_anomaly`
- `vessel_activity`
- `human_exposure_estimates`
- `recent_interactions`
- `sighting_reports`
- `reef_features`

## Operational Pattern

AI1SAD's engine output remains bounded because the initial report has no confirmed sighting and no live environmental stack. For operator planning around the carcass event, the recommended pattern is:

- `carcass_event_buffer_zone`
- `shoreline_parallel_sweep`
- future down-current drift corridor once tide/current support exists

Active regional pack: `western_australia`.

## Artifacts

- [Replay JSON](../assets/case_studies/plumpudding_beach_esperance_whale_carcass_2026_replay.json)
- [Factor Summary JSON](../assets/case_studies/plumpudding_beach_esperance_whale_carcass_2026_factor_summary.json)
- [Heatmap SVG](../assets/case_studies/plumpudding_beach_esperance_whale_carcass_2026_heatmap.svg)

## Operational Caveat

This replay is a bounded operational-surveillance artifact. It is not a safety guarantee and does not replace official beach, wildlife, weather, or emergency guidance.
