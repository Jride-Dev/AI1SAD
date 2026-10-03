# AI1SAD.org Deployment

## Production Shape

AI1SAD uses three independently deployable surfaces:

| Host | Service | Purpose |
| --- | --- | --- |
| `https://ai1sad.org` | Cloudflare Worker `ai1sad` with Static Assets | React dashboard and Incident Globe |
| `https://www.ai1sad.org` | Cloudflare redirect | Redirects to the apex domain |
| `https://api.ai1sad.org` | Hugging Face Docker Space | Read-only public API backed by MongoDB Atlas |
| `https://docs.ai1sad.org` | Cloudflare Pages project `ai1sad-docs` | MkDocs documentation portal |

The public deployment is a controlled demo. It does not enable admin writes, alerts, drone ingestion, media upload, billing, authentication, or private registry access. Target full working-version launch remains September 7, 2026.

## Before Deployment

The production branch must contain the reviewed globe, deployment configuration, and documentation. Do not deploy directly from the current dirty working tree. Commit and push only after review.

The configured MongoDB database currently contains `40,309` normalized incident documents and `3,398` Incident Globe projection documents. Keep the connection string in the Hugging Face Space secret named `MONGODB_URI` only.

## Frontend Workers Static Assets Project

Create a Cloudflare Workers application by importing `Jride-Dev/AI1SAD` with:

```text
Project name: ai1sad
Production branch: main
Root directory: frontend
Build command: npm run build
Deploy command: npm run deploy
Preview command: npx wrangler preview
```

Set these production build variables:

```text
VITE_AI1SAD_DEMO_MODE=true
VITE_AI1SAD_USE_MOCKS=false
VITE_AI1SAD_API_BASE_URL=https://api.ai1sad.org
VITE_AI1SAD_DOCS_URL=https://docs.ai1sad.org
```

The committed `frontend/wrangler.jsonc` names the Worker `ai1sad`, deploys `frontend/dist`, binds the Worker custom domains `ai1sad.org` and `www.ai1sad.org`, and enables Cloudflare's `single-page-application` fallback for direct visits to `/incident-globe`. Cloudflare manages the custom-domain DNS edge addresses; do not invent origin A or AAAA records for this static Worker. The committed `_headers` file sets browser security headers and permits API connections only to `https://api.ai1sad.org`. Hashed assets receive immutable caching; the data directory uses a one-day cache. Do not add a Pages-style `_redirects` SPA rule: Workers Static Assets rejects it as an infinite loop when `not_found_handling` already provides the fallback.

The Worker custom domains are deployed from `wrangler.jsonc`. Both hostnames currently serve the same application; a separate permanent `www`-to-apex Redirect Rule may be added later if canonical-host redirects are desired.

Cloudflare Email Routing is enabled for `ai1sad.org`. The public aliases `noreply@ai1sad.org` and `info@ai1sad.org` forward to a verified administrative destination. Cloudflare manages the required MX, SPF, and DKIM records. The private forwarding destination must not be committed to this repository or exposed in frontend configuration.

Do not add manual A, AAAA, or CNAME records for the apex or `www` hostnames while they are Worker custom domains. Cloudflare publishes and maintains the edge A/AAAA answers for those bindings, and a literal CNAME would conflict with the Worker route. Add the `api` CNAME only after the Hugging Face custom-domain request exists, and add the `docs` record only after its documentation-host target exists; no placeholder origin addresses are permitted.

## Backend Hugging Face Space

Deploy the reviewed runtime subset as a Hugging Face Docker Space. The root `Dockerfile` runs FastAPI on port `7860`, and `deploy/huggingface-space/README.md` supplies the Space metadata.

Create `MONGODB_URI` as a Space secret and set these public Space variables:

```text
MONGODB_DATABASE=AI1SAD
DEMO_MODE=true
ADMIN_EVENTS_ENABLED=false
ADMIN_SURVEILLANCE_ENABLED=false
ADMIN_ALERTS_ENABLED=false
DRONE_INGEST_ENABLED=false
MEDIA_ATTACHMENTS_ENABLED=false
API_ACCESS_ENABLED=false
CORS_ALLOWED_ORIGINS=https://ai1sad.org,https://www.ai1sad.org
SHARK_ATTACK_API_TITLE=AI1SAD Shark Attack Data API
```

Do not put `MONGODB_URI` in Cloudflare build variables or public Space variables because the browser application does not need database access and the connection string is secret.

