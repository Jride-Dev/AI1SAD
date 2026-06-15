# UAV Operator Feedback Intake

Phase 25F adds a structured feedback-intake and field-requirements tracker for UAV operators, lifeguards, coastal authorities, researchers, agency staff, citizen scientists, and shark-surveillance teams.

Feedback records are research inputs only. They are not live surveillance observations.

## Purpose

The feedback intake helps AI1SAD learn which field workflows real teams use:

- drone platform and model
- flight app or operating workflow
- telemetry availability and export format
- media/video reference workflow
- whether no-sighting patrols are logged
- observation fields currently recorded
- privacy and airspace constraints
- operator pain points
- requested features
- suggested observation categories
- source attribution notes

## API Endpoints

```text
POST /api/v1/uav/operator-feedback
GET /api/v1/uav/operator-feedback
PATCH /api/v1/uav/operator-feedback/{feedback_id}/status
```

These endpoints store requirements and research feedback. They do not create sightings, warnings, public alerts, replay facts, or surveillance feed entries.

## Frontend Route

```text
http://localhost:5174/uav-feedback
```

The frontend page is labeled **UAV Feedback**.

Required UI copy:

```text
Feedback records are research inputs, not live surveillance observations.
Submitting feedback does not create a sighting, warning, or public alert.
Contact details are optional and private by default.
```

## Public And Private Fields

Private/internal fields:

- `contact_reference`
- `internal_notes_private`
- `reviewed_at`
- `reviewer_role`
- private operator identifiers

Public-safe fields may include:

- `submitter_role`
- `organization_type`
- `region`
- `country`
- `drone_platform`
- `flight_app`
- `telemetry_available`
- `media_workflow`
- `public_summary`
- `requirements_tags`
- `review_status`

The public-safe helper strips contact references, private notes, reviewer role, and review timestamps.

## Validation

Feedback validation rejects:

- unsupported submitter role, organization type, telemetry availability, media workflow, or review status
- overlong notes, contact references, summaries, regions, and countries
- unsafe URL schemes in contact references
- raw secrets, API keys, or tokens
- contact details in public summaries
- malformed region/country characters

Real contact information is optional and is private by default when supplied.

## Safety Boundaries

- Feedback does not alter warning scores.
- Feedback does not create sightings.
- Feedback does not create public alerts.
- Feedback does not create replay facts.
- Feedback does not appear in public surveillance feeds.
- Feedback does not trigger drone operations.
- Feedback does not imply endorsement from any agency, operator, researcher, or lifeguard service.
- Feedback does not add drone SDK integrations, cloud storage, media upload, computer vision, autonomous flight control, or MAVLink command behavior.

## Review Status

Allowed review statuses:

- `new`
- `triaged`
- `needs_follow_up`
- `accepted_requirement`
- `rejected`
- `archived`

The status PATCH endpoint updates review metadata only. It does not promote feedback into operational data.

## Known Limitations

- There is no separate review dashboard in Phase 25F.
- There is no authentication or role model for field-feedback workflows yet.
- Feedback remains a research/requirements input until future phases define review and prioritization workflows.
- Phase 25G should add a feedback review dashboard and requirements prioritization view.
