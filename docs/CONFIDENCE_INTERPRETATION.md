# Confidence Interpretation

AI1SAD confidence is an operational data-quality indicator. It is not a probability of an encounter or attack.

## Components

- Coverage confidence: how many expected source categories are present.
- Freshness confidence: whether available signals are current enough for the requested lookback.
- Completeness confidence: how much important information is missing.

## Missing Data

Missing weather, SST, vessel, biological, human exposure, sighting, incident, reef, or regional-pack data lowers confidence. The model should report missing data rather than silently assuming normal conditions.

## Stale Data

Stale sources reduce freshness confidence. Stale signals should not be allowed to create strong operational alerts unless other current signals support the output.

## Practical Reading

- High confidence: enough relevant source categories are present and current.
- Moderate confidence: useful for review, but some sources are missing or stale.
- Low confidence: interpret cautiously and seek local authority or provider data.
- Very low confidence: insufficient data for strong operational conclusions.
