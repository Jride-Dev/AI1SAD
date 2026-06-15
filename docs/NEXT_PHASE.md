# Next Phase

## Phase 25D-B: Future Media Reference Expansion (Not Started)

## Objective

Future expansion of media reference support for drone/coastal observations beyond the current metadata-only analyst review fields added in Phase 25D-A.

## Phase 25D-A Completion Note

Phase 25D-A adds metadata-only analyst review fields:

- `MEDIA_REFERENCE_TYPES`, `ANALYST_REVIEW_STATUSES`, `REVIEW_OUTCOMES` enum sets
- `analyst_review_status`, `review_outcome`, `public_review_summary`, `analyst_notes_private`, `evidence_confidence`, `media_reference_type`, `media_timestamp` on observations
- PATCH `/api/v1/drone/missions/{mission_id}/observations/{observation_id}` endpoint
- `analyst_notes_private`, `analyst_reviewer_role`, `analyst_reviewed_at` excluded from public output via `PUBLIC_DROP_FIELDS`
- AnalystReviewPanel component in Drone Operator Console
- No computer vision, media upload/hosting, autonomous flight control, scoring-weight changes, or replay-output changes

## Planned Scope (Future Phase)

1. Media storage design (privacy, retention, access rules reviewed)
2. Media upload or external-hosted-reference support
3. Enhanced analyst review UI with media preview
4. Any expanded scoring or signal integration from reviewed media

## Constraints

- Do not tune scoring weights
- Do not add attack-probability language
- Do not infer shark intent
- Do not add autonomous takeoff, landing, waypoint, or offboard-control commands
- Do not transmit MAVLink commands
- Do not add DJI-specific dependencies
- Do not add computer vision
- Do not upload or host media until storage, privacy, and retention rules are reviewed
- Do not change auth/billing
- Do not commit until review

## Validation Expectations

- focused drone observation tests
- frontend tests
- frontend build
- full backend test suite
- mkdocs build
- secret scan
- prohibited-language scan

## Review Gate

Do not begin Phase 25D-B until Phase 25D-A has been reviewed and either committed or explicitly set aside.
