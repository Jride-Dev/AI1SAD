from __future__ import annotations

import hashlib
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


FREE_RESTRICTED_PREFIXES = (
    "/api/v1/surveillance",
    "/api/v1/signals/active",
    "/api/v1/provider-health",
)

PUBLIC_PATH_PREFIXES = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
)


@dataclass(frozen=True)
class ApiKeyRecord:
    key_hash: str
    tier: str = "free"
    status: str = "active"
    rate_limit_per_minute: int = 60
    id: str | None = None


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def tier_allows_path(tier: str, path: str) -> bool:
    if tier != "free":
        return True
    return not any(path.startswith(prefix) for prefix in FREE_RESTRICTED_PREFIXES)


class ApiAccessMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Any,
        *,
        api_keys: list[ApiKeyRecord] | None = None,
        default_rate_limit_per_minute: int = 60,
    ) -> None:
        super().__init__(app)
        self.api_keys = {record.key_hash: record for record in api_keys or []}
        self.default_rate_limit_per_minute = default_rate_limit_per_minute
        self.window_counts: dict[tuple[str, int], int] = defaultdict(int)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        if any(request.url.path.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES):
            return await call_next(request)

        api_key = request.headers.get("x-api-key")
        if not api_key:
            return JSONResponse({"detail": "API key required"}, status_code=401)

        record = self.api_keys.get(hash_api_key(api_key))
        if not record or record.status != "active":
            return JSONResponse({"detail": "Invalid API key"}, status_code=401)

        if not tier_allows_path(record.tier, request.url.path):
            return JSONResponse({"detail": "API tier does not allow this endpoint"}, status_code=403)

        window = int(time.time() // 60)
        key = (record.key_hash, window)
        self.window_counts[key] += 1
        limit = record.rate_limit_per_minute or self.default_rate_limit_per_minute
        if self.window_counts[key] > limit:
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)

        request.state.api_key_id = record.id
        request.state.api_tier = record.tier
        response = await call_next(request)
        response.headers["X-AI1SAD-API-Tier"] = record.tier
        return response
