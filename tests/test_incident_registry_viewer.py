from __future__ import annotations

from app.services.incident_registry_viewer import build_registry_view_model, render_registry_html


def test_local_registry_view_renders_real_case_without_side_effects() -> None:
    view_model = build_registry_view_model(include_mongo=False)
    rendered = render_registry_html(view_model)

    assert view_model["record_count"] == 1
    assert "AI1SAD-WA-GLENFIELD-BEACH-2026-09-14" in rendered
    assert "Mel Ismail" in rendered
    assert "Glenfield Beach" in rendered
    assert "unconfirmed" in rendered
    assert "unknown_insufficient_evidence" in rendered
    assert view_model["side_effects"]["creates_alerts"] is False
    assert view_model["side_effects"]["alters_scoring"] is False


def test_local_registry_view_escapes_embedded_script_content() -> None:
    view_model = build_registry_view_model(include_mongo=False)
    view_model["records"][0]["public_summary"] = "</script><script>alert('no')</script>"

    rendered = render_registry_html(view_model)

    assert "</script><script>alert('no')</script>" not in rendered
    assert "\\u003c/script\\u003e" in rendered
