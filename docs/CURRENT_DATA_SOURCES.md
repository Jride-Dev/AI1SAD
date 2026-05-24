# Current Condition Data Sources

Phase 3B adds a warning-data pipeline that aggregates current-condition signals. This creates a warning score, not an attack prediction.

## Reliable Automated Sources

- Open-Meteo: no-key rainfall and air-temperature history for previous 72 hours.
- NOAA/NWS: future interface for U.S. weather alerts and observations.
- NOAA CoastWatch ERDDAP: future SST interface once dataset IDs and spatial/time windows are selected.

## Limited Or Uncertain Sources

- Copernicus Marine: useful for ocean products, but requires product selection and credentials.
- Global Fishing Watch: useful for vessel/fishing activity proxies, but requires API access and careful interpretation.
- News/event search: useful for whale carcass, stranding, baitfish bloom, or prey event discovery, but noisy and incomplete.
- Human exposure estimates: likely derived from beach attendance, surf reports, holidays, weekends, weather, and local proxies; uncertainty will remain high.

## Biological Event Limitations

Biological events can be high-signal but sparse:

- Whale carcass reports may be delayed or removed quickly.
- Marine strandings may not imply nearshore shark presence.
- Baitfish/prey signals can be local and short-lived.
- Stale biological events expire from scoring.
- Manual events must be reviewed before being marked public.

## Provider Freshness

Provider ingestion is tracked separately from public warning responses:

- `provider_runs`: successful ingestion attempts, record counts, timing, and provider metadata.
- `provider_failures`: failed provider attempts, exception summaries, timestamps, and retry context.
- `provider_health`: latest provider status, including `last_success`, `records_ingested`, and `status`.

When observations are stale or missing, the warning engine lowers confidence and adds the source to `missing_data_sources`. It does not silently assume normal conditions.

Phase 5 also normalizes provider outputs into the generic `signals` collection. Signals carry `signal_type`, species context when known, location, timestamp, expiration, confidence, provider source, freshness, relevance, and public/private visibility. Warning and surveillance engines can consume active public signals alongside legacy observation collections.

Provider modules now live under `app/providers/`. Paid, key-restricted, or policy-sensitive providers are clean placeholder interfaces until credentials, terms, and review rules are ready.

## Warning Snapshot Cache

`warning_snapshots` stores public warning payloads behind a cache key derived from location, radius, lookback window, month, and river-mouth distance. Snapshots expire via `expires_at` and a MongoDB TTL index.

Default cache lifetime is region-aware:

- 30 minutes for fast-changing coastal/tourist regions such as Florida, Hawaii, and Red Sea profiles.
- 45 minutes for Australia profiles.
- 60 minutes for broader/default profiles.

Callers can bypass cache during QA with `bypass_cache=true`.

## Event Intelligence Collections

The event layer is intentionally deterministic and evidence-tracked. Event collections include:

- `biological_events`
- `marine_incidents`
- `shipping_events`
- `fish_kill_reports`
- `carcass_reports`
- `beach_closures`

Future records should include confidence labels such as `official`, `verified`, `community_report`, `news_only`, or `unconfirmed`.

## Warning Score, Not Attack Prediction

The warning engine estimates current encounter conditions from available signals:

- rainfall/runoff
- river mouth proximity
- sea surface temperature and anomaly
- fishing/vessel activity
- biological events
- human exposure
- regional seasonal multipliers

The warning score does not predict attacks. It is not a safety guarantee and should not replace official beach, lifeguard, weather, wildlife, or emergency guidance.

The project deliberately starts with deterministic, explainable rules. A Bayesian/statistical layer may come later, and any ML ensemble belongs after the data contracts, source freshness, and explainability layer are stable.

Provider API keys and external-provider configuration must stay in `.env` or deployment secrets only.
