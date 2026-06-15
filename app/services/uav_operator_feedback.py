from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.services.drone_observations import text_field


SUBMITTER_ROLES = {
    "uav_operator",
    "lifeguard",
    "coastal_authority",
    "researcher",
    "agency_staff",
    "citizen_scientist",
    "project_owner",
    "unknown",
}
ORGANIZATION_TYPES = {
    "government",
    "lifeguard_service",
    "research",
    "nonprofit",
    "private_operator",
    "volunteer",
    "independent",
    "unknown",
}
REVIEW_STATUSES = {"new", "triaged", "needs_follow_up", "accepted_requirement", "rejected", "archived"}
TELEMETRY_AVAILABLE = {"none", "unknown", "app_only", "export_file", "mavlink", "vendor_sdk", "manual_notes"}
MEDIA_WORKFLOWS = {
    "none",
    "sd_card",
    "app_gallery",
    "screen_recording",
    "agency_evidence_system",
    "external_reference",
    "local_reference_only",
    "unknown",
}

PRIVATE_FIELDS = {
    "contact_reference",
    "internal_notes_private",
    "reviewed_at",
    "reviewer_role",
}

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*[A-Za-z0-9_.-]{12,}"),
]
CONTACT_PATTERNS = [
    re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\+?\d[\d .()/-]{7,}\d"),
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def require_choice(value: Any, allowed: set[str], field: str) -> str:
    text = str(value or "").strip()
    if text not in allowed:
        raise ValueError(f"{field} must be one of: {', '.join(sorted(allowed))}")
    return text


def optional_choice(value: Any, allowed: set[str], field: str, default: str) -> str:
    if value is None or value == "":
        return default
    return require_choice(value, allowed, field)


def safe_identifier(value: Any, field: str, *, prefix: str) -> str:
    text = text_field(value, field, max_length=90, default="")
    if not text:
        text = f"{prefix}-{uuid4().hex[:12]}"
    if not re.fullmatch(r"[A-Za-z0-9_-]+", text):
        raise ValueError(f"{field} must contain only letters, numbers, underscores, or hyphens")
    return text


def bounded_text(value: Any, field: str, max_length: int, default: str = "") -> str:
    text = text_field(value, field, max_length=max_length, default=default)
    reject_secret_like_text(text, field)
    return text


def safe_region(value: Any, field: str) -> str | None:
    text = bounded_text(value, field, 120)
    if not text:
        return None
    if not re.fullmatch(r"[A-Za-z0-9 .,'()/&-]+", text):
        raise ValueError(f"{field} contains unsupported characters")
    return text


def safe_country(value: Any) -> str | None:
    text = bounded_text(value, "country", 80)
    if not text:
        return None
    if not re.fullmatch(r"[A-Za-z .'-]+", text):
        raise ValueError("country contains unsupported characters")
    return text


def bool_field(value: Any, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    raise ValueError("boolean field must be true or false")


def list_field(value: Any, field: str, *, max_items: int = 20, max_item_length: int = 80) -> list[str]:
    if value is None or value == "":
        return []
    items = value if isinstance(value, list) else [value]
    if len(items) > max_items:
        raise ValueError(f"{field} must contain at most {max_items} items")
    output: list[str] = []
    for item in items:
        text = bounded_text(item, field, max_item_length)
        if text:
            output.append(text)
    return output


def reject_secret_like_text(value: str, field: str) -> None:
    if not value:
        return
    if any(pattern.search(value) for pattern in SECRET_PATTERNS):
        raise ValueError(f"{field} appears to contain a secret or API key")


def reject_public_contact_or_secret(value: str) -> None:
    if not value:
        return
    reject_secret_like_text(value, "public_summary")
    if any(pattern.search(value) for pattern in CONTACT_PATTERNS):
        raise ValueError("public_summary must not include contact details")


def validate_contact_reference(value: Any) -> str | None:
    text = bounded_text(value, "contact_reference", 240)
    if not text:
        return None
    lowered = text.lower()
    if lowered.startswith(("http://", "javascript:", "data:", "file:", "ftp:")):
        raise ValueError("contact_reference must not contain unsafe URL schemes")
    return text


def build_feedback(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    feedback_id = safe_identifier(payload.get("feedback_id"), "feedback_id", prefix="feedback")
    public_summary = bounded_text(payload.get("public_summary"), "public_summary", 500)
    reject_public_contact_or_secret(public_summary)
    doc = {
        "_id": feedback_id,
        "feedback_id": feedback_id,
        "submitted_at": utc_now(),
        "submitter_role": optional_choice(payload.get("submitter_role"), SUBMITTER_ROLES, "submitter_role", "unknown"),
        "organization_type": optional_choice(payload.get("organization_type"), ORGANIZATION_TYPES, "organization_type", "unknown"),
        "region": safe_region(payload.get("region"), "region"),
        "country": safe_country(payload.get("country")),
        "contact_allowed": bool_field(payload.get("contact_allowed"), False),
        "contact_reference": validate_contact_reference(payload.get("contact_reference")),
        "drone_platform": bounded_text(payload.get("drone_platform"), "drone_platform", 120) or None,
        "drone_model": bounded_text(payload.get("drone_model"), "drone_model", 120) or None,
        "flight_app": bounded_text(payload.get("flight_app"), "flight_app", 120) or None,
        "telemetry_available": optional_choice(payload.get("telemetry_available"), TELEMETRY_AVAILABLE, "telemetry_available", "unknown"),
        "telemetry_export_format": bounded_text(payload.get("telemetry_export_format"), "telemetry_export_format", 120) or None,
        "media_workflow": optional_choice(payload.get("media_workflow"), MEDIA_WORKFLOWS, "media_workflow", "unknown"),
        "no_sighting_patrols_logged": bool_field(payload.get("no_sighting_patrols_logged"), False),
        "observation_fields_used": list_field(payload.get("observation_fields_used"), "observation_fields_used"),
        "privacy_constraints": list_field(payload.get("privacy_constraints"), "privacy_constraints", max_item_length=120),
        "controlled_airspace_notes": bounded_text(payload.get("controlled_airspace_notes"), "controlled_airspace_notes", 600) or None,
        "operator_pain_points": list_field(payload.get("operator_pain_points"), "operator_pain_points", max_item_length=160),
        "requested_features": list_field(payload.get("requested_features"), "requested_features", max_item_length=160),
        "suggested_observation_types": list_field(payload.get("suggested_observation_types"), "suggested_observation_types"),
        "workflow_notes": bounded_text(payload.get("workflow_notes"), "workflow_notes", 1200) or None,
        "public_summary": public_summary or None,
        "internal_notes_private": bounded_text(payload.get("internal_notes_private"), "internal_notes_private", 1200) or None,
        "review_status": optional_choice(payload.get("review_status"), REVIEW_STATUSES, "review_status", "new"),
        "reviewed_at": None,
        "reviewer_role": None,
        "requirements_tags": list_field(payload.get("requirements_tags"), "requirements_tags"),
        "research_input_only": True,
        "creates_sighting": False,
        "creates_public_alert": False,
        "alters_scoring": False,
        "alters_replay": False,
    }
    return doc


def public_feedback_doc(doc: dict[str, Any]) -> dict[str, Any]:
    output = {key: value for key, value in doc.items() if key not in PRIVATE_FIELDS and not key.startswith("_")}
    output["research_input_only"] = True
    output["creates_sighting"] = False
    output["creates_public_alert"] = False
    output["alters_scoring"] = False
    output["alters_replay"] = False
    return output


def update_feedback_status(doc: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    updates: dict[str, Any] = {}
    if "review_status" in payload:
        updates["review_status"] = optional_choice(payload.get("review_status"), REVIEW_STATUSES, "review_status", doc.get("review_status", "new"))
    if "requirements_tags" in payload:
        updates["requirements_tags"] = list_field(payload.get("requirements_tags"), "requirements_tags")
    if "internal_notes_private" in payload:
        updates["internal_notes_private"] = bounded_text(payload.get("internal_notes_private"), "internal_notes_private", 1200) or None
    if "reviewer_role" in payload:
        updates["reviewer_role"] = bounded_text(payload.get("reviewer_role"), "reviewer_role", 80) or None
    if not updates:
        raise ValueError("No valid feedback review fields to update")
    updates["reviewed_at"] = utc_now()
    return {**doc, **updates}
