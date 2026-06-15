from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.config import get_settings
from app.services.drone_observations import optional_bounded_float, parse_time, text_field


MEDIA_KINDS = {"image", "video", "telemetry_snapshot", "observation_note", "agency_report_reference", "unknown"}
REVIEW_VISIBILITIES = {"private_internal", "analyst_only", "operator_visible", "public_summary_only"}
PUBLIC_RELEASE_STATUSES = {"not_reviewed", "approved_analyst_only", "restricted", "retained", "inconclusive"}
ATTACHMENT_REVIEW_STATUSES = {"unreviewed", "needs_review", "in_review", "reviewed", "rejected", "inconclusive"}
MEDIA_REFERENCE_TYPES = {"local_filename", "camera_card_reference", "agency_evidence_id", "private_case_reference", "none"}
SAFE_MIME_PREFIXES = ("image/", "video/", "text/plain", "application/json")
BLOCKED_MIME_TERMS = ("javascript", "script", "executable", "x-msdownload", "x-sh", "x-bat", "x-msdos-program")
BLOCKED_FILENAME_EXTENSIONS = {
    ".bat",
    ".cmd",
    ".com",
    ".dll",
    ".exe",
    ".hta",
    ".jar",
    ".js",
    ".jse",
    ".mjs",
    ".msi",
    ".php",
    ".ps1",
    ".scr",
    ".sh",
    ".vbe",
    ".vbs",
    ".wsf",
}

