# UAV Operator Research Brief

## 1. Purpose

AI1SAD is a marine operational-intelligence platform for shark-risk awareness, coastal surveillance prioritisation, replay analysis, and drone-assisted observation workflows.

It is not an attack-prediction system.

This brief explains how AI1SAD supports UAV operators, lifeguards, coastal authorities, researchers, and shark-surveillance teams who fly or oversee real drone patrols. The system helps log observations, preserve evidence references, produce public-safe surveillance feeds, and learn from replay case studies.

AI1SAD supports human-operated patrols. It does not control aircraft, predict individual incidents, or infer shark intent.

---

## 2. What AI1SAD Does

- **Mission records** – log drone patrols with time, location, operator, and platform metadata
- **Human-entered observations** – record shark sightings, no-sighting patrols, carcasses, baitfish activity, poor visibility, swimmer density, surf-line activity, and other coastal signals
- **No-sighting patrols** – log that a patrol covered an area without observing anything, which is operationally useful even when uneventful
- **Telemetry context** – ingest read-only position, heading, altitude, speed, and battery telemetry from compatible platforms
- **Post-flight evidence references** – store metadata pointers to video files, camera card references, agency evidence IDs, and private case references
- **Analyst review** – annotate observations with review status, outcome, evidence confidence, and public-safe summaries
- **Public-safe summaries** – produce structured feeds that exclude private filenames, storage paths, raw media references, and internal notes
- **Replay and case-study learning** – run timeline-separated pre-incident, quiet-day, post-incident, and hypothetical replay scenarios
- **Source-attributed uncertainty** – mark species assessments as preliminary, same-individual links as unconfirmed, and visual assessments as analyst uncertainty

---

## 3. What AI1SAD Does Not Do

- Does not control drones
- Does not autonomously fly aircraft
- Does not bypass manufacturer apps
- Does not require consumer drone APIs for manual workflows
- Does not fetch, download, host, or analyse media
- Does not create shark sightings from telemetry alone
- Does not predict individual shark attacks
- Does not infer shark intent
- Does not claim certainty where evidence does not support it

---

## 4. Drone Workflow Modes

### 4.1 Manual Consumer Drone Workflow

**For:** DJI Fly, DJI Pilot, Ophelia GO, M RC PRO, Holy Stone-class apps, Wi-Fi camera drones, and other consumer drone flight apps.

AI1SAD works beside the drone app, not inside it.

**Workflow:**

1. The pilot flies the drone normally using the manufacturer's own app, controller, or software.
2. The operator watches the live video feed from the drone.
3. The operator logs observations in the AI1SAD Drone Operator Console.
4. Optional media or evidence references are added (e.g. video clip ID, SD card reference, agency evidence number).
5. An analyst reviews the observation and produces a public-safe summary.

AI1SAD does not need the consumer drone app to expose an API. The operator records observations separately while the drone is flown manually.

### 4.2 MAVLink Read-Only Telemetry Workflow

**For:** ArduPilot / PX4 / Pixhawk-style drones.

AI1SAD ingests telemetry context only. It does not send flight commands.

**Workflow:**

1. The MAVLink bridge reads telemetry from a JSONL fixture or compatible MAVLink source.
2. AI1SAD receives position, heading, altitude, speed, and battery context.
3. Operator observations remain human-entered through the Drone Operator Console.
4. Telemetry alone does not create sightings. Sightings require a human observation record.

No MAVLink commands are transmitted. The bridge is receive-only.

### 4.3 Post-Flight Evidence Workflow

**For:** Video files, photo files, screen recordings, SD card references, agency evidence IDs, clip IDs.

Current media support is metadata-only. AI1SAD stores evidence pointers, not media files.

**Workflow:**

1. After a patrol, the operator records a metadata reference to the evidence.
2. Supported reference types: local filename, camera card reference, agency evidence ID, or private case reference.
3. AI1SAD stores the reference alongside the observation record.
4. The reference remains private by default and is excluded from public feeds.
5. Binary upload, media hosting, and public release remain future work.

### 4.4 Agency / Helicopter / Lifeguard Report Workflow

**For:** Official aerial surveillance reports, helicopter patrol reports, lifeguard observation logs, and agency source documents.

Source-attributed observations can support surveillance context without becoming certainty claims.

**Workflow:**

1. An agency or operator report is entered as a source-attributed observation.
2. The source provenance is recorded (official agency notice, source-attributed media report, operator assessment, etc.).
3. Species information is marked with classification status and confidence level.
4. The observation supports surveillance priority without claiming certainty about the original report.

---

## 5. Compatibility Matrix

