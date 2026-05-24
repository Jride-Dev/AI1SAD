from __future__ import annotations

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api_access import ApiAccessMiddleware, ApiKeyRecord, hash_api_key


def build_client(*, key: str = "test-key", tier: str = "free", rate_limit: int = 60) -> TestClient:
    app = FastAPI()
    app.add_middleware(
        ApiAccessMiddleware,
        api_keys=[
            ApiKeyRecord(
                id="key-1",
                key_hash=hash_api_key(key),
                tier=tier,
                status="active",
                rate_limit_per_minute=rate_limit,
            )
        ],
    )

    @app.get("/api/v1/incidents")
    def incidents() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/surveillance/search-zones")
    def surveillance() -> dict[str, str]:
        return {"status": "ok"}

    return TestClient(app)


class ApiAccessTests(unittest.TestCase):
    def test_invalid_api_key_is_rejected(self):
        client = build_client()
        response = client.get("/api/v1/incidents", headers={"x-api-key": "wrong-key"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid API key")

    def test_missing_api_key_is_rejected(self):
        client = build_client()
        response = client.get("/api/v1/incidents")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "API key required")

    def test_free_tier_restrictions_block_surveillance_endpoint(self):
        client = build_client(tier="free")
        response = client.get("/api/v1/surveillance/search-zones", headers={"x-api-key": "test-key"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "API tier does not allow this endpoint")

    def test_paid_tier_can_access_surveillance_endpoint(self):
        client = build_client(tier="developer")
        response = client.get("/api/v1/surveillance/search-zones", headers={"x-api-key": "test-key"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-AI1SAD-API-Tier"], "developer")

    def test_rate_limiting(self):
        client = build_client(rate_limit=1)
        first = client.get("/api/v1/incidents", headers={"x-api-key": "test-key"})
        second = client.get("/api/v1/incidents", headers={"x-api-key": "test-key"})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second.json()["detail"], "Rate limit exceeded")


if __name__ == "__main__":
    unittest.main()