ATTACHMENT_PRIVATE_FIELDS = {
    "storage_key",
    "stored_filename",
    "original_filename",
    "checksum_sha256",
    "uploaded_by_role",
    "internal_notes",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def require_choice(value: Any, allowed: set[str], field: str) -> str:
    text = str(value or "").strip()
    if text not in allowed:
        raise ValueError(f"{field} must be one of: {', '.join(sorted(allowed))}")
    return text


def optional_choice(value: Any, allowed: set[str], field: str, default: str) -> str:
    if value in {None, ""}:
        return default
    return require_choice(value, allowed, field)


def bounded_int(value: Any, field: str, minimum: int, maximum: int) -> int | None:
    if value in {None, ""}:
        return None
    result = int(value)
    if result < minimum or result > maximum:
        raise ValueError(f"{field} must be between {minimum} and {maximum}")
    return result


def safe_identifier(value: Any, field: str, *, default_prefix: str) -> str:
    text = text_field(value, field, max_length=80, default="")
    if not text:
        text = f"{default_prefix}-{uuid4().hex[:12]}"
    if not re.fullmatch(r"[A-Za-z0-9_-]+", text):
        raise ValueError(f"{field} must contain only letters, numbers, underscores, or hyphens")
    return text


def validate_storage_root() -> Path:
    root = Path(get_settings().media_attachments_storage_root).expanduser()
    if not root.is_absolute():
        root = Path.cwd() / root
    resolved = root.resolve()
    blocked = [
        (Path.cwd() / "docs").resolve(),
        (Path.cwd() / "site").resolve(),
        (Path.cwd() / "frontend" / "dist").resolve(),
        (Path.cwd() / "frontend" / "public").resolve(),
    ]
    if any(resolved == path or path in resolved.parents for path in blocked):
        raise ValueError("MEDIA_ATTACHMENTS_STORAGE_ROOT cannot be inside docs, site, or frontend public/build directories")
    return resolved


def safe_filename(value: Any, field: str, *, default_suffix: str = ".metadata") -> str:
    text = text_field(value, field, max_length=180, default="")
    if not text:
        return f"{uuid4().hex}{default_suffix}"
    if re.match(r"^[A-Za-z]:[\\/]", text):
        raise ValueError(f"{field} must be a filename only")
    candidate = Path(text)
    if candidate.is_absolute() or len(candidate.parts) != 1 or ".." in text:
        raise ValueError(f"{field} must be a filename only")
    if not re.fullmatch(r"[A-Za-z0-9._ -]+", text):
        raise ValueError(f"{field} contains unsupported characters")
    if candidate.suffix.lower() in BLOCKED_FILENAME_EXTENSIONS:
        raise ValueError(f"{field} has an unsupported executable or script extension")
    return text


def validate_mime_type(value: Any) -> str | None:
    text = text_field(value, "mime_type", max_length=120, default="")
    if not text:
        return None
    lowered = text.lower()
    if any(term in lowered for term in BLOCKED_MIME_TERMS):
        raise ValueError("mime_type is not allowed for local attachment metadata")
    if not any(lowered == prefix or lowered.startswith(prefix) for prefix in SAFE_MIME_PREFIXES):
        raise ValueError("mime_type must be image, video, text/plain, or application/json")
    return lowered


def validate_checksum(value: Any) -> str | None:
    text = text_field(value, "checksum_sha256", max_length=64, default="")
    if not text:
        return None
    if not re.fullmatch(r"[A-Fa-f0-9]{64}", text):
        raise ValueError("checksum_sha256 must be a 64-character hexadecimal SHA-256 value")
    return text.lower()


def metadata_checksum(payload: dict[str, Any]) -> str:
    basis = "|".join(
        str(payload.get(key, ""))
        for key in ["observation_id", "mission_id", "media_kind", "original_filename", "mime_type", "file_size_bytes"]
    )
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def build_attachment(observation: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    validate_storage_root()
    attachment_id = safe_identifier(payload.get("attachment_id"), "attachment_id", default_prefix="attachment")
    media_kind = optional_choice(payload.get("media_kind"), MEDIA_KINDS, "media_kind", "unknown")
    review_visibility = optional_choice(payload.get("review_visibility"), REVIEW_VISIBILITIES, "review_visibility", "analyst_only")
    public_release_status = optional_choice(payload.get("public_release_status"), PUBLIC_RELEASE_STATUSES, "public_release_status", "not_reviewed")
    media_reference_type = optional_choice(payload.get("media_reference_type"), MEDIA_REFERENCE_TYPES, "media_reference_type", "none")
    original_filename = safe_filename(payload.get("original_filename"), "original_filename")
    stored_filename = f"{attachment_id}-{safe_filename(payload.get('stored_filename') or original_filename, 'stored_filename')}"
    doc = {
        "_id": attachment_id,
        "attachment_id": attachment_id,
        "observation_id": observation["observation_id"],
        "mission_id": observation["mission_id"],
        "media_reference_type": media_reference_type,
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "storage_backend": "local_private_filesystem",
        "storage_key": f"metadata/{observation['observation_id']}/{attachment_id}",
        "media_kind": media_kind,
        "mime_type": validate_mime_type(payload.get("mime_type")),
        "file_size_bytes": bounded_int(payload.get("file_size_bytes"), "file_size_bytes", 0, 500_000_000),
        "captured_at": validate_timestamp(payload.get("captured_at")),
        "uploaded_at": utc_now(),
        "uploaded_by_role": text_field(payload.get("uploaded_by_role"), "uploaded_by_role", max_length=80, default="operator") or "operator",
        "review_visibility": review_visibility,
        "public_release_status": public_release_status,
        "checksum_sha256": validate_checksum(payload.get("checksum_sha256")),
        "analyst_review_status": optional_choice(payload.get("analyst_review_status"), ATTACHMENT_REVIEW_STATUSES, "analyst_review_status", "unreviewed"),
        "public_summary": text_field(payload.get("public_summary"), "public_summary", max_length=500, default="") or None,
        "evidence_confidence": optional_bounded_float(payload.get("evidence_confidence"), "evidence_confidence", 0, 1),
        "internal_notes": text_field(payload.get("internal_notes"), "internal_notes", max_length=1000, default="") or None,
        "attachment_scope": "metadata_only_local",
        "media_analysis_performed": False,
        "sighting_created": False,
        "public_feed_exposed": False,
    }
    doc["checksum_sha256"] = doc["checksum_sha256"] or metadata_checksum(doc)
    return doc


def validate_timestamp(value: Any) -> datetime | None:
    if value in {None, ""}:
        return None
    try:
        return parse_time(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("captured_at must be a valid timestamp") from exc


def attachment_response_doc(doc: dict[str, Any]) -> dict[str, Any]:
    output = {key: value for key, value in doc.items() if key not in ATTACHMENT_PRIVATE_FIELDS}
    output["_id"] = str(output.get("_id", doc.get("_id", "")))
    output["private_by_default"] = True
    output["public_feed_exposed"] = False
    output["media_analysis_performed"] = False
    output["sighting_created"] = False
    return output


def update_attachment_review(doc: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    updates: dict[str, Any] = {}
    if "analyst_review_status" in payload:
        updates["analyst_review_status"] = optional_choice(payload.get("analyst_review_status"), ATTACHMENT_REVIEW_STATUSES, "analyst_review_status", doc.get("analyst_review_status", "unreviewed"))
    if "review_visibility" in payload:
        updates["review_visibility"] = optional_choice(payload.get("review_visibility"), REVIEW_VISIBILITIES, "review_visibility", doc.get("review_visibility", "analyst_only"))
    if "public_release_status" in payload:
        updates["public_release_status"] = optional_choice(payload.get("public_release_status"), PUBLIC_RELEASE_STATUSES, "public_release_status", doc.get("public_release_status", "not_reviewed"))
    if "public_summary" in payload:
        updates["public_summary"] = text_field(payload.get("public_summary"), "public_summary", max_length=500, default="") or None
    if "evidence_confidence" in payload:
        updates["evidence_confidence"] = optional_bounded_float(payload.get("evidence_confidence"), "evidence_confidence", 0, 1)
    if not updates:
        raise ValueError("No valid attachment review fields to update")
    updates["reviewed_at"] = utc_now()
    return {**doc, **updates}
