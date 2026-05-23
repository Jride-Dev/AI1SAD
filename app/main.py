from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.api_v1 import router as api_v1_router
from app.config import get_settings
from app.mongodb import ensure_mongodb_indexes, get_client, get_database


settings = get_settings()

app = FastAPI(
    title=settings.api_title,
    version="0.2.0",
    description="MongoDB Atlas API for public, privacy-preserving shark incident records.",
)
app.include_router(api_v1_router)


@app.on_event("startup")
def startup() -> None:
    ensure_mongodb_indexes(get_database())


@app.get("/health")
def health() -> dict[str, object]:
    try:
        get_client().admin.command("ping")
        return {"status": "ok", "database": settings.mongodb_database}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"MongoDB unavailable: {exc}") from exc
