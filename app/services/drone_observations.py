from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4


MISSION_TYPES = {
    "shoreline_parallel_sweep",
    "reef_gap_focus_scan",
    "channel_mouth_pass",
    "post_sighting_focus_area",
    "carcass_event_buffer_zone",
    "kelp_edge_focus_scan",
    "offshore_island_focus_scan",
    "manual_observation_patrol",
}

OBSERVATION_TYPES = {
    "shark_sighting",
    "unknown_large_marine_animal",
    "baitfish_congregation",
    "marine_mammal_activity",
    "carcass",
    "water_clarity_observation",
    "surf_line_activity",
    "swimmer_density",
    "vessel_activity",
    "no_sighting_patrol_result",
    "other",
}

REVIEW_STATUSES = {"unreviewed", "operator_reviewed", "analyst_reviewed", "confirmed", "rejected"}
SPECIES_ASSESSMENT_SOURCES = {
    "operator_visual_assessment",
    "analyst_visual_assessment",
    "agency_preliminary_assessment",
    "computer_vision_candidate",
    "confirmed_external_source",
}

MEDIA_REFERENCE_TYPES = {
    "local_filename",
    "drone_clip_id",
    "camera_card_reference",
    "external_url",
    "agency_evidence_id",
    "private_case_reference",
    "none",
}

ANALYST_REVIEW_STATUSES = {
    "unreviewed",
    "needs_review",
    "in_review",
    "reviewed",
    "rejected",
    "inconclusive",
}

REVIEW_OUTCOMES = {
    "no_public_change",
    "confirms_operator_observation",
    "downgrades_operator_observation",
    "upgrades_operator_observation",
    "species_uncertain",
    "false_positive",
    "duplicate",
    "unusable_media",
}