| Platform / Source                             | Current AI1SAD Support                                      | API Needed?             | Notes                                           |
| --------------------------------------------- | ----------------------------------------------------------- | ----------------------- | ----------------------------------------------- |
| Any consumer drone app                        | Manual Drone Operator Console                               | No                      | AI1SAD runs beside the app                      |
| DJI Fly / DJI Pilot                           | Manual workflow now; future read-only SDK research possible | No for current workflow | Strong candidate for future research            |
| Ophelia GO / M RC PRO / Holy Stone-class apps | Manual workflow only + post-flight evidence reference       | No                      | Manual fallback, not production API integration |
| Generic Wi-Fi camera drone app                | Manual workflow + map-pin observation                       | No                      | Useful if a human can observe and log           |
| ArduPilot / PX4 / Pixhawk                     | Read-only MAVLink bridge                                    | Yes, MAVLink            | Telemetry context only, no commands             |
| Agency helicopter/drone report                | Source-attributed report/reference                          | No                      | Human/agency source attribution                 |
| No telemetry / no API drone                   | Manual map-pin observation                                  | No                      | Basic patrol logging still supported            |

Supported workflow does not mean direct app or API integration. Manual workflow modes use the Drone Operator Console for human-entered observations alongside the existing flight app.

---

## 6. Coogee Beach Case-Study Relevance

The Coogee Beach Sydney 2026 replay is the most operator-relevant example in the replay library:

- Post-incident aerial, drone, and helicopter footage exists showing a large shark in the area.
- Source reporting indicates a probable white shark, attributed to drone and helicopter footage analysis.
- Authorities (NSW DPI) cautioned that the footage does not prove it was the same shark involved in the attack.
- A rescuer described a 3-4 metre shark and water "all red" during rescue, preserved as a source-attributed quote.
- A possible blood plume is noted as analyst visual assessment uncertainty, not confirmed fact.

This case shows why UAV evidence workflows need structured metadata and human review:

- Video evidence alone does not equal certainty.
- Species assessments need source attribution and confidence labels.
- Same-individual relationships require explicit caution.
- Visual assessments of water conditions are analyst uncertainty, not sensor output.
- AI1SAD preserves uncertainty instead of pretending video equals certainty.

---

## 7. Operator Questions AI1SAD Helps Answer

- Where should patrol attention focus?
- What was observed during this patrol?
- Was it a sighting, a no-sighting patrol, a carcass, baitfish activity, poor visibility, swimmer density, or another signal?
- What evidence exists for this observation?
- Who reviewed the observation?
- What can safely appear in public output?
- What uncertainty remains about the species, size, or same-individual link?
- What should be watched next?

---

## 8. Minimum Field Checklist for a Useful Patrol Observation

| Field | Purpose |
|---|---|
| Mission ID | Links observation to a specific patrol |
| Observed time | When the observation occurred |
| Latitude / longitude | Where the observation was made |
| Observation type | Sighting, no-sighting, carcass, baitfish, poor visibility, swimmer density, etc. |
| Operator role | Drone operator, lifeguard, analyst, coastal observer, agency observer |
| Confidence | How sure the operator is (0-1) |
| Visibility conditions | Clear, moderate, poor, unknown |
| Species guess (if any) | Must be marked provisional |
| Media/evidence reference | Optional: filename, card reference, agency ID, case reference |
| Public summary | Safe for public feed output |
| Private analyst notes | Optional: internal notes, never public |

---

## 9. Safety and Privacy Boundaries

- Private attachment metadata stays private. It is never exposed in public feeds.
- Public feeds exclude filenames, storage paths, keys, raw media references, checksums, uploader roles, and internal notes.
- No sightings are created from telemetry alone. A human observation record is always required.
- No species inference is performed from attachments. AI1SAD does not analyse media.
- No computer vision or automated media analysis is used.
- No autonomous drone control is supported.
- Attachment writes require `MEDIA_ATTACHMENTS_ENABLED=true` and are disabled by default.
- Raw media references in observation records are excluded from public responses.

---

## 10. Research Questions for Real UAV Operators

These questions are intended for future engagement with NSW, lifeguard, government, and research UAV teams:

1. What drone software is commonly used by NSW, lifeguard, government, and research UAV teams?
2. What telemetry, if any, is exportable from your current drone platforms?
3. Do operators currently log no-sighting patrols, and if so, how?
4. How are drone videos, photos, and screen recordings referenced internally?
5. What fields do operators actually record during a patrol (time, location, species, conditions, notes)?
6. How are public warnings separated from private operational notes in your current workflow?
7. What privacy rules apply to imagery of swimmers, beaches, and bystanders?
8. How are drone restrictions handled near airports, helipads, or controlled airspace?
9. What would make AI1SAD useful without interfering with existing flight and reporting workflows?
10. Would a structured observation log that preserves uncertainty be useful for post-patrol review and training?

---

## See Also

- [UAV Compatibility Matrix](UAV_COMPATIBILITY_MATRIX.md)
- [UAV Operator Feedback Intake](UAV_OPERATOR_FEEDBACK_INTAKE.md)
- [Drone Operator Console](DRONE_OPERATOR_CONSOLE.md)
- [Drone Observation Ingestion](DRONE_OBSERVATION_INGESTION.md)
- [Observation Analyst Review](OBSERVATION_ANALYST_REVIEW.md)
- [Local Media Attachment Prototype](LOCAL_MEDIA_ATTACHMENT_PROTOTYPE.md)
- [Drone Operations Safety](DRONE_OPERATIONS_SAFETY.md)
- [Coogee Beach Sydney 2026 replay](case_studies/coogee_beach_sydney_2026.md)
