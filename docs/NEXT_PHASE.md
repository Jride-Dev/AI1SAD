# Next Phase

## Phase 25E: UAV Operator Research Brief and Compatibility Matrix

## Objective

Create a research brief and compatibility matrix for human-operated UAV workflows that could feed AI1SAD observation records without adding aircraft control, cloud storage, computer vision, or vendor lock-in.

Do not start this phase automatically. Phase 25E begins only after Phase 25D-D is reviewed and committed.

## Current Baseline

Phase 25D-D should leave AI1SAD with:

- metadata-only local attachment records
- `MEDIA_ATTACHMENTS_ENABLED=false` by default
- stricter path, filename, MIME, checksum, timestamp, file-size, and enum validation
- no binary upload
- no cloud storage
- no external media fetch
- no computer vision
- no media-based species or sighting inference
- no public media exposure
- no scoring or replay changes

## Research Scope

1. Identify common human-operated UAV workflows for coastal observation.
2. Compare consumer, prosumer, agency, and open telemetry workflows at the documentation level.
3. Document what AI1SAD can ingest safely today:
   - mission metadata
   - human-entered observations
   - no-sighting patrol results
   - read-only telemetry replay
   - private attachment metadata
4. Document what remains out of scope:
   - autonomous aircraft control
   - MAVLink command transmission
   - DJI control dependencies
   - computer vision detections
   - binary media upload
   - cloud media hosting
5. Produce a compatibility matrix for:
   - manual console entry
   - CSV/JSON observation export
   - read-only MAVLink telemetry
   - agency evidence IDs
   - local private filename references
   - future upload-ready workflows

## Safety Boundaries

- Do not add flight-control code.
- Do not arm, take off, land, upload waypoints, change missions, or use offboard control.
- Do not add cloud storage.
- Do not add external media APIs.
- Do not fetch or download external media.
- Do not add computer vision.
- Do not infer species or sightings from media.
- Do not expose private media paths in public feeds.
- Do not change scoring weights.
- Do not modify replay outputs.

## Expected Artifacts

- UAV operator research brief
- compatibility matrix
- safety boundary summary
- recommended ingestion patterns for human-approved operations
- documentation links from README and MkDocs if a new page is added

## Validation Expectations

- mkdocs build
- README link/image check if README changes
- secret scan
- prohibited-language scan
- backend/frontend tests only if code changes occur

## Review Gate

Stop before committing unless explicitly asked to commit Phase 25E work.