In the Space settings, request `api.ai1sad.org` as the custom domain. Add a DNS-only CNAME from `api.ai1sad.org` to `hf.space`, then wait for Hugging Face to report the domain and certificate as ready. Custom domains require Hugging Face PRO, Team, or Enterprise. See [Hugging Face Spaces Deployment](HUGGINGFACE_SPACES_DEPLOY.md).

## Documentation Pages Project

Create a second Cloudflare Pages project from the same repository:

```text
Project name: ai1sad-docs
Production branch: main
Root directory: /
Build command: pip install -r requirements-docs.txt && mkdocs build --strict
Build output directory: site
Environment variable: PYTHON_VERSION=3.12
```

Attach `docs.ai1sad.org` as its custom domain. The docs project contains no runtime database connection or API secret.

## Cloudflare Zone Settings

Use these bounded production defaults:

- SSL/TLS mode: `Full (strict)` after all three certificates are active.
- Always Use HTTPS: enabled.
- Minimum TLS version: 1.2 or newer.
- Automatic HTTPS Rewrites: enabled.
- Browser Integrity Check: enabled.
- Cache HTML using Workers Static Assets defaults; do not cache `api.ai1sad.org` responses without endpoint-specific review.
- Keep Cloudflare Access off the public frontend and docs. Private analyst tools remain local and are not deployed.

Web Analytics is optional. If enabled later, document its privacy behavior before activation; the current build adds no analytics, advertising pixels, cookies, or user tracking.

## Post-Deployment Checks

Run the backend smoke test:

```powershell
F:\Python310\python.exe scripts\smoke_demo.py --base-url https://api.ai1sad.org
```

Then verify:

```text
https://api.ai1sad.org/health
https://api.ai1sad.org/api/v1/incidents-globe?decade=2020
https://ai1sad.org/
https://ai1sad.org/incident-globe
https://docs.ai1sad.org/
```

Confirm that an Origin request from `https://ai1sad.org` receives an appropriate CORS response and that unrelated origins do not. Confirm direct-route refresh works, the globe texture loads, decade and Provoked/Unprovoked filters work, marker infographics open, and no private fields appear in network responses.

## Rollback

- Cloudflare Workers can roll the frontend back to a prior successful deployment; Cloudflare Pages can roll the docs back.
- Hugging Face Spaces can roll the API back by restoring a previously validated Space repository revision while retaining the Space variables and secret.
- DNS changes should be reverted only to the last verified target; do not delete the MongoDB data or source collections as part of a frontend rollback.

## Known Limits

- `1,483` current globe records have unresolved coordinates and remain unplotted.
- Per-case media remains empty until rights and privacy review is complete.
- The public API has no end-user authentication or production billing system.
- The current frontend dependency audit has known development/build-chain advisories documented in [Dependency Security Review](DEPENDENCY_SECURITY_REVIEW.md). None originate from Three.js, but they require a separate bounded maintenance pass.

## Local Validation

Validation completed October 2, 2026:

- MongoDB connectivity: configured; `40,309` incident documents and `3,398` Incident Globe documents confirmed.
- Backend: `336 passed`, with two existing FastAPI startup-event deprecation warnings.
- Production CORS: `https://ai1sad.org` allowed; an unrelated test origin denied.
- Frontend tests: `30 passed`.
- Frontend production build: passed; Cloudflare `_headers` and globe texture copied into `dist`. Workers Static Assets configuration and SPA fallback are provided by `frontend/wrangler.jsonc`; the redundant `_redirects` rule was removed after Cloudflare correctly rejected it as an infinite loop.
- Cloudflare Worker deployment: passed; `ai1sad.org`, `www.ai1sad.org`, and `/incident-globe` returned HTTP `200` over HTTPS, with managed IPv4 and IPv6 edge answers.
- Email Routing: `ready`; the `noreply` and `info` forwarding rules are enabled, and Cloudflare reports the required MX, SPF, and DKIM records.
- MkDocs strict build: passed.
- Docker image and Space metadata: validated locally; the container health check and `/health` passed on port `7860`, with the production frontend CORS origin allowed.
- README local links/images check: `64` checked, `0` missing.
- Changed-file secret and prohibited-language scans: passed with no credential values or prohibited claims.
- Git whitespace check: passed with CRLF normalization warnings only.
- `sitemap.xml`: validated locally.
- Frontend audit: seven existing development/build-chain advisories remain (`1` low, `3` moderate, `3` high); no broad dependency update was performed in this deployment-preparation change.

Frontend deployment, apex/`www` DNS, TLS, Email Routing, and frontend production smoke checks are complete. Hugging Face Space deployment plus `api.ai1sad.org` and documentation hosting plus `docs.ai1sad.org` remain pending; do not create their DNS records until each service provides or requests its real target.
