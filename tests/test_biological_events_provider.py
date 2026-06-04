from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.providers.biological_events import (
    BIOLOGICAL_EVENT_TYPES,
    STATIC_BIOLOGICAL_EVENTS,
    normalize_static_biological_events,
    provider_health_document,
)
from app.services.alert_engine import evaluate_alerts
from app.services.signal_broker import warning_inputs_from_signals
from app.services.surveillance_engine import score_surveillance_zones
from app.services.warning_engine import calculate_warning
from app.replay.scenarios import REPLAY_SCENARIOS


def test_static_biological_examples_cover_required_regions():
    event_ids = {event["event_id"] for event in STATIC_BIOLOGICAL_EVENTS}

    assert "hawaii_turtle_season_tiger_context" in event_ids
    assert "florida_baitfish_blacktip_overlap" in event_ids
    assert "south_africa_seal_colony_white_shark_context" in event_ids
    assert "red_sea_carcass_dumping_anomaly_context" in event_ids
    assert "wa_reef_prey_context" in event_ids
    assert {"biological_event", "carcass", "sea_turtle_nesting", "baitfish_presence", "seal_presence"} <= BIOLOGICAL_EVENT_TYPES


def test_biological_event_provider_normalizes_signal_shape():
    signals = normalize_static_biological_events(lat=20.5, lon=38.5, radius_km=5)

    assert signals
    signal = signals[0]
    assert signal["signal_type"] == "carcass"
    assert signal["event_type"] == "carcass"
    assert signal["source"]["provider"] == "biological_events_static"
    assert signal["provider_timestamp"] == signal["timestamp"]
    assert signal["location"]["geo"]["type"] == "Point"
    assert signal["confidence"] > 0
    assert signal["data_freshness"]["status"] == "fresh"
    assert signal["event_id"] == "red_sea_carcass_dumping_anomaly_context"
    assert signal["pack_id"] == "red_sea"
    assert signal["source_notes"]
    assert signal["value"] > 0


def test_biological_signals_feed_warning_inputs():
    signals = normalize_static_biological_events(lat=27.7, lon=-80.2, radius_km=5)
    inputs = warning_inputs_from_signals(signals)

    assert inputs["biological_events"]
    assert inputs["biological_events"][0]["event_type"] == "baitfish_presence"
    assert inputs["provider_status"]["biological_events_static"] == "ok"


def test_generic_migration_context_is_bounded_in_warning():
    event = {
        "visibility": "public",
        "event_type": "sea_turtle_migration",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "confidence": 0.6,
        "value": 0.6,
    }

    result = calculate_warning(lat=21.3, lon=-157.8, biological_events=[event])

    assert 0 < result["signals"]["biological_event_score"] <= 5
    assert result["warning_score"] < 30
    assert result["warning_band"] in {"low", "moderate"}


def test_high_confidence_carcass_has_stronger_bounded_warning():
    event = {
        "visibility": "public",
        "event_type": "whale_carcass",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "confidence": 0.95,
        "value": 1.0,
    }

    result = calculate_warning(lat=20.5, lon=38.5, biological_events=[event])

    assert result["signals"]["biological_event_score"] >= 20
    assert result["warning_score"] < 45


def test_carcass_and_fish_kill_expire_from_signal_inputs():
    stale_timestamp = datetime.now(timezone.utc) - timedelta(hours=160)
    signals = [
        {
            "signal_type": "fish_kill",
            "timestamp": stale_timestamp,
            "expires_at": stale_timestamp + timedelta(hours=72),
            "visibility": "public",
            "value": 1,
            "confidence": 0.9,
            "source": {"provider": "biological_events_static"},
        }
    ]

    inputs = warning_inputs_from_signals(signals)

    assert inputs["biological_events"] == []


def test_carcass_has_stronger_surveillance_influence_than_migration_context():
    now = datetime.now(timezone.utc).isoformat()
    carcass = [{"visibility": "public", "event_type": "carcass", "observed_at": now, "confidence": 0.9, "value": 1.0}]
    migration = [{"visibility": "public", "event_type": "sea_turtle_migration", "observed_at": now, "confidence": 0.9, "value": 1.0}]

    carcass_result = score_surveillance_zones(
        lat=20.5,
        lon=38.5,
        radius_km=5,
        mission_type="drone",
        lookback_hours=72,
        warning_inputs={"biological_events": carcass, "provider_status": {}},
    )
    migration_result = score_surveillance_zones(
        lat=20.5,
        lon=38.5,
        radius_km=5,
        mission_type="drone",
        lookback_hours=72,
        warning_inputs={"biological_events": migration, "provider_status": {}},
    )

    carcass_zone = carcass_result["zones"][0]
    migration_zone = migration_result["zones"][0]
    assert carcass_zone["surveillance_priority_score"] > migration_zone["surveillance_priority_score"]
    assert any(factor["factor"] == "biological_event_surveillance_context" for factor in carcass_zone["dominant_factors"])


def test_biological_alerts_include_high_impact_watch_without_private_signals():
    now = datetime.now(timezone.utc)
    alerts = evaluate_alerts(
        {
            "lat": 20.5,
            "lon": 38.5,
            "warning_score": 20,
            "surveillance_priority_score": 30,
            "activity_hazard_score": 0,
            "confidence": 0.7,
            "signals": [
                {
                    "visibility": "public",
                    "signal_type": "fish_kill",
                    "timestamp": now.isoformat(),
                    "expires_at": (now + timedelta(hours=24)).isoformat(),
                    "private_notes": "do not expose",
                },
                {
                    "visibility": "private",
                    "signal_type": "whale_carcass",
                    "timestamp": now.isoformat(),
                    "expires_at": (now + timedelta(hours=24)).isoformat(),
                    "private_notes": "restricted source",
                },
            ],
        },
        now=now,
    )

    biological_alert = next(alert for alert in alerts if alert["alert_type"] == "biological_event")
    assert biological_alert["level"] == "watch"
    assert "private_notes" not in str(biological_alert)
    assert biological_alert["trigger"]["observed_value"] == 1


def test_provider_health_shape():
    health = provider_health_document(generated_signals=3)

    assert health["_id"] == "biological_events_static"
    assert health["provider"] == "biological_events_static"
    assert health["status"] == "healthy"
    assert health["records_ingested"] == 3
    assert health["mode"] == "static_manual_offline"


def test_plumpudding_carcass_metadata_preserves_provisional_taxonomy():
    scenario = REPLAY_SCENARIOS["plumpudding_beach_esperance_whale_carcass_2026_initial"]
    event = scenario.biological_events[0]

    assert event["event_type"] == "whale carcass"
    assert event["signal_type"] == "whale_carcass"
    assert event["whale_taxon"] == "Kogia sp."
    assert event["possible_species"] == "Kogia breviceps"
    assert event["taxonomy_status"] == "provisional"
    assert event["taxonomy_confidence"] == "provisional_unverified"
    assert event["official_species_identification"] is None
    assert event["distance_to_shore_m"] == 1
    assert event["reported_times"]["slswa_logged_at"] == "2026-05-29T15:04:00+08:00"


def test_plumpudding_carcass_warning_is_bounded():
    scenario = REPLAY_SCENARIOS["plumpudding_beach_esperance_whale_carcass_2026_initial"]
    result = calculate_warning(
        lat=scenario.lat,
        lon=scenario.lon,
        biological_events=scenario.biological_events,
        month=scenario.month,
    )

    assert result["signals"]["biological_event_score"] > 0
    assert result["warning_score"] < 45
    assert result["warning_band"] == "low"
