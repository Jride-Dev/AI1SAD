---
title: AI1SAD API
sdk: docker
app_port: 7860
license: apache-2.0
short_description: Read-only public API for the AI1SAD shark incident database.
---

# AI1SAD API

This Docker Space hosts the read-only FastAPI service used by [AI1SAD.org](https://ai1sad.org).

The Space requires a runtime secret named `MONGODB_URI`. Public runtime variables are documented in the main repository deployment guide. Admin writes, alerts, drone ingestion, and media uploads remain disabled.

Source provenance, privacy boundaries, model limitations, and deployment documentation are maintained in the [AI1SAD repository](https://github.com/Jride-Dev/AI1SAD).
