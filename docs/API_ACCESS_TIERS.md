# API Access Tiers

AI1SAD estimates environmental and surveillance-relevant shark encounter conditions. It does not predict individual attacks or guarantee safety outcomes.

This document defines the initial API monetization and access-control foundation. Billing provider integration is not implemented yet, and no Stripe or billing secrets should be committed.

`API_ACCESS_ENABLED=true` currently enables placeholder middleware only. Production deployment still requires real API-key loading, key rotation, hashed key storage, usage logging, billing integration, and persistent/distributed rate limiting.

## Free

Intended for exploration, public demos, and low-volume educational use.

- Basic public incident and summary endpoints.
- Low rate limit.
- No bulk export.
- No provider-health endpoint.
- No surveillance-priority endpoint.
- No commercial SLA.

## Developer

Intended for builders and prototypes.

- Higher request limits.
- Access to warning and signal endpoints.
- Limited surveillance-priority usage.
- No operational SLA.

## Research

Intended for academic, nonprofit, and public-interest research.

- Higher limits for reproducible analysis.
- Access to normalized signals and case-study outputs.
- Usage subject to privacy and source-license rules.
- May require project review for bulk access.

## Government/Enterprise

Intended for coastal safety teams, municipalities, agencies, and enterprise users.

- Higher limits and operational support.
- Surveillance-priority endpoints.
- Provider-health visibility.
- Custom data agreements where needed.
- Stronger audit, usage logging, and support expectations.

## Architecture Collections

- `users`
- `api_keys`
- `usage_logs`
- `billing_tiers`
- `rate_limits`
- `subscription_status`

API keys should be stored as hashes. Billing secrets, payment-provider keys, and customer payment details must stay outside the repository and outside public API responses.
