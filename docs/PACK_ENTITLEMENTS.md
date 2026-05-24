# Pack Entitlements

Pack entitlements are soft checks in Phase 8. They do not block Core model access, do not use Stripe, and do not perform real payment processing.

## Soft Access Behavior

Every user can access `core`.

When a request location falls inside a regional pack area:

- If the pack is enabled, responses set `active_pack` to that regional pack.
- If the pack is not enabled, responses keep `active_pack="core"` and include `pack_notice`.
- The API still returns the Core response.

This makes pack availability visible without pretending billing enforcement is production-ready.

## Entitlement Shape

```json
{
  "_id": "entitlement_123",
  "visibility": "public",
  "user_id": "user_123",
  "organization": "Coastal Safety Team",
  "pack_id": "western_australia",
  "access_tier": "research",
  "status": "active",
  "expires_at": null
}
```

## Access Tiers

- `free`: Core model and public metadata.
- `developer`: regional API prototyping.
- `research`: replay validation, calibration, and detailed regional intelligence.
- `government_enterprise`: operational public-safety and high-resolution event-intelligence workflows.

## Deployment Warning

This phase is not production billing. Real hosted deployment still needs:

- authenticated users
- hashed API key storage
- audited entitlement management
- rate-limit persistence
- billing-provider integration outside the repo
- legal and public-safety review

No Stripe keys, payment tokens, billing secrets, MongoDB URIs, or provider credentials should be committed.
