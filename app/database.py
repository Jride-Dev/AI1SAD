from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path("data/public/shark_attacks.sqlite")


def get_db_path() -> Path:
    return Path(os.getenv("SHARK_ATTACK_DB_PATH", str(DEFAULT_DB_PATH)))


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_all(query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    with connect() as conn:
        return [dict(row) for row in conn.execute(query, params or {})]


def fetch_one(query: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(query, params or {}).fetchone()
    return dict(row) if row else None

