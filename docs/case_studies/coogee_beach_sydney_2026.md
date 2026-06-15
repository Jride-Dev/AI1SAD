# Coogee Beach Sydney 2026 Replay

This case study adds a timeline-separated replay for the June 13, 2026 Coogee Beach shark incident in Sydney's eastern suburbs, New South Wales, Australia.

## Source-Attributed Event Record

- Location: Coogee Beach, Sydney eastern suburbs, NSW, Australia
- Date: 2026-06-13
- Victim context: 35-year-old woman
- Activity: swimming
- Distance offshore: approximately 30 m
- Outcome: critical but stable, with serious arm and leg injuries
- Shark size: reported 3-4 m
- Species context: suspected white shark, source-attributed preliminary only
- Authority response: Coogee and nearby eastern-suburbs beach closures after the incident
- Drone context: drone/helicopter surveillance increased; ordinary drone monitoring is constrained by Sydney Airport flight-path restrictions, with emergency use or exemption reported after the incident

The species and size information is not used in the strict pre-incident replay. It is retained only as source-attributed post-incident metadata.

## Replay Runs

### 1. Strict Pre-Incident Replay

The strict pre-incident run uses only timeline-valid context available before the incident window.

Excluded from this run:

- post-incident beach closures
- post-incident drone/helicopter response
- shark size
- suspected species
- invented tide, current, visibility, weather, or sighting values

Output:

- `warning_score`: 0.0, low
- `activity_hazard_score`: 0, low
- `surveillance_priority_score`: 4.0, low
- Active regional pack: `new_south_wales_australia`

Interpretation: with no live environmental, sighting, closure, or incident-specific signals available, AI1SAD keeps the strict pre-incident stack low.

### 2. Quiet-Day Comparison

The quiet-day comparison uses the same location, winter season, and swimming context without incident-specific or response signals.

Output:

- `warning_score`: 0.0, low
- `activity_hazard_score`: 0, low
- `surveillance_priority_score`: 4.0, low

Interpretation: strict pre-incident and quiet-day outputs match because no timeline-valid incident-specific signal is available.

### 3. Post-Incident Operational Update

The post-incident update includes the confirmed incident as a recent interaction. It also documents closures and source-attributed shark size/species metadata in the case artifact, without using them as pre-incident evidence.

Authorities increased drone and helicopter surveillance after the incident, demonstrating that aerial observation is already part of the practical coastal response. AI1SAD should support this by producing structured surveillance priorities, recommended patrol patterns, and map-ready observation feeds for human-operated aerial monitoring.

Structured post-incident aerial response fields:

- `aerial_surveillance_response`: `increased`
- `aerial_platforms`: `drone`, `helicopter`
- `drone_restriction_context`: Sydney Airport flight-path constraints / emergency review context
- `autonomous_flight_control`: `false`

Output:

- `warning_score`: 0.0, low
- `activity_hazard_score`: 0, low
- `surveillance_priority_score`: 18.0, low
- Dominant factor: `recent_interactions_nearby`

Interpretation: the operational surveillance priority rises after the confirmed incident, but the warning score remains low because live tide, current, visibility, weather, and sighting inputs are missing rather than invented.

### 4. Drone-Restriction Operational Scenario

This scenario is operational planning only. It models how AI1SAD should recommend human-approved monitoring patterns when routine drones are constrained by Sydney Airport flight-path rules.

It preserves the distinction between:

- human-operated drone/helicopter surveillance
- AI1SAD recommendation output
- no autonomous flight control

This case supports the Phase 25A/25B/25C drone roadmap need for:

- drone mission records
- surf-line observation intake
- map-ready surveillance feed
- aviation-restriction notes
- human-approved surveillance recommendations

It does not imply:

- autonomous flight
- bypassing aviation restrictions
- unsupervised drone use
- outbound MAVLink commands
- computer-vision inference

Output:

- `warning_score`: 0.0, low
- `activity_hazard_score`: 0, low
- `surveillance_priority_score`: 18.0, low

## Recommended Surveillance Patterns

- `beach_closure_support`
- `shoreline_parallel_sweep`
- `post_incident_focus_area`
- `lifeguard_observation_coordination`
- `aviation_restricted_drone_review`

When drone operations are restricted, AI1SAD should emphasize lifeguard observations, shoreline-parallel human-approved patrol review, helicopter or approved aviation coordination where available, and clear documentation of aviation constraints.

## Missing Signal Sources

The replay intentionally marks unavailable sources as missing:

- weather observations
- ocean observations
- SST anomaly
- vessel activity
- human exposure estimates
- sighting reports
- reef features

No tide, current, visibility, weather, or sighting values are invented for this case.

## Artifacts

- [Replay JSON](../assets/case_studies/coogee_beach_sydney_2026_replay.json)
- [Factor Summary JSON](../assets/case_studies/coogee_beach_sydney_2026_factor_summary.json)
- [Heatmap SVG](../assets/case_studies/coogee_beach_sydney_2026_heatmap.svg)

## Disclaimer

AI1SAD provides bounded operational-intelligence replay outputs. It does not guarantee safety outcomes, infer animal motivation, or replace official beach, lifeguard, aviation, wildlife, or emergency guidance.
