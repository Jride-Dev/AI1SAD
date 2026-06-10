# Explainability Engine

Phase 11 adds a deterministic explanation layer for AI1SAD warning, surveillance, replay, and alert outputs.

The explanation layer does not predict attacks. It explains why environmental, biological, human-exposure, activity, and regional signals produced a warning or surveillance-priority output.

Kelp forest factors may appear when static/offline kelp habitat signals are active. Explanation text treats kelp as bounded habitat and observation-planning context, especially where kelp edge, pinniped prey context, and human activity overlap.

## Outputs

Each explanation includes:

- `factor_contributions`: normalized factor points and contribution shares
- `confidence_breakdown`: coverage, freshness, completeness, and overall confidence
- `data_freshness`: provider/source status
- `missing_data_sources`: unavailable inputs that limit interpretation
- `missing_signal_impact`: plain-language impact of missing inputs
- `regional_pack_influence`: active pack, available pack, and features used
- `regional_rules_triggered`: rule keys from active contributing factors
- `suppression_reasons`: why weak alerts or high warning claims are suppressed
- `operational_interpretation`: concise field-facing explanation
- `recommended_action`: operational recommendation text
- `metadata`: model, scoring, provider stack, and generation version fields

Kelp explanations can include:

- `kelp_forest_habitat_context` in warning factors with small bounded points
- `kelp_forest_surveillance_context` in surveillance factors when habitat stacks with prey, activity, or white shark regional context
- stale/static freshness in `data_freshness`
- confidence reduction when dense kelp affects open-water visibility

Hawaii habitat explanations can include:

- `reef_channel_context`
- `reef_edge_context`
- `shallow_reef_context`
- `hardbottom_context`
- `baseline_habitat_freshness`
- `habitat_visibility_context`

These factors are bounded baseline-structure context and must not be described as live habitat-state observation.

Hawaii tide/current explanations can include:

- `tide_window_context`
- `nearshore_current_context`
- `channel_flow_context`
- `current_speed_context`
- `current_convergence_context`
- `nearshore_model_resolution`
- `forecast_freshness`
- `station_coverage_gap`
- `regional_fallback_used`
- `tidal_exchange_context`
- `baseline_tide_current_freshness`
- `hawaii_tide_current_baseline_context`

These factors are bounded water-movement context and must not be described as live PacIOOS, ROMS, or NOAA CO-OPS observations unless a future adapter ingests source-timestamped live or pre-fetched records.

Hawaii water clarity explanations can include:

- `water_clarity_context`
- `turbidity_context`
- `sediment_runoff_visibility_context`
- `surf_zone_visibility_context`
- `visibility_activity_stack_context`
- `visibility_signal_stack_context`
- `baseline_visibility_freshness`
- `hawaii_water_clarity_baseline_context`

These factors are bounded visibility context and must not be described as live NOAA CoastWatch, PacIOOS, camera, beach, or water-quality observations unless a future adapter ingests source-timestamped records.

Drone observation explanations can include:

- `review_status`
- `source_type`
- `probable_species` with explicit assessment source
- no-sighting patrol caveats
- human-approved recommended surveillance pattern

Drone explanations must treat recommended patterns as human-reviewed planning labels, not flight-control commands.

## API Routes

- `GET /api/v1/explain/location`
- `GET /api/v1/explain/surveillance`
- `GET /api/v1/explain/replay`
- `GET /api/v1/explain/alert/{alert_id}`

These routes compose existing model outputs. They do not rerank locations with a new model, add live providers, scrape data, or call ML/LLM prediction logic.

## Metadata

Explanation payloads include:

- `model_version`
- `scoring_revision`
- `provider_stack_version`
- `generated_at`
- `replay_asset_version` for replay explanations

## Safety Boundary

Explanation text must never claim individual attack prediction, shark intent, guaranteed safety, or provocation. Spearfishing, fishing, diving, and swimming context are treated as operational activity context.
