# Hawaii Habitat Provider

AI1SAD includes a static/offline Hawaii habitat adapter for bounded structural context. It does not ingest live habitat feeds at runtime.

Provider module: `app/providers/hawaii_habitat.py`

## Purpose

Represent baseline nearshore structure context for surveillance planning:

- reef-channel
- shallow reef
- reef edge
- hardbottom
- submerged vegetation
- sandy bottom
- dropoff
- nearshore structure
- habitat visibility context

These are historic/static baseline layers, not real-time observations.

## Source Direction (Baseline Candidates)

1. NOAA NCCOS Oahu shallow-water benthic habitat maps
2. Hawaii Statewide GIS benthic-habitat layer
3. Pacific Islands Benthic Habitat Mapping Center Oahu resources

Source dates are retained in metadata and must not be represented as current conditions.

## Signal Types

- `reef_channel_habitat`
- `shallow_reef_habitat`
- `reef_edge_habitat`
- `hardbottom_habitat`
- `submerged_vegetation_habitat`
- `sandy_bottom_habitat`
- `dropoff_habitat`
- `nearshore_structure_context`
- `habitat_visibility_context`

## Profile Fields

Each static profile includes:

- `id`
- `region`
- `island`
- `location_name`
- coordinates and polygon reference
- `habitat_type`
- `geomorphology_type`
- `biological_cover_type`
- `depth_band_m`
- `edge_context`
- `channel_context`
- `visibility_context`
- `confidence`
- `source_name`
- `source_url_reference` and/or `source_notes`
- `source_date`
- `data_freshness`
- `baseline_only: true`
- `pack_id`
- `visibility`

## Bounded Behavior

- Habitat alone must not create high warning.
- Reef-channel and edge context can modestly raise surveillance attention.
- Stronger attention requires stacked activity/sighting/biological/weather/SST/exposure context.
- Historic baselines influence interpretation only and should reduce confidence when stale.

## Privacy and Output Safety

- Public outputs exclude `private_notes` and `restricted` fields.
- Baseline metadata is public-safe and source-attributed.

## Operational Caveat

Historic GIS baselines are structural reference layers only. They are not live water-state, animal-presence, or current-condition observations.
