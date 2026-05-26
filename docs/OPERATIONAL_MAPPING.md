# Operational Mapping

Phase 14 adds an operational map layer to the AI1SAD frontend dashboard.

The map is a visualization surface only. It does not calculate warning scores, surveillance priority, activity hazard, alert levels, confidence, or model rules in the browser.

## Purpose

Operational mapping helps users see where AI1SAD recommends surveillance attention and why.

The map is intended for:

- drone/search planning review
- lifeguard or beach-manager situational awareness
- replay validation walkthroughs
- public demo explanation
- researcher review of model outputs

It is not an attack prediction map, beach closure authority, shark-intent inference system, or replacement for local agencies.

## Map Layers

The frontend can display these API-backed layers:

- `surveillance_priority_score`
- `warning_score`
- `activity_hazard_score`
- active alerts
- replay heatmap cells
- demo scenario points

Replay heatmap cells use `surveillance_priority_score` as the primary value. `warning_score` and `activity_hazard_score` remain secondary context.

## Demo Scenarios

The scenario selector includes:

- Horseshoe Reef 2026
- Queensland Spearfishing 2026
- Florida inlet/crowded beach
- Hawaii October tiger shark context
- Red Sea anomaly context

When the backend is unavailable, mock data preserves the same visual states so the dashboard can still demonstrate the operational split between general warning, activity hazard, and surveillance priority.

## Why This Zone?

Clicking a zone, heatmap cell, alert marker, or demo scenario point opens the explanation panel with:

- coordinates
- active pack
- `warning_score`
- `activity_hazard_score`
- `surveillance_priority_score`
- dominant factors
- factor contributions
- confidence breakdown
- recommended action
- recommended surveillance pattern
- disclaimer

This panel consumes backend explanation and replay output fields. It does not recalculate factor contributions or model results.

## Low Warning / High Surveillance Split

Some operational cases may show low general warning and high surveillance priority.

That is not contradictory. In AI1SAD:

- `warning_score` describes environmental and live-condition stack strength
- `activity_hazard_score` describes risk introduced by what people are doing in context
- `surveillance_priority_score` describes where safety teams may want to look first

The map labels these cases as activity/habitat-specific surveillance priority.

## Legend

The legend uses:

- low
- moderate
- elevated
- high
- urgent surveillance

Colors are visual labels only. Score values and bands still come from backend API responses.

## Safety Boundary

AI1SAD estimates environmental and surveillance-relevant shark encounter conditions. It does not predict individual attacks or guarantee safety outcomes.
