# Piedade And Boa Viagem Recife 2026

This paired case study records a timeline-separated AI1SAD replay for two Greater Recife incidents in Pernambuco, Brazil. It is designed to show what the current model can and cannot represent without adding a Recife scoring retune.

The replay uses four runs:

- Piedade strict pre-incident replay
- Piedade quiet-day comparison
- Boa Viagem strict pre-incident replay
- Boa Viagem quiet-day comparison

## Verified Incident Records

| Field | Piedade Beach | Boa Viagem Beach |
| --- | --- | --- |
| Location | Piedade Beach, Jaboatao dos Guararapes, Greater Recife, Pernambuco, Brazil | Boa Viagem Beach, Recife, Pernambuco, Brazil; Acaiaca / Padre Bernardino Pessoa corridor |
| Replay coordinates | `-8.171, -34.914` approximate operational point | `-8.126, -34.899` approximate operational point |
| Date | `2026-05-31` | `2026-06-01` |
| Approximate local time | `13:40` | `15:10` |
| Victim context | Bather, age 11 | Bather, age 19 |
| Outcome | Serious injuries with left-leg amputation | Serious injuries with right-leg amputation |
| Source-attributed species assessment | CEMIT preliminary adult bull shark, Portuguese source term `tubarão-cabeça-chata`, approximately 2.5 m if retained from source | CEMIT preliminary adult tiger shark, Portuguese source term `tubarão-tigre`, approximately 3 m |

The CEMIT species assessments are stored as preliminary, source-attributed classifications. They are not used as independently verified taxonomy in the strict pre-incident model inputs.

The paired replay does not generalize both incidents as bull-shark events. It keeps Piedade's source-attributed bull-shark context separate from Boa Viagem's source-attributed tiger-shark context and does not assume the same individual shark caused both incidents.

## Replay Inputs

The strict pre-incident runs do not include hindsight signals. Tide, current, turbidity, rainfall, SST, and weather values are marked missing where unavailable.

| Run | Timeline rule | Included signals | Excluded signals |
| --- | --- | --- | --- |
| Piedade strict pre-incident | Before `2026-05-31T13:40-03:00` | Bather/swimming activity and baseline reef-barrier/channel context | Boa Viagem incident, later response activity, post-incident species assessment as model input |
| Piedade quiet day | Same location, season, time-of-day | Same baseline activity and habitat context | Incident-specific signals |
| Boa Viagem strict pre-incident | Before `2026-06-01T15:10-03:00` | Bather/swimming activity, baseline reef-barrier/channel context, and Piedade as a known recent regional interaction | Post-Boa-Viagem response activity and post-incident species assessment as model input |
| Boa Viagem quiet day | Same location, season, time-of-day | Same baseline activity and habitat context | Piedade recent-interaction signal |

## Replay Results

| Run | Warning Score | Activity Hazard Score | Surveillance Priority Score | Confidence | Interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| Piedade strict pre-incident | `0.0` low | `0` low | `9.0` low | `0.43` | Very weak pre-incident signal stack; available context only defines an observation corridor. |
| Piedade quiet day | `0.0` low | `0` low | `9.0` low | `0.43` | Same output because no incident-specific pre-signal is available. |
| Boa Viagem strict pre-incident | `0.0` low | `0` low | `23.0` low | `0.48` | Prior Piedade interaction adds a timeline-valid regional cluster signal, raising surveillance attention by `14.0`. |
| Boa Viagem quiet day | `0.0` low | `0` low | `9.0` low | `0.43` | Without the Piedade recent interaction, Boa Viagem returns to the same weak baseline. |

## Dominant Factors

Piedade strict pre-incident:

- `reef_dropoff_habitat_proximity`: `5`
- `activity_context`: `4`

Boa Viagem strict pre-incident:

- `recent_interactions_nearby`: `14`
- `reef_dropoff_habitat_proximity`: `5`
- `activity_context`: `4`

Species-specific explainability metadata:

- `piedade_source_attributed_bull_shark_suitability`: `0` points; CEMIT preliminary `tubarão-cabeça-chata` context only
- `boa_viagem_source_attributed_tiger_shark_suitability`: `0` points; CEMIT preliminary `tubarão-tigre` context only
- `species_agnostic_recent_interaction_lift`: `14.0` points; shared corridor cluster context after Piedade, not a same-species or same-individual assumption

## Missing Signal Sources

The replay explicitly marks these gaps:

- live sighting ingestion
- Recife/Pernambuco regional pack
- tide and current observations
- turbidity and water clarity
- rainfall/runoff lookback
- SST/anomaly
- human exposure estimates
- vessel/fishing context
- telemetry or monitoring-program ingestion

## Operational Recommendations

Recommended patterns:

- `reef_barrier_parallel_sweep`
- `nearshore_channel_ladder_search`
- posted-swim-zone observation focus
- future tide/current and turbidity-informed corridor once supported

The current model identifies the Boa Viagem cluster signal only after Piedade becomes timeline-valid input. It does not claim the Piedade strict pre-incident signal stack was strong. This result points to coverage gaps: live observations, Recife-specific habitat/water-state context, and human-exposure timing would matter more than tuning around these two events.

## Artifacts

- [Replay JSON](../assets/case_studies/piedade_boa_viagem_recife_2026_replay.json)
- [Factor Summary JSON](../assets/case_studies/piedade_boa_viagem_recife_2026_factor_summary.json)
- [Heatmap SVG](../assets/case_studies/piedade_boa_viagem_recife_2026_heatmap.svg)
- [Recife Signal Gap Analysis](../RECIFE_SIGNAL_GAP_ANALYSIS.md)

## Caveat

This replay is a bounded operational-surveillance artifact for review and planning. It does not replace official beach, lifeguard, emergency, wildlife, or public-health guidance.
