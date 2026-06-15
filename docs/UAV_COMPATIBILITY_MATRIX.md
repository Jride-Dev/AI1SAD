# UAV Compatibility Matrix

This page summarises which drone platforms and workflows are supported by AI1SAD today and what integration mode each uses.

## Supported Workflow Modes

- **Manual Drone Operator Console** – the pilot flies normally using the drone's own app; the operator records observations in AI1SAD separately.
- **Read-only MAVLink telemetry** – position, heading, altitude, speed, and battery context is ingested without sending commands.
- **Post-flight evidence reference** – metadata pointers to video files, camera cards, agency evidence IDs, and case references.
- **Source-attributed agency report** – official reports from helicopter patrols, lifeguards, or agencies are entered with source provenance.

## Compatibility Table

| Platform / Source                             | Current AI1SAD Support                                      | API Needed?             | Notes                                           |
| --------------------------------------------- | ----------------------------------------------------------- | ----------------------- | ----------------------------------------------- |
| Any consumer drone app                        | Manual Drone Operator Console                               | No                      | AI1SAD runs beside the app                      |
| DJI Fly / DJI Pilot                           | Manual workflow now; future read-only SDK research possible | No for current workflow | Strong candidate for future research            |
| Ophelia GO / M RC PRO / Holy Stone-class apps | Manual workflow only + post-flight evidence reference       | No                      | Manual fallback, not production API integration |
| Generic Wi-Fi camera drone app                | Manual workflow + map-pin observation                       | No                      | Useful if a human can observe and log           |
| ArduPilot / PX4 / Pixhawk                     | Read-only MAVLink bridge                                    | Yes, MAVLink            | Telemetry context only, no commands             |
| Agency helicopter/drone report                | Source-attributed report/reference                          | No                      | Human/agency source attribution                 |
| No telemetry / no API drone                   | Manual map-pin observation                                  | No                      | Basic patrol logging still supported            |

## What Supported Workflow Means

Supported workflow does not mean direct app or API integration.

- Manual modes use the **Drone Operator Console** for human-entered observations alongside the existing flight app.
- AI1SAD does not need a consumer drone app to expose an API.
- Supported workflow means AI1SAD can be part of the patrol workflow without replacing the existing flight app.

## What Is Not Supported

- Autonomous flight control
- MAVLink command transmission
- DJI SDK control
- Computer vision detections
- Binary media upload
- Cloud media hosting
- Vendor lock-in to any single platform

---

## See Also

- [UAV Operator Research Brief](UAV_OPERATOR_RESEARCH_BRIEF.md)
- [Drone Operator Console](DRONE_OPERATOR_CONSOLE.md)
- [Drone Operations Safety](DRONE_OPERATIONS_SAFETY.md)
- [MAVLink Telemetry Bridge](MAVLINK_TELEMETRY_BRIDGE.md)
