# Media Attachment Storage Design

## 1. Purpose

This document describes the future design for attaching media evidence to drone and coastal observations.

Phase 25D-A added metadata-only analyst review fields: media reference types, review status, review outcome, public review summary, private analyst notes, and evidence confidence. Phase 25D-B takes the next step: a planning and privacy-review phase that defines what media attachment support will eventually need, what storage boundaries must exist, and what must remain private.

The design is metadata-first. Phase 25D-C implements a local-only metadata prototype for attachment records behind `MEDIA_ATTACHMENTS_ENABLED=false` by default. It does not upload, host, fetch, download, parse, or analyze media.

## 2. Non-Goals for Current Phase

Phase 25D-B does not implement media handling:

- No file uploads
- No file downloads
- No external URL fetching
- No computer vision
- No species detection from media
- No autonomous detections from media
- No public release of private evidence
- No database migrations
- No storage client code
- No frontend upload UI

## 3. Attachment Model Proposal

Phase 25D-C metadata-only attachment records use this model as a local prototype. Binary storage and public release remain future work.

| Field | Type | Description |
|---|---|---|
| `attachment_id` | string | UUID for the attachment record |
| `observation_id` | string | Link to parent observation |
| `mission_id` | string | Link to parent mission |
| `storage_backend` | string | Which backend holds the file: `local`, `s3`, `supabase`, `agency_reference`, `external_url` |
| `storage_key` | string | Opaque key or path within the backend |
| `original_filename` | string | Original filename; never exposed in public output |
| `media_kind` | string | Enum: `image`, `video`, `telemetry_snapshot`, `observation_note`, `agency_report_reference`, `unknown` |
| `mime_type` | string | MIME type of the stored file |
| `file_size_bytes` | integer | File size in bytes |
| `captured_at` | ISO timestamp | When the media was originally captured |
| `uploaded_at` | ISO timestamp | When the media was uploaded to storage |
| `uploaded_by_role` | string | Role of the uploader: `operator`, `analyst`, `agency` |
| `review_visibility` | string | Visibility level for the review context |
| `public_release_status` | string | Enum: `not_reviewed`, `approved_public`, `approved_analyst_only`, `restricted`, `retained` |
| `retention_policy` | string | Retention rule identifier |
| `checksum_sha256` | string | SHA-256 hash for integrity verification |
| `redaction_status` | string | Enum: `not_required`, `pending`, `completed`, `exempt` |
| `chain_of_custody_note` | string | Optional provenance note for evidence handling |
| `evidence_confidence` | float | Analyst confidence in the media evidence, 0.0-1.0 |
| `analyst_review_status` | string | Review status for the attachment (extends observation-level review) |
| `public_summary` | string | Public-safe description of the media content |

The model keeps attachments separate from observation records. An observation may have zero, one, or multiple attachments. Private attachment fields are never included in public feed output.

## 4. Allowed Future Media Kinds

| Media Kind | Description |
|---|---|
| `image` | Still image from drone, phone, or camera |
| `video` | Video clip from drone or handheld camera |
| `telemetry_snapshot` | Still frame or data overlay from drone telemetry |
| `observation_note` | Text note submitted alongside media (already supported as metadata) |
| `agency_report_reference` | Pointer to an external agency report or evidence file |
| `unknown` | Fallback when media kind is not yet classified |

## 5. Future Storage Backend Options

The following backends are documented for future review. None are implemented.

### Local Private Filesystem (Lab/Demo Use)

- Works within the repo's `data/` directory, excluded from git via `.gitignore`
- No authentication required during local development
- Not suitable for multi-user or deployed environments
- No automatic backup or replication
- Retention is manual

### Supabase Storage

- Integrates with existing Supabase project if adopted
- Provides per-bucket access policies and signed URLs
- Supports public/private bucket separation
- Requires Supabase service key for server-side uploads
- Signed URLs limit public exposure window
- Vendor dependency; migration path must be considered

### S3-Compatible Storage

- Standard object storage (AWS S3, MinIO, DigitalOcean Spaces, etc.)
- Presigned URLs for controlled access
- Bucket policies for public/private separation
- Lifecycle rules for automated retention and deletion
- Broad industry support; no vendor lock-in for S3 API
- Requires AWS SDK or S3 client library integration

### Agency-Owned Storage Reference Only

- AI1SAD stores only a reference (URL or identifier) to media hosted by an external agency
- AI1SAD does not fetch, cache, or host the media
- Access control is the agency's responsibility
- Reference must include a provenance note
- No storage client code needed on the AI1SAD side

### External URL Reference Only

- Similar to the existing `media_reference` field
- URL is metadata only; AI1SAD does not fetch or validate the URL
- Appropriate for public web sources when attribution is clear
- Risk: URL may become stale; no AI1SAD retention control
- Public feed must not expose private URLs

## 6. Privacy Model

Each attachment carries a visibility level that determines where the attachment metadata and storage reference may appear.

