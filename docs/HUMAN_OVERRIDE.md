# Human Override

AI1SAD estimates environmental and surveillance-relevant shark encounter conditions. It does not predict individual attacks or guarantee safety outcomes.

AI1SAD alerts are decision-support artifacts. Lifeguards, beach managers, drone operators, public safety teams, and wildlife authorities remain responsible for operational decisions.

## Operating Rules

- Do not treat AI1SAD alerts as automatic beach closures.
- Do not describe alerts as proof of shark intent.
- Treat spearfishing, fishing, diving, surfing, and swimming as activity context, not moral blame.
- Prefer official local guidance when it conflicts with model output.
- Preserve private notes, restricted reports, victim information, and internal operational details.

## Acknowledgement And Resolution

Admin alert acknowledgement and resolution endpoints are disabled by default. They should only be enabled in trusted deployments after real authentication, authorization, audit logging, and key storage are implemented.

`ADMIN_ALERTS_ENABLED=true` is not sufficient for production readiness by itself.

## Escalation

Escalate alerts for human review when:

- surveillance priority is high but environmental warning is low
- a biological event is uncertain but close to a busy beach
- a recent interaction or verified sighting cluster is active
- confidence is low because provider data is stale or missing
- community reports conflict with official sources
