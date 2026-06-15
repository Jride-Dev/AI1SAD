# Next Phase

## Phase 25D-C: Local-Only Media Attachment Prototype (Not Started)

## Objective

Build a local-only media attachment prototype for drone/coastal observations using the filesystem-based design documented in Phase 25D-B.

Phase 25D-C should build on Phase 25D-A review metadata and Phase 25D-B storage design without adding cloud storage, computer vision, or autonomous flight control.

## Phase 25D-B Completion Note

Phase 25D-B is a planning-and-documentation phase:

- `docs/MEDIA_ATTACHMENT_STORAGE_DESIGN.md` documents the full attachment model, storage backend tradeoffs, privacy visibility levels, public-feed rules, security review checklist, and implementation gates
- No storage clients, upload endpoints, database migrations, or frontend upload UI are added
- Updated: README, OBSERVATION_ANALYST_REVIEW.md, DRONE_OPERATOR_CONSOLE.md, DRONE_DATA_CONTRACT.md, DRONE_OPERATIONS_SAFETY.md, CURRENT_DATA_SOURCES.md, PROJECT_STATUS.md, NEXT_PHASE.md, mkdocs.yml
- MkDocs navigation includes the new design document
- No code changes

## Planned Scope (Future Phase)

1. Local filesystem-based media storage within `data/` directory
2. Upload endpoint for attaching media to existing observations
3. Media kind and MIME type validation
4. Server-side EXIF/geotag stripping before storage
5. Private-bucket semantics for local filesystem (no public access path)
6. Attachment metadata stored alongside observation records
7. Frontend media reference display (no upload UI yet)
8. Public-feed filtering for attachment metadata based on visibility level
9. Configuration flag to disable upload (`MEDIA_UPLOAD_ENABLED=false`)

## Constraints

- Do not add cloud storage (S3, Supabase Storage, Cloudinary, etc.)
- Do not add computer vision
- Do not add species detection from media
- Do not add autonomous flight control
- Do not transmit MAVLink commands
- Do not add DJI-specific dependencies
- Do not change auth/billing
- Do not change scoring weights
- Do not modify replay outputs
- Do not commit until review

## Validation Expectations

- focused drone observation tests
- focused attachment storage tests
- frontend tests
- frontend build
- full backend test suite
- mkdocs build
- secret scan
- prohibited-language scan

## Review Gate

Do not begin Phase 25D-C until Phase 25D-B has been reviewed and either committed or explicitly set aside.
