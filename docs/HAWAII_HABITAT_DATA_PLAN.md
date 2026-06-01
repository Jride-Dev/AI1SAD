# Hawaii Habitat Data Plan

This planning note defines how static Hawaii habitat baselines should be prepared for future ingestion workflows.

## Candidate Sources

| Source candidate | Source format | Historic/current status | Intended adapter use | Future ingestion method | Freshness caveat | Licensing/attribution to verify |
| --- | --- | --- | --- | --- | --- | --- |
| NOAA NCCOS Oahu shallow-water benthic habitat maps | GIS layers, metadata, map products | Historic/static baseline | Oahu nearshore structure and benthic-class baseline | Offline preprocessing to canonical static profiles | Not live observations; retain source date | Confirm redistribution terms and attribution text |
| Hawaii Statewide GIS benthic-habitat layer | State GIS dataset/layer | Historic/static baseline | Statewide baseline coverage and fallback profiles | Periodic offline export and profile regeneration | Source date must be preserved and surfaced | Verify state dataset licensing and map credits |
| Pacific Islands Benthic Habitat Mapping Center Oahu resources | Bathymetry, optical validation, shapefiles, metadata | Historic/static baseline | Channel/edge/depth context enrichment | Offline conversion pipeline with schema checks | Validation period may differ by sub-layer | Verify PIBHMC use rights and attribution requirements |

## Adapter Usage Boundary

- Use as baseline habitat context only.
- Do not present these layers as current conditions.
- Keep influence bounded and stack-dependent.

## Future Ingestion Steps (Later)

1. Acquire source metadata and license terms.
2. Normalize geometry and classification names into AI1SAD profile schema.
3. Preserve source date, source name, and attribution fields.
4. Export static profile bundle for offline runtime use.
5. Add versioned snapshot metadata and changelog notes.

## Redistribution and Attribution Checklist

- Confirm license allows redistribution in docs/assets/runtime bundles.
- Confirm attribution wording and citation links.
- Confirm update cadence and source retirement policy.
