# Recife Signal Gap Analysis

This note explains what the paired Piedade and Boa Viagem replay could represent with current AI1SAD layers, and what remains missing for a future Greater Recife / Pernambuco regional pack.

The replay should not drive scoring-weight changes by itself. The useful next step is signal coverage: habitat, water movement, visibility, exposure, sightings, and monitoring-program ingestion.

## Current Replay Finding

Piedade strict pre-incident replay stayed low because only bather/swimming activity and baseline reef-barrier/channel context were available. Boa Viagem strict pre-incident replay also stayed low-warning, but surveillance priority rose from `9.0` to `23.0` because the previous day's Piedade incident was timeline-valid recent-interaction context.

## Signal-Gap Matrix

| Signal | Current AI1SAD support | Pre-incident availability | Confidence impact | Surveillance usefulness | Recommended next action | Provider or dataset candidate | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Regional incident density | Generic recent-interaction support | Partial for Boa Viagem only | Medium | High | Build Recife cohort and strict controls | Public historical incident datasets, CEMIT public records where usable | high |
| Live sightings / lifeguard observations | Generic sighting field exists | Unavailable in these strict runs | High | High | Add source-attributed observation ingestion plan | Local lifeguard/public-safety channels, official advisories | high |
| Reef-barrier habitat | Generic reef feature flag only | Baseline context only | Medium | High | Add static habitat mapping adapter later | Pernambuco coastal habitat/GIS sources to verify | high |
| Nearshore channels | Generic reef/channel feature text only | Baseline context only | Medium | High | Add channel-corridor layer with source dates | Coastal engineering, bathymetry, hydrographic datasets | high |
| High-tide overtopping context | Not supported for Recife | Missing | Medium | High | Add tide/current adapter coverage after source review | Tide station/model sources to verify | high |
| Tide/current observations | Hawaii static adapter only | Missing | Medium | High | Extend water-movement planning beyond Hawaii after Phase 23 pattern review | Official Brazil tide/current sources to verify | medium |
| Turbidity / water clarity | Planned Phase 24 gap | Missing | High | High | Add turbidity/visibility layer before calibration | Satellite ocean color, local water-quality datasets to verify | high |
| Rainfall/runoff lookback | Warning field exists | Missing for this replay | Medium | Medium | Add source-timestamped rainfall lookback where available | Weather stations, official meteorological products | medium |
| SST/anomaly | SST field exists | Missing for this replay | Medium | Medium | Add source-timestamped SST context | Satellite SST products, official ocean products | medium |
| Urban human exposure | Human exposure field exists | Missing for this replay | Medium | High | Build beach-time-of-day exposure baselines | Public beach-use proxies, lifeguard staffing, tourism calendars | high |
| Swimming/bathing context | Generic swimming context exists | Available as incident activity context | Low | Medium | Keep as activity context; do not overfit | Source-attributed incident record | low |
| Bull-shark suitability | Generic species context exists in other regions | Piedade has CEMIT preliminary `tubarão-cabeça-chata` classification only | Medium | Medium | Plan Recife species suitability profile after cohort review | CEMIT and scientific/public regional literature | medium |
| Tiger-shark suitability | Generic species context exists in other regions | Boa Viagem has CEMIT preliminary `tubarão-tigre` classification only | Medium | Medium | Plan Recife species suitability profile after cohort review | CEMIT and scientific/public regional literature | medium |
| Telemetry / monitoring programs | No Recife ingestion | Missing | High | High | Plan future ingestion with licensing/privacy review | Pernambuco monitoring programs and public releases | high |

## Regional-Pack Planning Notes

A future Recife / Pernambuco pack should cover:

- Boa Viagem
- Piedade
- Candeias
- Olinda / Del Chifre
- reef-barrier habitat
- nearshore channels
- high-tide overtopping context
- urban human exposure
- bull-shark suitability
- tiger-shark suitability
- future telemetry ingestion from Pernambuco monitoring programs

The first version should be static/offline and source-dated. It should label habitat and historical layers as baseline context, not current observations.

## Do Not Tune Yet

These two incidents are important for replay and gap analysis, but they are not enough to justify broad scoring changes. Recommended order:

1. Build a 10-20 case Greater Recife cohort with quiet-day controls.
2. Add source-dated reef-barrier/channel habitat context.
3. Add tide/current and high-tide overtopping support where official sources permit.
4. Add turbidity/water-clarity support.
5. Add live observation and monitoring-program ingestion when governance is clear.
6. Review calibration only after the cohort and signal coverage improve.

## Current Interpretation

The paired replay shows that AI1SAD can represent incident-cluster separation when one event is already timeline-valid. It cannot yet represent Recife-specific water-state, visibility, exposure, or monitoring signals before the first event. That is a signal-coverage gap, not a reason to tune weights around a small cluster.

The species review should remain incident-specific: Piedade is the source-attributed bull-shark suitability case, Boa Viagem is the source-attributed tiger-shark suitability case, and the shared-corridor lift is species-agnostic recent-interaction context. The replay must not assume the same individual shark caused both incidents.
