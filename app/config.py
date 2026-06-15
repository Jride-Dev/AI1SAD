from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def load_env(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str
    mongodb_database: str
    api_title: str = "AI1SAD Shark Attack Data API"
    demo_mode: bool = False
    admin_events_enabled: bool = False
    admin_surveillance_enabled: bool = False
    admin_alerts_enabled: bool = False
    drone_ingest_enabled: bool = False
    media_attachments_enabled: bool = False
    media_attachments_storage_root: str = "./data/media_attachments"
    api_access_enabled: bool = False
    api_free_rate_limit_per_minute: int = 60


@lru_cache
def get_settings() -> Settings:
    load_env()
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    return Settings(
        mongodb_uri=os.getenv("MONGODB_URI", ""),
        mongodb_database=os.getenv("MONGODB_DATABASE", "AI1SAD"),
        api_title=os.getenv("SHARK_ATTACK_API_TITLE", "AI1SAD Shark Attack Data API"),
        demo_mode=demo_mode,
        admin_events_enabled=False if demo_mode else os.getenv("ADMIN_EVENTS_ENABLED", "false").lower() == "true",
        admin_surveillance_enabled=False if demo_mode else os.getenv("ADMIN_SURVEILLANCE_ENABLED", "false").lower() == "true",
        admin_alerts_enabled=False if demo_mode else os.getenv("ADMIN_ALERTS_ENABLED", "false").lower() == "true",
        drone_ingest_enabled=False if demo_mode else os.getenv("DRONE_INGEST_ENABLED", "false").lower() == "true",
        media_attachments_enabled=False if demo_mode else os.getenv("MEDIA_ATTACHMENTS_ENABLED", "false").lower() == "true",
        media_attachments_storage_root=os.getenv("MEDIA_ATTACHMENTS_STORAGE_ROOT", "./data/media_attachments"),
        api_access_enabled=os.getenv("API_ACCESS_ENABLED", "false").lower() == "true",
        api_free_rate_limit_per_minute=int(os.getenv("API_FREE_RATE_LIMIT_PER_MINUTE", "60")),
    )