| Visibility Level | Description |
|---|---|
| `private_internal` | Visible only to system internals; never returned in any API response |
| `analyst_only` | Visible only in analyst-review API responses; excluded from public and operator feeds |
| `operator_visible` | Visible to operator console and analyst review; excluded from public feed |
| `public_summary_only` | Only the public-safe summary and public_release_status appear in public feed; storage key and filename are never exposed |
| `public_attachment_allowed` | Attachment metadata and public-safe fields appear in public feed when release is approved |

Default visibility for new attachments is `analyst_only`. Public release requires explicit analyst approval.

Phase 25D-C does not support `public_attachment_allowed`; that visibility remains a future design concept pending security review.

## 7. Public-Feed Rules

Public feed responses must never expose:

- Raw private media URLs or signed URLs intended for internal use
- Storage keys or backend paths (`storage_key`)
- Original private filenames (`original_filename`)
- Analyst private notes (`analyst_notes_private`)
- Operator private notes (`internal_notes`)
- Unreviewed evidence attachments
- Internal evidence IDs
- Precise sensitive coordinates beyond the current public-feed coordinate precision rules
- Any attachment with `review_visibility` of `private_internal`, `analyst_only`, or `operator_visible`
- Chain-of-custody notes
- Redaction status details
- Upload timestamps when they reveal operational patterns

Allowed in public feed (when explicitly released):

- `public_summary`
- `public_release_status` (limited to `approved_public`)
- `media_kind` (non-sensitive)
- `captured_at` (if not revealing operational patterns)
- `evidence_confidence` (same bounds as existing observation field)

## 8. Review Workflow

Future review workflow for observations with media attachments:

1. Operator submits observation with optional media reference
2. Optional: operator or analyst uploads media to storage
3. Analyst reviews evidence in the Analyst Review panel
4. Analyst sets `analyst_review_status` and `review_outcome`
5. Analyst writes `analyst_notes_private` (never public)
6. Analyst writes `public_review_summary` (public-safe)
7. Analyst optionally sets `evidence_confidence` (0.0-1.0)
8. Analyst sets `public_release_status` to control whether attachment metadata appears in public feed
9. Public feed receives only safe fields and approved attachments
10. Private attachment metadata and storage references remain excluded

Phase 25D-C adds local metadata-only attachment endpoints for creating attachment records and updating attachment review metadata. A future multipart upload path would be needed before binary storage is implemented.

## 9. Security Review Checklist

Before any storage implementation is enabled, the following must be reviewed:

- **File type restrictions**: Only allow known-safe MIME types; reject executables, scripts, archives, and unknown types
- **Max file size**: Enforce a configurable per-file size limit (e.g., 10 MB for images, 50 MB for video)
- **Malware scanning**: Integrate with a server-side AV scanner or reject uploads until scanning is available
- **Signed URLs**: Use time-limited signed URLs for access to private storage; never expose permanent storage keys
- **Private buckets**: Store all uploads in private buckets by default; public buckets only for explicitly approved media
- **Retention policy**: Define how long media is retained; automated deletion via lifecycle rules or scheduled tasks
- **Audit trail**: Log all upload, access, review, and deletion events with timestamp and actor identity
- **Access control**: Restrict upload and access to authenticated roles; no anonymous upload or read
- **Public-redaction review**: Require human review before any attachment is marked public_release_status=approved_public
- **Metadata leakage review**: Strip EXIF, geotags, device info, and software metadata from uploaded images before storage
- **EXIF/geotag handling**: Strip all embedded metadata client-side or server-side before storage; do not store raw EXIF
- **Deletion policy**: Support soft-delete with configurable grace period before hard deletion; log all deletions
- **Rate limiting**: Limit upload frequency per mission, per operator, and per observation

## 10. Implementation Gates

Before future storage implementation is enabled:

1. Decide which storage backend to support (local, S3, Supabase, or combination)
2. Decide the auth model (API key, bearer token, or session-based for uploads)
3. Decide retention policy (how long, automated deletion rules, archival strategy)
4. Decide public redaction rules (who approves, what fields are safe)
5. Decide storage migration pattern (how to move between backends)
6. Decide local/demo fallback (filesystem-based for development, no external dependency)
7. Write tests before enabling upload (unit tests for storage abstraction, integration tests for each backend)
8. Keep upload disabled by default behind a configuration flag (e.g., `MEDIA_UPLOAD_ENABLED=false`)
9. Review security checklist items before any deployment that enables upload
10. Document the upload API contract, error responses, and rate limits

## 11. Safety Boundaries

- Media does not create sightings by itself. An observation must exist before media metadata can be attached.
- Media does not create autonomous detections. AI1SAD does not run computer vision on uploaded media.
- Media does not infer species automatically. Species classification remains a human-reviewed analyst action.
- AI1SAD does not control drones. Media attachment is an observation-ingestion feature, not a flight-control feature.
- AI1SAD does not predict individual attacks. Media evidence supports human review; it does not change the system's safety boundaries.
- Private media is never exposed in public feed output.
- Storage keys and backend paths are never exposed in any API response.
