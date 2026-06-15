# Observation Analyst Review

## Overview

Phase 25D-A adds metadata-only analyst review fields to drone and coastal observations. An analyst can annotate an existing observation with review status, outcome, a public summary, and private notes — without modifying the original observation, without AI1SAD fetching or hosting media, and without creating a new sighting from media reference alone.

## Safety Boundaries

- Analyst review fields are metadata annotations only
- AI1SAD does not fetch, host, analyze, or serve media files
- `media_reference` is an optional external identifier stored as a reference only and excluded from public output by default
- `analyst_notes_private` is excluded from public feed output via `PUBLIC_DROP_FIELDS`
- `evidence_confidence` is bounded 0.0-1.0
- Analyst review does not create a sighting or change observation type
- The PATCH endpoint updates only analyst review fields on an existing observation

## Added Fields

### On Every Observation

| Field | Type | Description |
|---|---|---|
| `analyst_review_status` | string | Enum: `unreviewed`, `needs_review`, `in_review`, `reviewed`, `rejected`, `inconclusive` |
| `analyst_reviewed_at` | ISO timestamp or null | When the analyst review was performed |
| `analyst_reviewer_role` | string or null | Free-text role of the reviewer |
| `analyst_notes_private` | string or null | Analyst-only notes; never exposed in public output |
| `public_review_summary` | string or null | Public-safe summary of the review |
| `review_outcome` | string or null | Enum: `no_public_change`, `confirms_operator_observation`, `downgrades_operator_observation`, `upgrades_operator_observation`, `species_uncertain`, `false_positive`, `duplicate`, `unusable_media` |
| `evidence_confidence` | float or null | Analyst confidence in the media evidence, 0.0-1.0 |
| `media_reference_type` | string or null | Enum: `local_filename`, `drone_clip_id`, `camera_card_reference`, `external_url`, `agency_evidence_id`, `private_case_reference`, `none` |
| `media_timestamp` | ISO timestamp or null | When the media was captured |

### Private Fields (Excluded from Public Feed)

- `analyst_notes_private`
- `analyst_reviewer_role`
- `analyst_reviewed_at`
- `media_reference`
- `media_reference_type`
- `media_timestamp`

## API Endpoints

### PATCH `/api/v1/drone/missions/{mission_id}/observations/{observation_id}`

Updates analyst review fields on an existing observation.

Request body (partial):

```json
{
  "analyst_review_status": "reviewed",
  "review_outcome": "confirms_operator_observation",
  "public_review_summary": "Clip review confirms shark sighting",
  "analyst_notes_private": "Internal: follow up with operator",
  "evidence_confidence": 0.85
}
```

Response:

```json
{
  "status": "updated",
  "observation": { ... },
  "flight_control_commands_exposed": false
}
```

Validation:

- All enum values are validated server-side; unsupported types return 422
- `confidence` and `evidence_confidence` must be between 0 and 1; impossible values return 422
- Private fields and raw media references are filtered from public output

## Frontend

The Analyst Review panel appears in the Drone Operator Console below the recent observations list. It surfaces observations with `analyst_review_status` of `unreviewed`, `needs_review`, or `in_review`.

The review card includes:

- Review status dropdown (all `ANALYST_REVIEW_STATUSES`)
- Outcome dropdown (all `REVIEW_OUTCOMES`)
- Public review summary textarea
- Private notes textarea with a visible warning that notes are never public
- Submit button

## Related Documents

- [Media Attachment Storage Design](MEDIA_ATTACHMENT_STORAGE_DESIGN.md) — design and privacy review for future evidence attachment workflows

## Testing

- Backend: PATCH endpoint validates enums, filters private fields and raw media references, and does not create sightings from media references
- Frontend: panel renders pending observations, dropdowns contain valid enum values, private notes warning is visible, and raw media references are hidden from public cards
