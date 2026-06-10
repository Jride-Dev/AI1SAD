# Replay Library

The AI1SAD replay library presents historical and demo scenarios as evidence-backed operational case studies. Each entry is a structured record with replay output, quiet-day comparison, factor summary, explanation text, version metadata, and a disclaimer.

Replay library outputs are read-only scenario records. They do not add scoring logic, new providers, billing, authentication, or individual outcome claims.

## API Endpoints

```text
GET /api/v1/replay/library
GET /api/v1/replay/library/{replay_id}
```

## Current Library Entries

| Replay ID | Title | Region | Context |
| --- | --- | --- | --- |
| `horseshoe_reef_2026` | Horseshoe Reef 2026 | Western Australia | Spearfishing, reef habitat, and white shark regional suitability |
| `queensland_spearfishing_reef_tiger_bull_2026` | Queensland Spearfishing 2026 | Far North Queensland, Australia | Tropical reef spearfishing with tiger/bull shark operational context |
| `florida_crowded_inlet_demo` | Florida Crowded Inlet Demo | Florida | Crowding, inlet exposure, surf/fishing activity, and regional species context |
| `nsa_panama_city_florida_2026_drone_observation` | NSA Panama City Florida 2026 Drone Observation Fixture | Panama City, Florida | Human-operated drone observation, analyst-attributed probable species metadata, and no-sighting patrol semantics |
| `hawaii_october_tiger_context_demo` | Hawaii October Tiger Shark Context Demo | Hawaii | October regional context and calm monitoring workflow |
| `cromwells_beach_hawaii_2026` | Cromwell's Beach Hawaii 2026 | Honolulu, Oahu, Hawaii | Timeline-separated pre-incident, quiet-day, post-incident update, and hypothetical early-sighting sensitivity |
| `plumpudding_beach_esperance_whale_carcass_2026` | Plumpudding Beach Esperance Whale Carcass 2026 | Western Australia | Official WA carcass advice replay with bounded initial report and hypothetical sighting sensitivity |
| `michaelmas_island_albany_wa_2026` | Michaelmas Island Albany WA 2026 | Western Australia | Active-event replay with strict pre-incident, quiet-day, and post-incident operational update runs |
| `lovers_point_pacific_grove_whale_carcass_2026` | Lovers Point Pacific Grove Whale Carcass 2026 | Monterey County, California | Nearshore carcass, closure, drift-planning, and hypothetical sighting sensitivity replay |
| `piedade_boa_viagem_recife_2026` | Piedade and Boa Viagem Recife 2026 | Greater Recife, Pernambuco, Brazil | Paired strict chronology replay with Piedade-to-Boa-Viagem recent-interaction lift |
| `red_sea_anomaly_demo` | Red Sea Anomaly Demo | Red Sea | Biological anomaly and tourism corridor operational review |

## Linked Case Studies

- [Horseshoe Reef 2026](CASE_STUDY_HORSESHOE_REEF_2026.md)
- [Queensland Spearfishing 2026](case_studies/queensland_spearfishing_2026.md)
- [NSA Panama City Florida 2026 Drone Observation Fixture](case_studies/nsa_panama_city_florida_2026.md)
- [Cromwell's Beach Hawaii 2026](case_studies/cromwells_beach_hawaii_2026.md)
- [Plumpudding Beach Esperance Whale Carcass 2026](case_studies/plumpudding_beach_esperance_whale_carcass_2026.md)
- [Michaelmas Island Albany WA 2026](case_studies/michaelmas_island_albany_wa_2026.md)
- [Lovers Point Pacific Grove Whale Carcass 2026](case_studies/lovers_point_pacific_grove_whale_carcass_2026.md)
- [Piedade and Boa Viagem Recife 2026](case_studies/piedade_boa_viagem_recife_2026.md)
- [Recife Signal Gap Analysis](RECIFE_SIGNAL_GAP_ANALYSIS.md)
- [Hawaii Signal Gap Analysis](HAWAII_SIGNAL_GAP_ANALYSIS.md)
- [Hawaii Habitat Provider](HAWAII_HABITAT_PROVIDER.md)

## Required Fields

Each replay library item includes:

- `id`
- `title`
- `region`
- `coordinates`
- `observed_at`
- `activity_context`
- `species_context`
- `replay_output`
- `quiet_day_comparison`
- `factor_summary`
- `explanation_summary`
- `heatmap_asset`
- `model_version`
- `scoring_revision`
- `provider_stack_version`
- `generated_at`
- `disclaimer`

## Operational Use

The library is intended for demos, documentation, regression review, and operator education. The frontend displays the backend-provided fields directly and does not calculate scores.
