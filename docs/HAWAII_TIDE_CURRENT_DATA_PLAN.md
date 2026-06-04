# Hawaii Tide And Current Data Plan

This plan defines future ingestion for Hawaii tide, current, and nearshore water-movement context. Phase 23 starts with static/offline profiles only.

| Source candidate | Source format | Historic/current status | Intended adapter use | Later ingestion method | Freshness caveat | Attribution/licensing notes |
| --- | --- | --- | --- | --- | --- | --- |
| PacIOOS South Shore Oahu ROMS | model grid / forecast products | current-capable, not live in Phase 23 | preferred south-shore Oahu nearshore current baseline | scheduled prefetch or reviewed adapter | must retain model run time and age | verify PacIOOS attribution and redistribution requirements |
| PacIOOS Oahu ROMS | model grid / forecast products | current-capable, not live in Phase 23 | Oahu fallback when south-shore product is unavailable | scheduled prefetch or reviewed adapter | coarser than south-shore product | verify product-specific terms |
| PacIOOS Main Hawaiian Islands ROMS | model grid / forecast products | current-capable, not live in Phase 23 | regional fallback | scheduled prefetch or reviewed adapter | coarse regional context only | verify product-specific terms |
| NOAA CO-OPS | station observations and predictions | current-capable, not live in Phase 23 | supporting tide/current station checks | station adapter with explicit IDs and timestamps | station may not represent reef-channel microconditions | follow NOAA attribution guidance |

## Ingestion Rules

- Begin with cached/pre-fetched source snapshots, not live scraping.
- Preserve model run time, station timestamp, product name, and source URL.
- Store stale or missing data explicitly.
- Do not treat model baselines as direct beach observations.
- Do not tune scoring around Cromwell's Beach or any single event.

## Validation Plan

- Compare static baseline outputs against future source snapshots.
- Maintain Cromwell timeline separation tests.
- Add quiet-day controls for south-shore Oahu.
- Review across a Hawaii replay cohort before calibration changes.
