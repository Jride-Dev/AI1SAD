from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services.alert_engine import evaluate_alerts


def base_payload(**overrides):
    payload = {
        "lat": -31.9826564,
        "lon": 115.5153234,
        "warning_score": 0,
        "activity_hazard_score": 58,
        "surveillance_priority_score": 99.3,
        "confidence": 0.48,
        "dominant_factors": [{"factor": "reef spearfishing white shark context", "points": 58}],
        "data_freshness": {"environmental": {"status": "missing"}},
    }
    payload.update(overrides)
    return payload


def test_high_surveillance_priority_creates_alert_even_with_low_warning_score():
    alerts = evaluate_alerts(base_payload())
    types = {alert["alert_type"] for alert in alerts}
    assert "surveillance_priority" in types
    surveillance = next(alert for alert in alerts if alert["alert_type"] == "surveillance_priority")
    assert surveillance["level"] == "urgent_surveillance"
    assert surveillance["zone"]["location"]["geo"]["coordinates"] == [115.5153234, -31.9826564]
    assert "drone" in surveillance["recommended_action"].lower()


def test_stale_signal_expires_alert():
    alerts = evaluate_alerts(
        base_payload(
            surveillance_priority_score=90,
            activity_hazard_score=0,
            data_freshness={"sighting": {"status": "stale"}, "weather": {"status": "expired"}},
        )
    )
    assert alerts == []


def test_quiet_day_comparison_suppresses_weak_alert():
    alerts = evaluate_alerts(
        base_payload(
            warning_score=25,
            surveillance_priority_score=30,
            activity_hazard_score=10,
            quiet_day_comparison={"delta": 3},
            signals=[],
        )
    )
    assert alerts == []


def test_activity_hazard_creates_activity_specific_alert():
    alerts = evaluate_alerts(base_payload(surveillance_priority_score=20, activity_hazard_score=62))
    types = {alert["alert_type"] for alert in alerts}
    assert "activity_hazard" in types


def test_private_internal_signals_are_not_exposed_in_public_alerts():
    now = datetime.now(timezone.utc)
    alerts = evaluate_alerts(
        base_payload(
            warning_score=10,
            surveillance_priority_score=20,
            activity_hazard_score=0,
            signals=[
                {
                    "visibility": "private",
                    "signal_type": "sighting",
                    "private_notes": "do not expose",
                    "expires_at": (now + timedelta(hours=2)).isoformat(),
                },
                {
                    "visibility": "public",
                    "signal_type": "carcass",
                    "private_notes": "do not expose",
                    "expires_at": (now + timedelta(hours=2)).isoformat(),
                },
            ],
        )
    )
    assert any(alert["alert_type"] == "biological_event" for alert in alerts)
    assert "private_notes" not in str(alerts)
