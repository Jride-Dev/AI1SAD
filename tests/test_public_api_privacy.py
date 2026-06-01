from __future__ import annotations

import re
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone
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

PUBLIC_ALERT = {
    "_id": "public-alert",
    "visibility": "public",
    "status": "active",
    "alert_type": "surveillance_priority",
    "level": "urgent_surveillance",
    "title": "Public surveillance alert",
    "summary": "Public alert summary",
    "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
    "zone": {"location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}}, "radius_km": 2.5},
    "recommended_action": "Prioritize drone/search coverage.",
    "dominant_factors": [{"factor": "public factor", "contribution": 0.4}],
    "confidence": 0.8,
    "expires_at": datetime.now(timezone.utc) + timedelta(hours=2),
    "data_freshness": {"weather": {"status": "fresh"}},
    "disclaimer": "AI1SAD estimates environmental and surveillance-relevant shark encounter conditions. It does not predict individual attacks or guarantee safety outcomes.",
}

PRIVATE_ALERT = {
    **PUBLIC_ALERT,
    "_id": "private-alert",
    "visibility": "private",
    "title": "Private alert",
    "private_notes": "Do not expose private alert notes",
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
            if "$gt" in expected and value <= expected["$gt"]:
                return False
            if "$regex" in expected:
                flags = re.IGNORECASE if "i" in str(expected.get("$options", "")) else 0
                pattern = re.compile(str(expected["$regex"]), flags)
                if not pattern.search(str(value or "")):
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

    def find_one(self, query: dict[str, Any], _projection: dict[str, Any] | None = None) -> dict[str, Any] | None:
        self.last_find_query = query
        for doc in self.docs:
            if matches(doc, query):
                return deepcopy(doc)
        return None

    def replace_one(self, query: dict[str, Any], replacement: dict[str, Any], upsert: bool = False):
        for index, doc in enumerate(self.docs):
            if matches(doc, query):
                self.docs[index] = deepcopy(replacement)
                return type("ReplaceResult", (), {"matched_count": 1, "modified_count": 1, "upserted_id": None})()
        if upsert:
            self.docs.append(deepcopy(replacement))
            return type("ReplaceResult", (), {"matched_count": 0, "modified_count": 0, "upserted_id": replacement.get("_id")})()
        return type("ReplaceResult", (), {"matched_count": 0, "modified_count": 0, "upserted_id": None})()

    def insert_one(self, document: dict[str, Any]):
        stored = deepcopy(document)
        stored.setdefault("_id", f"fake-{len(self.docs) + 1}")
        self.docs.append(stored)
        return type("InsertResult", (), {"inserted_id": stored["_id"]})()

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
            COLLECTIONS["risk_observations"]: FakeCollection(
                [
                    {
                        "_id": "public-risk",
                        "visibility": "public",
                        "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
                        "risk": {"score": 20, "band": "low"},
                    },
                    {
                        "_id": "private-risk",
                        "visibility": "private",
                        "private_notes": "Do not expose private risk observation",
                        "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
                        "risk": {"score": 90, "band": "high"},
                    },
                ]
            ),
            COLLECTIONS["regional_risk_profiles"]: FakeCollection(
                [
                    {
                        "_id": "florida",
                        "region_key": "florida",
                        "name": "Florida",
                        "visibility": "public",
                        "private_notes": "Do not expose regional profile notes",
                        "center": {"geo": {"type": "Point", "coordinates": [-80.2, 27.7]}},
                        "local_summer_high_exposure_months": [5, 6, 7, 8, 9],
                        "known_high_attention_months": [3, 4, 10],
                        "dominant_species": ["blacktip shark"],
                        "environmental_multipliers": {"summer": 1.08},
                        "human_exposure_multipliers": {"weekend": 1.15, "non_summer_tourist": 1.08, "beach_exposure": 1.1},
                        "notes": "Public profile note",
                        "citations": ["test citation"],
                    },
                    {
                        "_id": "private-profile",
                        "region_key": "private-profile",
                        "name": "Private Profile",
                        "visibility": "private",
                        "private_notes": "Never expose this private profile",
                        "center": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
                    },
                ]
            ),
            COLLECTIONS["weather_observations"]: FakeCollection(
                [
                    {
                        "_id": "public-weather",
                        "visibility": "public",
                        "rainfall_mm": 50,
                        "observed_at": datetime.now(timezone.utc),
                        "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
                    }
                ]
            ),
            COLLECTIONS["ocean_observations"]: FakeCollection([]),
            COLLECTIONS["vessel_activity"]: FakeCollection([]),
            COLLECTIONS["human_exposure_estimates"]: FakeCollection([]),
            COLLECTIONS["biological_events"]: FakeCollection(
                [
                    {
                        "_id": "public-bio-event",
                        "visibility": "public",
                        "event_type": "whale_carcass",
                        "description": "Public whale carcass report",
                        "observed_at": datetime.now(timezone.utc),
                        "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
                        "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
                    },
                    {
                        "_id": "private-bio-event",
                        "visibility": "private",
                        "event_type": "whale_carcass",
                        "private_notes": "Do not expose private biological event",
                        "description": "Private event",
                        "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
                    },
                ]
            ),
            COLLECTIONS["warning_snapshots"]: FakeCollection([]),
            COLLECTIONS["provider_runs"]: FakeCollection([]),
            COLLECTIONS["provider_failures"]: FakeCollection([]),
            COLLECTIONS["provider_health"]: FakeCollection([]),
            COLLECTIONS["marine_incidents"]: FakeCollection([]),
            COLLECTIONS["shipping_events"]: FakeCollection([]),
            COLLECTIONS["fish_kill_reports"]: FakeCollection([]),
            COLLECTIONS["carcass_reports"]: FakeCollection([]),
            COLLECTIONS["beach_closures"]: FakeCollection([]),
            COLLECTIONS["surveillance_zones"]: FakeCollection([]),
            COLLECTIONS["surveillance_missions"]: FakeCollection([]),
            COLLECTIONS["recent_interactions"]: FakeCollection(
                [
                    {
                        "_id": "public-interaction",
                        "visibility": "public",
                        "observed_at": datetime.now(timezone.utc),
                        "fatal": False,
                        "summary": "Public interaction summary",
                        "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
                    },
                    {
                        "_id": "private-interaction",
                        "visibility": "private",
                        "observed_at": datetime.now(timezone.utc),
                        "fatal": True,
                        "private_notes": "Do not expose private interaction note",
                        "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
                    },
                ]
            ),
            COLLECTIONS["sighting_reports"]: FakeCollection(
                [
                    {
                        "_id": "public-sighting",
                        "visibility": "public",
                        "observed_at": datetime.now(timezone.utc),
                        "verified": True,
                        "confidence": "verified",
                        "summary": "Public sighting report",
                        "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
                    },
                    {
                        "_id": "private-sighting",
                        "visibility": "private",
                        "observed_at": datetime.now(timezone.utc),
                        "verified": True,
                        "private_notes": "Do not expose private sighting note",
                        "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
                    },
                ]
            ),
            COLLECTIONS["reef_features"]: FakeCollection(
                [
                    {
                        "_id": "public-reef",
                        "visibility": "public",
                        "feature_type": "reef",
                        "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
                    },
                    {
                        "_id": "private-reef",
                        "visibility": "private",
                        "private_notes": "Do not expose private reef note",
                        "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
                    },
                ]
            ),
            COLLECTIONS["drone_priority_snapshots"]: FakeCollection([]),
            COLLECTIONS["signals"]: FakeCollection(
                [
                    {
                        "_id": "public-signal",
                        "visibility": "public",
                        "signal_type": "weather_rainfall",
                        "species": "bull shark",
                        "timestamp": datetime.now(timezone.utc),
                        "expires_at": datetime.now(timezone.utc) + timedelta(hours=12),
                        "confidence": 0.8,
                        "value": 100,
                        "units": "mm",
                        "source": {"provider": "test_weather", "dataset": "unit_test"},
                        "risk_relevance": {"score": 0.8, "factors": ["rainfall_runoff"]},
                        "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
                    },
                    {
                        "_id": "private-signal",
                        "visibility": "private",
                        "signal_type": "weather_rainfall",
                        "timestamp": datetime.now(timezone.utc),
                        "confidence": 1,
                        "value": 200,
                        "private_notes": "Do not expose private signal note",
                        "source": {"provider": "private_provider"},
                        "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
                    },
                ]
            ),
            COLLECTIONS["ecology_events"]: FakeCollection([]),
            COLLECTIONS["species_season_profiles"]: FakeCollection(
                [
                    {
                        "_id": "bull-florida",
                        "visibility": "public",
                        "region": "Florida",
                        "species": "bull shark",
                        "active_months": [5, 6, 7, 8, 9],
                        "peak_months": [8, 9],
                        "risk_factors": ["river mouth", "runoff"],
                    },
                    {
                        "_id": "private-season",
                        "visibility": "private",
                        "region": "Florida",
                        "species": "bull shark",
                        "private_notes": "Do not expose private season note",
                    },
                ]
            ),
            COLLECTIONS["migration_windows"]: FakeCollection(
                [
                    {
                        "_id": "bull-migration",
                        "visibility": "public",
                        "region": "Florida",
                        "species": "bull shark",
                        "start_month": 7,
                        "end_month": 10,
                    }
                ]
            ),
            COLLECTIONS["prey_presence_zones"]: FakeCollection([]),
            COLLECTIONS["vessel_activity_snapshots"]: FakeCollection([]),
            COLLECTIONS["tourism_exposure_profiles"]: FakeCollection([]),
            COLLECTIONS["alerts"]: FakeCollection([PUBLIC_ALERT, PRIVATE_ALERT]),
            COLLECTIONS["alert_zones"]: FakeCollection([]),
            COLLECTIONS["alert_rules"]: FakeCollection([]),
            COLLECTIONS["alert_delivery_logs"]: FakeCollection([]),
            COLLECTIONS["alert_acknowledgements"]: FakeCollection([]),
            COLLECTIONS["regional_packs"]: FakeCollection(
                [
                    {
                        "_id": "core",
                        "pack_id": "core",
                        "visibility": "public",
                        "name": "AI1SAD Core",
                        "covered_regions": ["global"],
                        "center": {"geo": {"type": "Point", "coordinates": [0, 0]}},
                        "coverage_radius_km": 20040,
                        "dominant_species": ["bull shark"],
                        "environmental_signals": ["rainfall"],
                        "human_exposure_signals": ["activity_context"],
                        "surveillance_rules": ["core_surveillance"],
                        "alert_rules": ["core_alert"],
                        "replay_scenarios": ["florida_summer_heavy_rain"],
                        "docs_links": ["docs/REGIONAL_PACKS.md"],
                        "required_access_tier": "free",
                        "features": ["core_warning"],
                    },
                    {
                        "_id": "florida",
                        "pack_id": "florida",
                        "visibility": "public",
                        "name": "Florida Regional Pack",
                        "covered_regions": ["Florida"],
                        "center": {"geo": {"type": "Point", "coordinates": [-80.2, 27.7]}},
                        "coverage_radius_km": 900,
                        "dominant_species": ["bull shark", "blacktip shark"],
                        "environmental_signals": ["rainfall_runoff"],
                        "human_exposure_signals": ["weekend"],
                        "surveillance_rules": ["inlet_runoff"],
                        "alert_rules": ["crowded_beach_inlet_rainfall"],
                        "replay_scenarios": ["florida_summer_heavy_rain"],
                        "docs_links": ["docs/REGIONAL_PACKS.md"],
                        "required_access_tier": "developer",
                        "features": ["florida_inlet_rules"],
                    },
                    {
                        "_id": "private-pack",
                        "pack_id": "private-pack",
                        "visibility": "private",
                        "name": "Private Pack",
                        "private_notes": "Do not expose private pack notes",
                    },
                ]
            ),
            COLLECTIONS["pack_entitlements"]: FakeCollection([]),
            COLLECTIONS["pack_features"]: FakeCollection(
                [
                    {"_id": "public-pack-feature", "visibility": "public", "pack_id": "florida", "feature_key": "inlet_runoff"},
                    {
                        "_id": "private-pack-feature",
                        "visibility": "private",
                        "pack_id": "florida",
                        "feature_key": "private",
                        "private_notes": "Do not expose private feature",
                    },
                ]
            ),
            COLLECTIONS["pack_replay_scenarios"]: FakeCollection(
                [
                    {"_id": "public-pack-replay", "visibility": "public", "pack_id": "florida", "scenario_id": "florida_summer_heavy_rain"},
                    {
                        "_id": "private-pack-replay",
                        "visibility": "private",
                        "pack_id": "florida",
                        "scenario_id": "private_replay",
                        "private_notes": "Do not expose private replay",
                    },
                ]
            ),
            COLLECTIONS["pack_species_profiles"]: FakeCollection(
                [
                    {"_id": "public-pack-species", "visibility": "public", "pack_id": "florida", "species": "bull shark"},
                    {
                        "_id": "private-pack-species",
                        "visibility": "private",
                        "pack_id": "florida",
                        "species": "private shark",
                        "private_notes": "Do not expose private species",
                    },
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

    def test_risk_history_excludes_private_observations(self):
        response = self.client.get("/api/v1/risk/history?lat=25&lon=-80")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("not an attack prediction", payload["disclaimer"])
        self.assertEqual([item["_id"] for item in payload["results"]], ["public-risk"])
        self.assertNotIn("private", str(payload).lower())
        self.assertEqual(self.db[COLLECTIONS["risk_observations"]].last_find_query["visibility"], "public")

    def test_risk_location_uses_only_public_incident_density(self):
        response = self.client.get("/api/v1/risk/location?lat=25&lon=-80&recent_rainfall_mm_24h=50&weekend=true&month=11")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("not an attack prediction", payload["disclaimer"])
        self.assertNotIn("Private note should not appear", str(payload))
        self.assertNotIn("Restricted note should not appear", str(payload))
        self.assertNotIn("private profile", str(payload).lower())
        self.assertNotIn("regional profile notes", str(payload).lower())
        self.assertEqual(payload["signals"]["historical_incident_count"], 1)
        self.assertEqual(payload["regional_profile"]["region_key"], "florida")
        self.assertGreater(payload["warning_score"], payload["score"])
        self.assertEqual(self.db[COLLECTIONS["incidents"]].last_find_query["visibility"], "public")

    def test_warning_events_exclude_private_notes(self):
        response = self.client.get("/api/v1/warnings/events?lat=25&lon=-80")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([item["_id"] for item in payload["results"]], ["public-bio-event"])
        self.assertNotIn("private", str(payload).lower())
        self.assertEqual(self.db[COLLECTIONS["biological_events"]].last_find_query["visibility"], "public")

    def test_warning_location_excludes_private_notes(self):
        response = self.client.get("/api/v1/warnings/location?lat=25&lon=-80&month=11")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("not an attack prediction", payload["disclaimer"])
        self.assertNotIn("private", str(payload).lower())
        self.assertIn("warning_score", payload)
        self.assertIn("contribution", payload["dominant_factors"][0])
        self.assertFalse(payload["cached"])

    def test_warning_location_uses_public_cache_snapshot(self):
        first = self.client.get("/api/v1/warnings/location?lat=25&lon=-80&month=11")
        second = self.client.get("/api/v1/warnings/location?lat=25&lon=-80&month=11")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertFalse(first.json()["cached"])
        self.assertTrue(second.json()["cached"])
        self.assertEqual(self.db[COLLECTIONS["warning_snapshots"]].docs[0]["visibility"], "public")
        self.assertIn("expires_at", self.db[COLLECTIONS["warning_snapshots"]].docs[0])

    def test_manual_event_admin_endpoint_disabled_by_default(self):
        response = self.client.post(
            "/api/v1/admin/events/manual",
            json={"event_type": "whale_carcass", "lat": 25, "lon": -80, "description": "test"},
        )
        self.assertEqual(response.status_code, 403)

    def test_surveillance_search_zones_exclude_private_notes(self):
        response = self.client.get(
            "/api/v1/surveillance/search-zones?lat=25&lon=-80&activity_context=fishing&suspected_species=bull%20shark&river_mouth_distance_km=1"
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("prioritization score", payload["disclaimer"])
        self.assertEqual(len(payload["zones"]), 1)
        self.assertIn("dominant_factors", payload["zones"][0])
        self.assertNotIn("private", str(payload).lower())
        self.assertEqual(self.db[COLLECTIONS["recent_interactions"]].last_find_query["visibility"], "public")
        self.assertEqual(self.db[COLLECTIONS["sighting_reports"]].last_find_query["visibility"], "public")

    def test_surveillance_recent_interactions_and_sightings_exclude_private(self):
        interactions = self.client.get("/api/v1/surveillance/recent-interactions?lat=25&lon=-80")
        sightings = self.client.get("/api/v1/surveillance/sightings?lat=25&lon=-80")
        self.assertEqual(interactions.status_code, 200)
        self.assertEqual(sightings.status_code, 200)
        self.assertEqual([item["_id"] for item in interactions.json()["results"]], ["public-interaction"])
        self.assertEqual([item["_id"] for item in sightings.json()["results"]], ["public-sighting"])
        self.assertNotIn("private", str(interactions.json()).lower())
        self.assertNotIn("private", str(sightings.json()).lower())

    def test_surveillance_admin_endpoints_disabled_by_default(self):
        payload = {"lat": 25, "lon": -80, "summary": "test"}
        interaction = self.client.post("/api/v1/admin/surveillance/interaction", json=payload)
        sighting = self.client.post("/api/v1/admin/surveillance/sighting", json=payload)
        self.assertEqual(interaction.status_code, 403)
        self.assertEqual(sighting.status_code, 403)

    def test_signals_api_excludes_private_signals(self):
        response = self.client.get("/api/v1/signals/location?lat=25&lon=-80")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([item["_id"] for item in payload["results"]], ["public-signal"])
        self.assertNotIn("private", str(payload).lower())
        self.assertIn("data_freshness", payload)

    def test_active_signal_influences_warning_score(self):
        with_signal = self.client.get("/api/v1/warnings/location?lat=25&lon=-80&bypass_cache=true")
        self.db[COLLECTIONS["signals"]].docs = []
        without_signal = self.client.get("/api/v1/warnings/location?lat=25&lon=-80&bypass_cache=true")
        self.assertEqual(with_signal.status_code, 200)
        self.assertEqual(without_signal.status_code, 200)
        self.assertGreater(with_signal.json()["warning_score"], without_signal.json()["warning_score"])

    def test_stale_signal_reduces_warning_confidence(self):
        self.db[COLLECTIONS["signals"]].docs = [
            {
                "_id": "stale-signal",
                "visibility": "public",
                "signal_type": "weather_rainfall",
                "timestamp": datetime.now(timezone.utc) - timedelta(hours=8),
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=4),
                "max_age_hours": 6,
                "confidence": 0.8,
                "value": 100,
                "source": {"provider": "test_weather"},
                "risk_relevance": {"score": 0.8, "factors": ["rainfall_runoff"]},
                "location": {"geo": {"type": "Point", "coordinates": [-80.0, 25.0]}},
            }
        ]
        response = self.client.get("/api/v1/warnings/location?lat=25&lon=-80&bypass_cache=true")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("test_weather:stale", payload["missing_data_sources"])
        self.assertEqual(payload["data_freshness"]["test_weather"]["status"], "stale")

    def test_provider_health_and_species_profiles_are_public_safe(self):
        self.db[COLLECTIONS["provider_health"]].docs = [{"_id": "open_meteo", "provider": "open_meteo", "status": "healthy"}]
        health = self.client.get("/api/v1/provider-health")
        season = self.client.get("/api/v1/regions/Florida/season-profile")
        species = self.client.get("/api/v1/species/bull%20shark/risk-profile")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(season.status_code, 200)
        self.assertEqual(species.status_code, 200)
        self.assertNotIn("private", str(season.json()).lower())
        self.assertNotIn("private", str(species.json()).lower())

    def test_species_regex_metacharacters_are_escaped(self):
        response = self.client.get("/api/v1/species/bull.*shark/risk-profile")
        self.assertEqual(response.status_code, 200)
        query = self.db[COLLECTIONS["species_season_profiles"]].last_find_query
        assert query is not None
        self.assertEqual(query["species"]["$regex"], re.escape("bull.*shark"))

    def test_region_regex_metacharacters_are_escaped(self):
        response = self.client.get("/api/v1/regions/Flor.*da/season-profile")
        self.assertEqual(response.status_code, 200)
        query = self.db[COLLECTIONS["species_season_profiles"]].last_find_query
        assert query is not None
        self.assertEqual(query["region"]["$regex"], re.escape("Flor.*da"))

    def test_empty_or_whitespace_search_is_rejected(self):
        species = self.client.get("/api/v1/signals/species?species=%20%20")
        region = self.client.get("/api/v1/regions/%20/season-profile")
        self.assertEqual(species.status_code, 422)
        self.assertEqual(region.status_code, 422)

    def test_overly_long_species_or_region_is_rejected(self):
        long_value = "a" * 81
        species = self.client.get(f"/api/v1/signals/species?species={long_value}")
        region = self.client.get(f"/api/v1/regions/{long_value}/season-profile")
        self.assertEqual(species.status_code, 422)
        self.assertEqual(region.status_code, 422)

    def test_intentional_partial_search_still_works(self):
        species = self.client.get("/api/v1/species/bull/risk-profile")
        region = self.client.get("/api/v1/regions/Flor/season-profile")
        self.assertEqual(species.status_code, 200)
        self.assertEqual(region.status_code, 200)
        self.assertGreaterEqual(len(species.json().get("season_profiles", [])), 1)
        self.assertGreaterEqual(len(region.json().get("results", [])), 1)

    def test_public_provider_failures_use_coarse_error_summary(self):
        self.db[COLLECTIONS["provider_failures"]].docs = [
            {"_id": "failure-1", "provider": "open_meteo", "status": "failed", "last_error": "Traceback...secret details"}
        ]
        response = self.client.get("/api/v1/provider-health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["recent_failures"][0]["error_summary"], "fetch_failed")
        self.assertNotIn("Traceback", str(payload))
        self.assertNotIn("secret details", str(payload))

    def test_provider_failure_does_not_crash_warning_endpoint(self):
        self.db[COLLECTIONS["provider_failures"]].docs = [
            {"_id": "failure-1", "provider": "noaa_coastwatch", "status": "failed", "error_summary": "timeout"}
        ]
        response = self.client.get("/api/v1/warnings/location?lat=25&lon=-80&bypass_cache=true")
        self.assertEqual(response.status_code, 200)
        self.assertIn("data_freshness", response.json())
        self.assertEqual(response.json()["data_freshness"]["ocean_observations"]["status"], "missing")

    def test_alert_routes_exclude_private_alerts(self):
        active = self.client.get("/api/v1/alerts/active")
        nearby = self.client.get("/api/v1/alerts/location?lat=25&lon=-80")
        private_lookup = self.client.get("/api/v1/alerts/private-alert")
        self.assertEqual(active.status_code, 200)
        self.assertEqual(nearby.status_code, 200)
        self.assertEqual(private_lookup.status_code, 404)
        self.assertEqual([item["_id"] for item in active.json()["results"]], ["public-alert"])
        self.assertEqual([item["_id"] for item in nearby.json()["results"]], ["public-alert"])
        self.assertNotIn("private", str(active.json()).lower())
        self.assertNotIn("private", str(nearby.json()).lower())

    def test_alert_evaluate_is_public_safe(self):
        response = self.client.post(
            "/api/v1/alerts/evaluate",
            json={
                "lat": 25,
                "lon": -80,
                "warning_score": 0,
                "surveillance_priority_score": 92,
                "activity_hazard_score": 50,
                "confidence": 0.7,
                "dominant_factors": [{"factor": "reef context", "private_notes": "hide me"}],
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(any(alert["alert_type"] == "surveillance_priority" for alert in payload["alerts"]))
        self.assertNotIn("private_notes", str(payload))

    def test_alert_admin_endpoints_disabled_by_default(self):
        acknowledge = self.client.post("/api/v1/admin/alerts/acknowledge", json={"alert_id": "public-alert"})
        resolve = self.client.post("/api/v1/admin/alerts/resolve", json={"alert_id": "public-alert"})
        self.assertEqual(acknowledge.status_code, 403)
        self.assertEqual(resolve.status_code, 403)


if __name__ == "__main__":
    unittest.main()
