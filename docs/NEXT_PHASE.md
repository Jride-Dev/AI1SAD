# Next Phase

## Phase 25D-D: Media Attachment Security Review and Upload Hardening

## Objective

Review the Phase 25D-C local-only metadata prototype and define the security controls required before any binary media upload path is added.

Do not start this phase automatically. Phase 25D-D begins only after Phase 25D-C is reviewed and committed.

## Current Baseline

Phase 25D-C provides:

- metadata-only attachment records
- `MEDIA_ATTACHMENTS_ENABLED=false` by default
- local private filesystem backend label
- no binary upload
- no cloud storage
- no external media fetch
- no computer vision
- no public media exposure
- no scoring or replay changes

## Review Scope

1. Confirm attachment endpoints are gated by `MEDIA_ATTACHMENTS_ENABLED`.
2. Confirm public feeds never expose private attachment fields.
3. Confirm path traversal and unsafe filenames are rejected.
4. Confirm MIME-type and file-size metadata validation is bounded.
5. Confirm attachments do not create sightings or alter scores.
6. Define upload-hardening requirements before any binary upload is implemented.

## Upload-Hardening Questions

Before adding upload support, decide:

- maximum file sizes by media kind
- accepted MIME types and extension mapping
- malware scanning strategy
- EXIF/geotag stripping strategy
- retention and deletion policy
- local storage root isolation rules
- audit logging fields
- role/auth model for attachment create/list/review
- public release and redaction workflow
- whether upload remains local-only or stays deferred

## Safety Boundaries

- Do not add cloud storage.
- Do not add external media APIs.
- Do not fetch or download external media.
- Do not add computer vision.
- Do not parse media for species or sightings.
- Do not expose private media paths in public feeds.
- Do not change scoring weights.
- Do not modify replay outputs.
- Do not add autonomous flight control.
- Do not add MAVLink command behavior.
- Do not add public media release without a separate review gate.

## Validation Expectations

- focused attachment tests
- focused drone observation tests
- full backend tests
- frontend tests
- frontend build
- npm audit high
- mkdocs build
- README link/image check
- secret scan
- prohibited-language scan
- git diff --check

## Review Gate

Stop before committing unless explicitly asked to commit Phase 25D-D work.
