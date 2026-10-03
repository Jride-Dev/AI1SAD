# Hugging Face Spaces Deployment

AI1SAD deploys its public FastAPI backend as a Hugging Face Docker Space. Railway is not part of the production architecture.

## Space

Create a public or protected Docker Space named `ai1sad-api`. Docker Spaces and custom domains require a Hugging Face PRO, Team, or Enterprise plan. The container listens on port `7860`, as declared by `deploy/huggingface-space/README.md`.

Upload only these reviewed runtime files to the Space repository:

```text
README.md                         from deploy/huggingface-space/README.md
Dockerfile                        from the repository root
requirements.txt
app/
providers/
docs/assets/
```

The root `.dockerignore` prevents local credentials, raw imports, private records, media, generated reports, frontend dependencies, and local databases from entering the Docker build context.

## Runtime Configuration

Create `MONGODB_URI` as a Space secret. Never add it as a public variable, commit it, paste it into an issue, or place it in frontend configuration.

Set these Space variables:

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

Demo mode preserves the public read-only guardrails while `MONGODB_URI` supplies the reviewed public MongoDB collections. The Space must not expose private collections, raw source files, credentials, or administrative write endpoints.

## Custom Domain

In the Space settings, request the custom domain `api.ai1sad.org`. Hugging Face requires a CNAME from `api.ai1sad.org` to `hf.space`. Keep the record DNS-only until Hugging Face reports the custom domain as ready and its certificate is active. Do not invent A or AAAA origin addresses.

## Validation

After deployment, run:

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

- Free hardware can sleep when unused; paid hardware is required for continuous availability.
- The Space source is public unless protected visibility is enabled on a qualifying plan.
- Custom domains require a qualifying Hugging Face plan.
- MongoDB remains the source of record; the Space filesystem is disposable and must not be used for persistent registry data.
