# Hawaii Water Clarity Data Plan

This plan defines future ingestion for Hawaii water clarity, turbidity, sediment/runoff visibility, and surf-zone visibility context. Phase 24 starts with static/offline profiles only.

| Source candidate | Source format | Historic/current status | Intended adapter use | Later ingestion method | Freshness caveat | Attribution/licensing notes |
| --- | --- | --- | --- | --- | --- | --- |
| NOAA CoastWatch / ocean color | satellite product / gridded product | current-capable, not live in Phase 24 | broad water-clarity and turbidity proxy context | scheduled prefetch or reviewed adapter | cloud cover and nearshore resolution can limit usefulness | verify product-specific attribution and redistribution requirements |
| PacIOOS water-quality products | station, model, or gridded products where available | current-capable, not live in Phase 24 | Hawaii-first water-quality and visibility-relevant context | scheduled prefetch with source timestamps | product coverage may not map directly to surf-zone visibility | verify PacIOOS product terms |
| Hawaii beach water-quality datasets | agency dataset / reported observations | historic/current depending on product | nearshore water-quality context and public-health visibility caveats | reviewed dataset import or scheduled prefetch | sampling frequency may lag operational windows | verify Hawaii DOH or dataset-specific attribution requirements |
| Static reef-channel/runoff notes | reviewed baseline pack metadata | historic/static | baseline sediment/runoff and surf-zone visibility context | manual baseline curation | not current conditions | retain source notes and review dates |

## Ingestion Rules

- Begin with cached/pre-fetched source snapshots, not live scraping.
- Preserve source timestamp, product name, station or grid reference, and source URL.
- Store stale or missing data explicitly.
- Do not treat static clarity baselines as direct beach observations.
- Do not tune scoring around Cromwell's Beach or any single event.
- Keep private review notes out of public warning, surveillance, alert, and replay outputs.

## Validation Plan

- Compare static baseline outputs against future source snapshots.
- Maintain Cromwell timeline separation tests.
- Add quiet-day controls for south-shore Oahu.
- Review across a Hawaii replay cohort before calibration changes.
