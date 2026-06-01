# Kelp Forest Provider

AI1SAD uses kelp forest habitat as bounded environmental context for operational monitoring. The first implementation is static/offline only. It does not call live canopy APIs, scrape maps, or infer animal intent.

## Provider

`app/providers/kelp_forest.py` emits normalized Signal-shaped records from static kelp habitat profiles.

Provider id:

```text
kelp_forest_static
```

Dataset:

```text
static_manual_kelp_forest_profiles
```

## Signal Types

- `kelp_forest_presence`
- `kelp_density_context`
- `kelp_edge_habitat`
- `kelp_prey_overlap`
- `white_shark_kelp_hunting_context`

## Profile Shape

Each static profile includes:

- region
- center coordinates
- `density_class`: `sparse`, `moderate`, `dense`, or `optimal_edge`
- canopy confidence
- data freshness note
- known prey association
- pinniped presence and context
- human activity overlap notes
- source notes
- pack association

## Initial Profiles

- Central California kelp and white shark habitat demo
- Monterey Bay / Central Coast kelp demo
- South Africa False Bay / Seal Island kelp context
- Western Australia reef and kelp context
- Golden rule kelp bed demo, clearly marked synthetic

## Scoring Boundary

Kelp is not a standalone high-warning signal.

- Sparse kelp has low influence.
- Moderate and edge kelp are contextual.
- `optimal_edge` has the strongest habitat effect, but remains bounded.
- Dense kelp can reduce open-water visibility confidence instead of automatically increasing warning.
- Kelp plus pinniped context can raise surveillance priority.
- Kelp plus spearfishing, diving, or surfing can raise operational attention.

The warning engine applies only a small kelp context score. The surveillance engine gives kelp more influence when it stacks with edge habitat, prey, activity, or white shark regional context.

## Freshness

Static kelp profiles are marked stale by design. They remain useful as habitat context, but current canopy extent should be verified before operational use. Future seasonal or current canopy observations can increase confidence without changing the static provider contract.

## Public Safety Language

Kelp outputs must not be described as attack probability, individual prediction, or shark intent. They are habitat and observation-planning context only.