PUBLIC_DROP_FIELDS = {"notes_internal", "internal_notes", "analyst_notes", "analyst_notes_internal", "analyst_notes_private", "analyst_reviewer_role", "analyst_reviewed_at", "operator_id", "private_notes", "restricted"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_time(value: Any, *, default: datetime | None = None) -> datetime:
    if value is None:
        return default or utc_now()
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def required_time(payload: dict[str, Any], field: str) -> datetime:
    if payload.get(field) in {None, ""}:
        raise ValueError(f"{field} is required")
    return parse_time(payload[field])


def bounded_float(value: Any, field: str, minimum: float, maximum: float) -> float:
    result = float(value)
    if result < minimum or result > maximum:
        raise ValueError(f"{field} must be between {minimum} and {maximum}")
    return result


def optional_bounded_float(value: Any, field: str, minimum: float, maximum: float) -> float | None:
    if value in {None, ""}:
        return None
    return bounded_float(value, field, minimum, maximum)


def bounded_int(value: Any, field: str, minimum: int, maximum: int) -> int:
    result = int(value)
    if result < minimum or result > maximum:
        raise ValueError(f"{field} must be between {minimum} and {maximum}")
    return result


def text_field(value: Any, field: str, *, max_length: int = 200, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    if len(text) > max_length:
        raise ValueError(f"{field} must be {max_length} characters or fewer")
    return text


def point(lon: float, lat: float) -> dict[str, Any]:
    return {"geo": {"type": "Point", "coordinates": [float(lon), float(lat)]}}


def public_visibility(value: Any) -> str:
    return "public" if value in {True, "public"} else "private"


def require_choice(value: str, allowed: set[str], field: str) -> str:
    if value not in allowed:
        raise ValueError(f"{field} must be one of: {', '.join(sorted(allowed))}")
    return value


def build_mission(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    mission_type = require_choice(str(payload.get("mission_type", "manual_observation_patrol")), MISSION_TYPES, "mission_type")
    mission_id = text_field(payload.get("mission_id") or f"mission-{uuid4().hex[:12]}", "mission_id", max_length=80)
    started_at = required_time(payload, "started_at")
    ended_at = parse_time(payload.get("ended_at")) if payload.get("ended_at") else None
    launch = payload.get("launch_location") or {}
    area = payload.get("intended_area") or launch
    if launch:
        launch_lat = bounded_float(launch["latitude"], "launch_location.latitude", -90, 90)
        launch_lon = bounded_float(launch["longitude"], "launch_location.longitude", -180, 180)
    if area:
        area_lat = bounded_float(area["latitude"], "intended_area.latitude", -90, 90)
        area_lon = bounded_float(area["longitude"], "intended_area.longitude", -180, 180)
    doc = {
        "_id": mission_id,
        "mission_id": mission_id,
        "drone_id": text_field(payload["drone_id"], "drone_id", max_length=80),
        "operator_id": text_field(payload["operator_id"], "operator_id", max_length=80),
        "operator_role": text_field(payload.get("operator_role", "human_operator"), "operator_role", max_length=80),
        "region": text_field(payload.get("region", ""), "region", max_length=120),
        "pack_id": text_field(payload.get("pack_id", "core"), "pack_id", max_length=80),
        "mission_type": mission_type,
        "started_at": started_at,
        "ended_at": ended_at,
        "status": text_field(payload.get("status", "active"), "status", max_length=40),
        "launch_location": point(launch_lon, launch_lat) if launch else None,
        "intended_area": point(area_lon, area_lat) if area else None,
        "recommended_pattern": text_field(payload.get("recommended_pattern", mission_type), "recommended_pattern", max_length=80),
        "human_approved": True,
        "autonomous_flight_control": False,
        "source": text_field(payload.get("source", "drone_operator_submission"), "source", max_length=120),
        "visibility": public_visibility(payload.get("visibility", "public")),
        "notes_public": text_field(payload.get("notes_public", ""), "notes_public", max_length=500),
        "notes_internal": text_field(payload.get("notes_internal", ""), "notes_internal", max_length=1000),
        "created_at": utc_now(),
    }
    return doc


def build_telemetry(mission: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    lat = bounded_float(payload["latitude"], "latitude", -90, 90)
    lon = bounded_float(payload["longitude"], "longitude", -180, 180)
    telemetry_id = text_field(payload.get("telemetry_id") or f"telemetry-{uuid4().hex[:12]}", "telemetry_id", max_length=80)
    return {
        "_id": telemetry_id,
        "telemetry_id": telemetry_id,
        "mission_id": mission["mission_id"],
        "drone_id": text_field(payload.get("drone_id", mission["drone_id"]), "drone_id", max_length=80),
        "timestamp": required_time(payload, "timestamp"),
        "latitude": lat,
        "longitude": lon,
        "location": point(lon, lat),
        "altitude_m": optional_bounded_float(payload.get("altitude_m"), "altitude_m", -20, 1000),
        "heading_deg": optional_bounded_float(payload.get("heading_deg"), "heading_deg", 0, 360),
        "groundspeed_mps": optional_bounded_float(payload.get("groundspeed_mps"), "groundspeed_mps", 0, 80),
        "battery_percent": optional_bounded_float(payload.get("battery_percent"), "battery_percent", 0, 100),
        "gps_fix_quality": text_field(payload.get("gps_fix_quality", "unknown"), "gps_fix_quality", max_length=40),
        "camera_heading_deg": optional_bounded_float(payload.get("camera_heading_deg"), "camera_heading_deg", 0, 360),
        "camera_pitch_deg": optional_bounded_float(payload.get("camera_pitch_deg"), "camera_pitch_deg", -180, 180),
        "source": text_field(payload.get("source", mission.get("source", "drone_operator_submission")), "source", max_length=120),
        "source_type": text_field(payload.get("source_type", "human_operated_drone"), "source_type", max_length=80),
        "visibility": public_visibility(payload.get("public_visibility", mission.get("visibility", "public"))),
        "public_visibility": payload.get("public_visibility", True),
        "created_at": utc_now(),
    }


def build_observation(mission: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    observation_type = require_choice(str(payload.get("observation_type")), OBSERVATION_TYPES, "observation_type")
    review_status = require_choice(str(payload.get("review_status", "unreviewed")), REVIEW_STATUSES, "review_status")
    species_source = payload.get("species_assessment_source")
    if species_source is not None:
        require_choice(str(species_source), SPECIES_ASSESSMENT_SOURCES, "species_assessment_source")
    media_ref_type = payload.get("media_reference_type")
    if media_ref_type is not None:
        require_choice(str(media_ref_type), MEDIA_REFERENCE_TYPES, "media_reference_type")
    analyst_review_status = payload.get("analyst_review_status")
    if analyst_review_status is not None:
        require_choice(str(analyst_review_status), ANALYST_REVIEW_STATUSES, "analyst_review_status")
    review_outcome = payload.get("review_outcome")
    if review_outcome is not None:
        require_choice(str(review_outcome), REVIEW_OUTCOMES, "review_outcome")
    lat = bounded_float(payload["latitude"], "latitude", -90, 90)
    lon = bounded_float(payload["longitude"], "longitude", -180, 180)
    confidence = max(0.0, min(1.0, float(payload.get("confidence", 0.35) or 0.35)))
    observation_id = text_field(payload.get("observation_id") or f"observation-{uuid4().hex[:12]}", "observation_id", max_length=80)
    doc = {
        "_id": observation_id,
        "observation_id": observation_id,
        "mission_id": mission["mission_id"],
        "drone_id": text_field(payload.get("drone_id", mission["drone_id"]), "drone_id", max_length=80),
        "timestamp": required_time(payload, "timestamp"),
        "latitude": lat,
        "longitude": lon,
        "location": point(lon, lat),
        "observation_type": observation_type,
        "count": bounded_int(payload.get("count", 0 if observation_type == "no_sighting_patrol_result" else 1), "count", 0 if observation_type == "no_sighting_patrol_result" else 1, 1000),
        "estimated_length_m": optional_bounded_float(payload.get("estimated_length_m"), "estimated_length_m", 0.1, 20),
        "probable_species": text_field(payload.get("probable_species"), "probable_species", max_length=120, default="") or None,
        "species_assessment_source": species_source,
        "species_confidence": optional_bounded_float(payload.get("species_confidence"), "species_confidence", 0, 1),
        "observed_behavior": text_field(payload.get("observed_behavior"), "observed_behavior", max_length=200, default="") or None,
        "behavior_source": text_field(payload.get("behavior_source"), "behavior_source", max_length=120, default="") or None,
        "evidence_type": text_field(payload.get("evidence_type"), "evidence_type", max_length=80, default="") or None,
        "media_reference": text_field(payload.get("media_reference"), "media_reference", max_length=500, default="") or None,
        "media_reference_type": media_ref_type,
        "media_timestamp": parse_time(payload["media_timestamp"]) if payload.get("media_timestamp") else None,
        "analyst_notes": text_field(payload.get("analyst_notes"), "analyst_notes", max_length=1000, default="") or None,
        "analyst_review_status": analyst_review_status or "unreviewed",
        "analyst_reviewed_at": parse_time(payload["analyst_reviewed_at"]) if payload.get("analyst_reviewed_at") else None,
        "analyst_reviewer_role": text_field(payload.get("analyst_reviewer_role"), "analyst_reviewer_role", max_length=80, default="") or None,
        "analyst_notes_private": text_field(payload.get("analyst_notes_private"), "analyst_notes_private", max_length=1000, default="") or None,
        "public_review_summary": text_field(payload.get("public_review_summary"), "public_review_summary", max_length=500, default="") or None,
        "review_outcome": review_outcome,
        "evidence_confidence": optional_bounded_float(payload.get("evidence_confidence"), "evidence_confidence", 0, 1),
        "confidence": confidence,
        "review_status": review_status,
        "source": text_field(payload.get("source", mission.get("source", "drone_operator_submission")), "source", max_length=120),
        "source_type": text_field(payload.get("source_type", "human_operated_drone"), "source_type", max_length=80),
        "visibility": public_visibility(payload.get("public_visibility", mission.get("visibility", "public"))),
        "public_visibility": payload.get("public_visibility", True),
        "internal_notes": text_field(payload.get("internal_notes"), "internal_notes", max_length=1000, default="") or None,
        "active_pack": mission.get("pack_id", "core"),
        "recommended_surveillance_pattern": mission.get("recommended_pattern", mission.get("mission_type")),
        "human_approved": mission.get("human_approved") is True,
        "autonomous_flight_control": False,
        "created_at": utc_now(),
    }
    return doc


def public_doc(doc: dict[str, Any]) -> dict[str, Any]:
    output = {key: value for key, value in doc.items() if key not in PUBLIC_DROP_FIELDS}
    output["_id"] = str(output.get("_id", doc.get("_id", "")))
    return output


def review_multiplier(status: str) -> float:
    return {
        "unreviewed": 0.45,
        "operator_reviewed": 0.65,
        "analyst_reviewed": 0.8,
        "confirmed": 1.0,
        "rejected": 0.0,
    }.get(status, 0.45)


def drone_observation_to_sighting(doc: dict[str, Any]) -> dict[str, Any] | None:
    if doc.get("visibility") != "public" or doc.get("review_status") == "rejected":
        return None
    if doc.get("observation_type") not in {"shark_sighting", "unknown_large_marine_animal"}:
        return None
    status = str(doc.get("review_status", "unreviewed"))
    return {
        "visibility": "public",
        "source": doc.get("source", "drone_observation"),
        "source_type": doc.get("source_type", "human_operated_drone"),
        "confidence": "verified" if status in {"analyst_reviewed", "confirmed"} else "unreviewed",
        "verified": status in {"analyst_reviewed", "confirmed"},
        "review_status": status,
        "observed_at": doc.get("timestamp"),
        "timestamp": doc.get("timestamp"),
        "location": doc.get("location"),
        "summary": f"Drone observation: {doc.get('observation_type')}",
        "probable_species": doc.get("probable_species"),
        "species_assessment_source": doc.get("species_assessment_source"),
        "species_confidence": doc.get("species_confidence"),
        "official_species_classification": doc.get("official_species_classification", "unknown"),
        "drone_observation_id": doc.get("observation_id"),
        "weight_hint": round(float(doc.get("confidence", 0.35)) * review_multiplier(status), 3),
    }


def observation_signal_type(observation_type: str) -> str:
    return {
        "shark_sighting": "shark_sighting",
        "unknown_large_marine_animal": "sighting",
        "baitfish_congregation": "baitfish_presence",
        "marine_mammal_activity": "seal_presence",
        "carcass": "whale_carcass",
        "water_clarity_observation": "water_clarity_context",
        "surf_line_activity": "human_exposure",
        "swimmer_density": "human_exposure",
        "vessel_activity": "vessel_activity",
        "no_sighting_patrol_result": "no_sighting_patrol_result",
        "other": "drone_observation",
    }.get(observation_type, "drone_observation")


def drone_observation_signal(doc: dict[str, Any]) -> dict[str, Any]:
    expires_at = parse_time(doc.get("timestamp")) + timedelta(hours=3)
    return {
        "visibility": "public",
        "signal_type": observation_signal_type(str(doc.get("observation_type"))),
        "timestamp": doc.get("timestamp"),
        "expires_at": expires_at,
        "value": doc.get("count", 1),
        "confidence": float(doc.get("confidence", 0.35)) * review_multiplier(str(doc.get("review_status", "unreviewed"))),
        "source": {"provider": "drone_observation_intake", "source_type": doc.get("source_type")},
        "location": doc.get("location"),
        "review_status": doc.get("review_status"),
        "mission_id": doc.get("mission_id"),
    }


def map_feed_item(doc: dict[str, Any], mission: dict[str, Any] | None = None) -> dict[str, Any]:
    timestamp = parse_time(doc.get("timestamp"))
    expires_at = timestamp + timedelta(hours=3)
    review_status = str(doc.get("review_status", "unreviewed"))
    observation_type = str(doc.get("observation_type"))
    no_sighting = observation_type == "no_sighting_patrol_result"
    return {
        "latitude": doc.get("latitude"),
        "longitude": doc.get("longitude"),
        "timestamp": timestamp.isoformat(),
        "observation_type": observation_type,
        "review_status": review_status,
        "confidence": doc.get("confidence"),
        "mission_id": doc.get("mission_id"),
        "source_type": doc.get("source_type", "human_operated_drone"),
        "active_pack": doc.get("active_pack") or (mission or {}).get("pack_id", "core"),
        "explanation_summary": "No-sighting patrol result reduces uncertainty only inside documented coverage and time window." if no_sighting else f"Drone {observation_type} report is source-attributed and review status is {review_status}.",
        "recommended_action": "Do not treat no-sighting patrol as proof of safety; continue official guidance." if no_sighting else "Review observation, source confidence, and local official guidance before operational escalation.",
        "recommended_surveillance_pattern": doc.get("recommended_surveillance_pattern") or (mission or {}).get("recommended_pattern", "manual_observation_patrol"),
        "expires_at": expires_at.isoformat(),
        "data_freshness": {"status": "fresh" if expires_at >= utc_now() else "stale", "source": "drone_observation_intake"},
    }
