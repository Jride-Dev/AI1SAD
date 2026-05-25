# Explainability Engine

Phase 11 adds a deterministic explanation layer for AI1SAD warning, surveillance, replay, and alert outputs.

The explanation layer does not predict attacks. It explains why environmental, biological, human-exposure, activity, and regional signals produced a warning or surveillance-priority output.

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
