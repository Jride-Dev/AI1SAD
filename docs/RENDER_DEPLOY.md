# Render Deployment

AI1SAD deploys its read-only public FastAPI backend as a Render Docker web service. The committed `render.yaml` Blueprint uses Render's free web-service plan and the root `Dockerfile`.

## Create The Service

In Render, create a Blueprint from `Jride-Dev/AI1SAD` on branch `main`. Render reads `render.yaml` and proposes one service named `ai1sad-api` with:

```text
Runtime: Docker
Plan: Free
Dockerfile: ./Dockerfile
Health check: /health
Port: Render-provided PORT, defaulting locally to 10000
```

During initial Blueprint creation, enter `MONGODB_URI` when Render prompts for the `sync: false` value. Do not commit it, paste it into an issue, or expose it to frontend configuration. The remaining public-safe environment values are declared in `render.yaml`.

Demo mode keeps administrative writes, alerts, drone ingestion, media uploads, and API access control disabled. MongoDB remains the source of record; Render's filesystem is disposable and contains no raw imports, private reports, local databases, or credentials.

## Custom Domain

After the `onrender.com` URL is healthy, add `api.ai1sad.org` under the service's Custom Domains settings. Render displays the exact DNS target required for verification. Add that target to Cloudflare as a DNS-only CNAME, verify the domain in Render, and wait for managed TLS to become active before production smoke checks.

Do not invent an A or AAAA origin address. Keep the default Render subdomain enabled until the custom domain is verified.

## Validation

Run:

```powershell
F:\Python310\python.exe scripts\smoke_demo.py --base-url https://api.ai1sad.org
```

Also verify:

```text
GET https://api.ai1sad.org/health
GET https://api.ai1sad.org/api/v1/incidents-globe?decade=2020
Origin: https://ai1sad.org
```

The frontend origin must receive the expected CORS headers, unrelated origins must not, and public responses must not contain restricted notes, credentials, raw provider bodies, or private media references.

## Known Limits

- A free Render web service spins down after 15 minutes without inbound traffic and can take about one minute to start again.
- Free service filesystems are ephemeral; all persistent registry data remains in MongoDB.
- Free usage is subject to Render's monthly instance-hour, bandwidth, and build-minute limits.
- Render is a controlled public-demo host, not a change to warning scoring, source provenance, replay behavior, privacy filtering, or database contents.
