from __future__ import annotations

import unittest
from copy import deepcopy
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api_v1 import router
from app.mongodb import COLLECTIONS, get_database


PUBLIC_INCIDENT = {
    "_id": "public-1",
    "canonical_key": "case:public",
    "visibility": "public",
    "date": {"text": "2026-01-01", "year": 2026, "month": 1, "day": 1},
    "incident_type": "Unprovoked",
    "country": "USA",
    "region": "Florida",
    "location": {"name": "Public Beach", "geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
    "activity": "surfing",
    "sex": "M",
    "age": "31",
    "injury_summary": "Minor injury",
    "fatal": False,
    "species": {"common": "blacktip shark", "scientific": None},
    "source": {"name": "test_source", "row_number": 1, "source_record_id": "2026.01.01"},
    "duplicate": {"is_duplicate": False, "duplicate_of": None},
}

PRIVATE_INCIDENT = {
    **PUBLIC_INCIDENT,
    "_id": "private-1",
    "visibility": "private",
    "injury_summary": "Private note should not appear",
}

RESTRICTED_INCIDENT = {
    **PUBLIC_INCIDENT,
    "_id": "restricted-1",
    "visibility": "restricted",
    "injury_summary": "Restricted note should not appear",
}


def matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, expected in query.items():
        if key == "$and":
            if not all(matches(document, clause) for clause in expected):
                return False
            continue
        value = dotted_get(document, key)
        if isinstance(expected, dict):
            if "$ne" in expected and value == expected["$ne"]:
                return False
            if "$regex" in expected and expected["$regex"].lower() not in str(value or "").lower():
                return False
            continue
        if value != expected:
            return False
    return True


def dotted_get(document: dict[str, Any], key: str) -> Any:
    current: Any = document
    for part in key.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


class FakeCursor:
    def __init__(self, docs: list[dict[str, Any]]):
        self.docs = docs

    def sort(self, *_args: Any, **_kwargs: Any) -> "FakeCursor":
        return self

    def skip(self, count: int) -> "FakeCursor":
        self.docs = self.docs[count:]
        return self

    def limit(self, count: int) -> "FakeCursor":
        self.docs = self.docs[:count]
        return self

    def __iter__(self):
        return iter(self.docs)


class FakeCollection:
    def __init__(self, docs: list[dict[str, Any]]):
        self.docs = docs
        self.last_find_query: dict[str, Any] | None = None
        self.last_aggregate_pipeline: list[dict[str, Any]] | None = None

    def find(self, query: dict[str, Any], _projection: dict[str, Any] | None = None) -> FakeCursor:
        self.last_find_query = query
        return FakeCursor([deepcopy(doc) for doc in self.docs if matches(doc, query)])

    def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        self.last_find_query = query
        for doc in self.docs:
            if matches(doc, query):
                return deepcopy(doc)
        return None

    def count_documents(self, query: dict[str, Any]) -> int:
        return len([doc for doc in self.docs if matches(doc, query)])

    def aggregate(self, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        self.last_aggregate_pipeline = pipeline
        match = pipeline[0].get("$match", {})
        public_docs = [doc for doc in self.docs if matches(doc, match)]
        return [{"key": 2026, "incidents": len(public_docs), "fatalities": 0, "fatality_rate_percent": 0.0}]


class FakeDB:
    def __init__(self):
        self.collections = {
            COLLECTIONS["incidents"]: FakeCollection([PUBLIC_INCIDENT, PRIVATE_INCIDENT, RESTRICTED_INCIDENT]),
            COLLECTIONS["private_notes"]: FakeCollection(
                [
                    {
                        "_id": "private-note-1",
                        "visibility": "private",
                        "incident_id": "public-1",
                        "note": "Do not expose this private analyst note",
                    }
                ]
            ),
            COLLECTIONS["sources"]: FakeCollection(
                [
                    {"_id": "public-source", "name": "public-source", "visibility": "public"},
                    {"_id": "private-source", "name": "private-source", "visibility": "private"},
                ]
            ),
            COLLECTIONS["locations"]: FakeCollection(
                [
                    {"_id": "public-location", "name": "public-location", "visibility": "public"},
                    {"_id": "private-location", "name": "private-location", "visibility": "private"},
                ]
            ),
        }

    def __getitem__(self, name: str) -> FakeCollection:
        return self.collections[name]


class PublicApiPrivacyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = FakeDB()
        test_app = FastAPI()
        test_app.include_router(router)
        test_app.dependency_overrides[get_database] = lambda: self.db
        self.client = TestClient(test_app)

    def test_incident_list_excludes_private_and_restricted(self):
        response = self.client.get("/api/v1/incidents")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["count"], 1)
        self.assertEqual([item["id"] for item in payload["results"]], ["public-1"])
        self.assertEqual(self.db[COLLECTIONS["incidents"]].last_find_query["visibility"], "public")

    def test_private_incident_lookup_returns_404(self):
        response = self.client.get("/api/v1/incidents/private-1")
        self.assertEqual(response.status_code, 404)

    def test_stats_match_filters_visibility_public(self):
        response = self.client.get("/api/v1/stats/yearly")
        self.assertEqual(response.status_code, 200)
        pipeline = self.db[COLLECTIONS["incidents"]].last_aggregate_pipeline
        assert pipeline is not None
        self.assertEqual(pipeline[0]["$match"]["visibility"], "public")

    def test_sources_exclude_private(self):
        response = self.client.get("/api/v1/sources")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["_id"] for item in response.json()], ["public-source"])
        self.assertEqual(self.db[COLLECTIONS["sources"]].last_find_query["visibility"], "public")

    def test_nearby_locations_exclude_private(self):
        response = self.client.get("/api/v1/locations/nearby?lat=25&lon=-80")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["_id"] for item in response.json()], ["public-location"])
        self.assertEqual(self.db[COLLECTIONS["locations"]].last_find_query["visibility"], "public")

    def test_private_notes_collection_has_no_public_route(self):
        response = self.client.get("/api/v1/private_notes")
        self.assertEqual(response.status_code, 404)

        incident_response = self.client.get("/api/v1/incidents/public-1")
        self.assertEqual(incident_response.status_code, 200)
        self.assertNotIn("private", str(incident_response.json()).lower())
        self.assertIsNone(self.db[COLLECTIONS["private_notes"]].last_find_query)


if __name__ == "__main__":
    unittest.main()
