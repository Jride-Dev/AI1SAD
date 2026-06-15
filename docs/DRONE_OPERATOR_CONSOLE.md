# Drone Operator Console

Phase 25C adds a local frontend console for human-entered coastal and drone patrol observations. Phase 25D-A adds metadata-only analyst review fields. Phase 25D-B documents the media attachment storage design and privacy review for future evidence workflows.

The console is observation intake only. It does not control aircraft, transmit MAVLink commands, upload waypoints, run computer vision, or infer sightings from telemetry alone.

Required operating invariant:

```text
AI1SAD recommends missions.
Humans approve missions.
Drone operators fly missions.
AI1SAD ingests observations.
```

## Local Route

Frontend route:

```text
http://localhost:5174/drone-console
```

The page is available from the local dashboard navigation as **Drone Console**.

## What Operators Can Record

The console supports source-attributed, human-entered observation types:

- shark sighting
- unknown large marine animal
- no-sighting patrol
- carcass
- baitfish congregation
- marine mammal activity
- poor visibility
- surf-line activity
- swimmer density
- vessel activity
- other

`OTHER` is accepted as a generic observation type and remains bounded context. It does not create a shark sighting.

## Required Fields

- mission ID
- observation type
- observed timestamp
- latitude
- longitude
- observer role
- visual confidence
- provenance

The console maps these fields onto the existing drone observation endpoint:

```text
POST /api/v1/drone/missions/{mission_id}/observations
```

## Optional Fields

- estimated size
- estimated count
- species guess
- species confidence
- behavior notes
- visibility notes
- surf-zone notes
- media reference
- operator notes
- public summary

Species guesses are stored as provisional operator metadata. They are not official species classifications.

Media references are references only in Phase 25C. The console does not upload images or video.

## Mission And Telemetry Context

The console reuses existing mission and feed routes:

```text
GET /api/v1/drone/missions/{mission_id}
GET /api/v1/drone/missions/{mission_id}/observations
GET /api/v1/drone/active-observations
GET /api/v1/drone/surveillance-feed
```

If the read-only MAVLink bridge has posted telemetry to a mission, that telemetry remains mission context only. Telemetry alone never creates an observation or sighting.

## Safety Copy

The UI states:

```text
AI1SAD records human observations and recommends surveillance attention. It does not control aircraft or predict individual shark attacks.
```

For no-sighting patrols:

```text
No-sighting patrols reduce uncertainty only within the observed patrol area, time window, and visibility conditions. They do not prove an area is safe.
```

For species guesses:

```text
Species guesses are provisional unless confirmed by an official source or qualified review.
```

## Demo And Live Behavior

Demo fixtures are available only when frontend mock mode is explicitly enabled.

In live mode, backend failures and validation errors are shown to the operator. The console does not silently switch to mock data after a failed live request.

Drone write endpoints remain disabled unless:

```text
DRONE_INGEST_ENABLED=true
```

## Public Feed Filtering

Public feed output remains map-ready and public-safe. Internal/operator notes and raw media references are not exposed through public response paths.

The console displays recent feed items with:

- observation type
- timestamp
- coordinates
- confidence
- public/private visibility marker when available
- provenance or source label

Raw `media_reference`, `media_reference_type`, and `media_timestamp` values are hidden from public feed cards. Future attachment-release rules can add public-safe media summaries without exposing private filenames, case references, or storage paths.

## Analyst Review Panel

Phase 25D-A adds an Analyst Review panel below the recent observations list. The panel surfaces observations with `analyst_review_status` of `unreviewed`, `needs_review`, or `in_review`.

Each review card includes:

- Review status dropdown (unreviewed, needs_review, in_review, reviewed, rejected, inconclusive)
- Outcome dropdown (no_public_change, confirms_operator_observation, downgrades_operator_observation, upgrades_operator_observation, species_uncertain, false_positive, duplicate, unusable_media)
- Public review summary textarea
- Private notes textarea with a visible warning that analyst notes are never public
- Submit button

The PATCH endpoint is used to submit review updates:

```text
PATCH /api/v1/drone/missions/{mission_id}/observations/{observation_id}
```

Private notes and reviewer role are not returned in public feed output.

See [Observation Analyst Review](OBSERVATION_ANALYST_REVIEW.md).

## Media Attachment Design

Phase 25D-B documents the media attachment storage design and privacy review. Current implementation stores review metadata and evidence pointers only; it does not upload, host, fetch, or analyze media. Future attachment support is design-documented in the [Media Attachment Storage Design](MEDIA_ATTACHMENT_STORAGE_DESIGN.md) document, which covers the attachment model, storage backend options, privacy model, public-feed rules, security checklist, and implementation gates. No storage implementation is included in Phase 25D-B.
