from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.api_v1 import router as api_v1_router
from app.api_access import ApiAccessMiddleware
from app.config import get_settings
from app.mongodb import ensure_mongodb_indexes, get_client, get_database


settings = get_settings()

app = FastAPI(
    title=settings.api_title,
    version="0.2.0",
    description="MongoDB Atlas API for public, privacy-preserving shark incident records.",
)
app.include_router(api_v1_router)
if settings.api_access_enabled:
    app.add_middleware(ApiAccessMiddleware, default_rate_limit_per_minute=settings.api_free_rate_limit_per_minute)


@app.on_event("startup")
def startup() -> None:
    current = get_settings()
    if current.demo_mode or not current.mongodb_uri:
        return
    ensure_mongodb_indexes(get_database())


@app.get("/health")
def health() -> dict[str, object]:
    current = get_settings()
    if current.demo_mode or not current.mongodb_uri:
        return {
            "status": "ok",
            "mode": "demo" if current.demo_mode else "unconfigured",
            "database_configured": bool(current.mongodb_uri),
            "database": current.mongodb_database,
        }
    try:
        get_client().admin.command("ping")
        return {"status": "ok", "mode": "live", "database_configured": True, "database": current.mongodb_database}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"MongoDB unavailable: {exc}") from exc
