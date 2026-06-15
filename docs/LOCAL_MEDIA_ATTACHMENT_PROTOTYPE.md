# Local Media Attachment Prototype

Phase 25D-C adds a local-only, metadata-only attachment prototype for drone and coastal observation evidence. Phase 25D-D hardens validation and documents upload-security gates before any binary upload work exists.

It is disabled by default and intended for local demo/review workflows only.

## Configuration

```text
MEDIA_ATTACHMENTS_ENABLED=false
MEDIA_ATTACHMENTS_STORAGE_ROOT=./data/media_attachments
```

Attachment write endpoints reject requests unless `MEDIA_ATTACHMENTS_ENABLED=true`.

`MEDIA_ATTACHMENTS_STORAGE_ROOT` is reserved for local private storage experiments and must not point inside tracked documentation, site, frontend public, or frontend build directories. `data/media_attachments/` is ignored by git.

## Scope

Implemented in Phase 25D-C:

- metadata-only attachment records
- local private filesystem backend label
- private-by-default review visibility
- public-safe summary field
- attachment review metadata
- API validation for media kind, visibility, review status, release status, MIME type, filenames, file size, checksum, timestamp, and confidence
- frontend metadata form in the Drone Operator Console

Hardened in Phase 25D-D:

- path traversal, absolute paths, Windows drive-root paths, and parent-directory references are rejected
- executable and script filename extensions are rejected
- unsupported media kinds, reference types, review visibility, review status, and public release statuses are rejected
- impossible file sizes, invalid checksums, malformed timestamps, and overlong summaries are rejected
- original filenames are treated only as private display metadata and are never used as storage paths

Not implemented:

- binary file upload
- file download
- cloud storage
- external URL fetching
- signed URLs
- computer vision
- media parsing
- species inference
- public attachment release
- autonomous flight control

## API Endpoints

```text
POST /api/v1/drone/observations/{observation_id}/attachments
GET /api/v1/drone/observations/{observation_id}/attachments
PATCH /api/v1/drone/observations/{observation_id}/attachments/{attachment_id}/review
```

All three endpoints are local-prototype endpoints and require `MEDIA_ATTACHMENTS_ENABLED=true`.

## Privacy Rules

Public feeds do not expose:

- `attachment_id`
- `storage_key`
- `stored_filename`
- `original_filename`
- local paths
- `checksum_sha256`
- `uploaded_by_role`
- private review notes
- raw media references

Attachment endpoint responses expose only safe metadata for local review. Storage keys, filenames, checksums, and uploader role are filtered from responses.

## Safety Rules

- Local attachments are private evidence records. They are not exposed in the public surveillance feed.
- AI1SAD does not analyze media, infer species, or create sightings from attachments.
- Do not upload sensitive media unless local attachment support is explicitly enabled.
- Attachments do not alter scoring.
- Attachments do not create sightings.
- Attachments do not change drone flight behavior.

## Known Limitations

- Metadata-only: no binary upload is implemented.
- No authentication model is implemented for attachment workflows.
- Public attachment release is not implemented.
- Local filesystem storage remains a prototype planning boundary, not production evidence storage.
- Binary upload remains blocked until a future phase defines authentication, malware scanning, EXIF/geotag stripping, retention, and public-release review.
