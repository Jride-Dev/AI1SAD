"""Generate a local-only HTML view of internal AI1SAD registry cases."""

from __future__ import annotations

import argparse
import html
import json
import webbrowser
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.mongodb import COLLECTIONS, get_database
from app.services.incident_registry import registry_side_effects
from app.services.incident_registry_cases import real_world_registry_records


DEFAULT_OUTPUT = Path("reports/ai1sad_incident_registry.html")


def build_registry_view_model(*, include_mongo: bool = True) -> dict[str, Any]:
    records = [record.model_dump(mode="json") for record in real_world_registry_records()]
    mongo = {
        "configured": bool(get_settings().mongodb_uri),
        "connected": False,
        "database": get_settings().mongodb_database,
        "archival_source_count": 0,
        "linked_archival_source_count": 0,
        "message": "MongoDB is not configured; showing repository registry cases.",
    }

    if include_mongo and mongo["configured"]:
        try:
            database = get_database()
            database.client.admin.command("ping")
            collection = database[COLLECTIONS["archival_sources"]]
            case_ids = [record["ai1sad_case_id"] for record in records]
            mongo.update(
                {
                    "connected": True,
                    "archival_source_count": collection.count_documents({}),
                    "linked_archival_source_count": collection.count_documents(
                        {"linked_ai1sad_case_id": {"$in": case_ids}}
                    ),
                    "message": "Connected to MongoDB.",
                }
            )
        except Exception as exc:
            mongo["message"] = f"MongoDB could not be reached: {type(exc).__name__}"

    return {
        "records": records,
        "record_count": len(records),
        "mongo": mongo,
        "side_effects": registry_side_effects(),
    }


def _json_for_script(value: Any) -> str:
    return (
        json.dumps(value, ensure_ascii=True)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def render_registry_html(view_model: dict[str, Any]) -> str:
    payload = _json_for_script(view_model)
    title = html.escape("AI1SAD Shark-Human Incident Registry")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{ color-scheme: light; font-family: Inter, Segoe UI, sans-serif; color: #172334; background: #edf4f6; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-width: 320px; background: #edf4f6; }}
    header {{ background: #071f2b; color: #f6fbfc; padding: 24px clamp(20px, 5vw, 72px); border-bottom: 4px solid #14a3a6; }}
    header p {{ margin: 6px 0 0; color: #b9d9de; }}
    h1 {{ margin: 0; font-size: clamp(24px, 3vw, 38px); letter-spacing: 0; }}
    h2 {{ margin: 0 0 14px; font-size: 20px; letter-spacing: 0; }}
    h3 {{ margin: 22px 0 8px; font-size: 15px; letter-spacing: 0; text-transform: uppercase; color: #536675; }}
    main {{ width: min(1180px, calc(100% - 32px)); margin: 24px auto 48px; display: grid; gap: 16px; }}
    .status {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1px; background: #cad8dc; border: 1px solid #cad8dc; }}
    .metric {{ background: #fff; padding: 16px; min-height: 84px; }}
    .metric strong {{ display: block; font-size: 24px; color: #0b7779; }}
    .metric span {{ color: #5d6d78; font-size: 13px; }}
    .case {{ background: #fff; border: 1px solid #cad8dc; border-radius: 6px; overflow: hidden; }}
    .case-head {{ display: flex; justify-content: space-between; gap: 20px; padding: 20px; border-bottom: 1px solid #dbe5e8; }}
    .case-head p {{ margin: 6px 0 0; color: #60717d; }}
    .badges {{ display: flex; flex-wrap: wrap; gap: 8px; align-content: flex-start; justify-content: flex-end; }}
    .badge {{ padding: 5px 8px; border-radius: 4px; background: #e6f4f4; color: #075f61; font-size: 12px; font-weight: 700; white-space: nowrap; }}
    .badge.restricted {{ background: #fff0d9; color: #8b4e00; }}
    .case-body {{ padding: 20px; }}
    .facts {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); border: 1px solid #dbe5e8; }}
    .fact {{ padding: 13px; border-right: 1px solid #dbe5e8; }}
    .fact:last-child {{ border-right: 0; }}
    .fact span {{ display: block; color: #6c7d88; font-size: 11px; text-transform: uppercase; margin-bottom: 4px; }}
    .grid {{ display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(280px, .65fr); gap: 20px; }}
    .callout {{ border-left: 4px solid #14a3a6; padding: 12px 14px; background: #eef8f8; line-height: 1.55; }}
    .warning {{ border-left-color: #d38418; background: #fff8e9; }}
    ul {{ margin: 8px 0; padding-left: 20px; }}
    li {{ margin: 7px 0; line-height: 1.45; }}
    .source {{ padding: 12px 0; border-top: 1px solid #e1e9eb; }}
    .source:first-of-type {{ border-top: 0; }}
    .source a {{ color: #087b7d; font-weight: 700; text-decoration-thickness: 1px; }}
    .source small {{ display: block; color: #657681; margin-top: 4px; }}
    .empty {{ color: #6b7c87; font-style: italic; }}
    footer {{ color: #63737e; font-size: 12px; text-align: center; padding: 12px; }}
    @media (max-width: 820px) {{ .status, .facts {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} .grid {{ grid-template-columns: 1fr; }} .case-head {{ display: block; }} .badges {{ justify-content: flex-start; margin-top: 12px; }} }}
    @media (max-width: 480px) {{ .status, .facts {{ grid-template-columns: 1fr; }} .fact {{ border-right: 0; border-bottom: 1px solid #dbe5e8; }} }}
  </style>
</head>
<body>
  <header>
    <h1>{title}</h1>
    <p>Local internal review view. Registry evidence does not create warnings, alerts, scoring, replay facts, or public-feed entries.</p>
  </header>
  <main>
    <section class="status" id="status"></section>
    <div id="cases"></div>
  </main>
  <footer>Generated locally from the repository registry schema and configured MongoDB metadata.</footer>
  <script>
    const data = {payload};
    const esc = (value) => String(value ?? "").replace(/[&<>"']/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}}[c]));
    const label = (value) => esc(String(value ?? "unknown").replaceAll("_", " "));
    const list = (items) => items?.length ? `<ul>${{items.map(item => `<li>${{esc(item)}}</li>`).join("")}}</ul>` : '<p class="empty">None recorded.</p>';
    const sources = (items) => items.map(source => `<div class="source"><a href="${{esc(source.source_url)}}" target="_blank" rel="noreferrer">${{esc(source.source_name || source.source_id)}}</a><small>${{esc(source.source_date || "Date not recorded")}} | ${{esc(source.source_title || source.source_id)}}</small><small>Supports: ${{(source.linked_claims || []).map(label).join(", ")}}</small></div>`).join("");
    document.getElementById("status").innerHTML = `
      <div class="metric"><strong>${{data.record_count}}</strong><span>Registry cases</span></div>
      <div class="metric"><strong>${{data.mongo.connected ? "Connected" : "Offline"}}</strong><span>MongoDB | ${{esc(data.mongo.database)}}</span></div>
      <div class="metric"><strong>${{data.mongo.archival_source_count}}</strong><span>Archival source records</span></div>
      <div class="metric"><strong>${{data.mongo.linked_archival_source_count}}</strong><span>Sources linked to shown cases</span></div>`;
    document.getElementById("cases").innerHTML = data.records.map(record => `
      <article class="case">
        <div class="case-head">
          <div><h2>${{esc(record.location)}} | ${{esc(record.incident_date_normalized)}}</h2><p>${{esc(record.ai1sad_case_id)}}</p></div>
          <div class="badges"><span class="badge restricted">${{label(record.public_visibility)}}</span><span class="badge">${{label(record.review_status)}}</span><span class="badge">Species: ${{label(record.official_species_status)}}</span></div>
        </div>
        <div class="case-body">
          <div class="facts">
            <div class="fact"><span>Victim</span><strong>${{esc(record.victim_context)}}</strong></div>
            <div class="fact"><span>Activity</span><strong>${{label(record.activity)}}</strong></div>
            <div class="fact"><span>Time</span><strong>${{esc(record.incident_time_raw)}}</strong></div>
            <div class="fact"><span>Fatality</span><strong>${{record.fatality ? "Fatal" : "Non-fatal"}}</strong></div>
          </div>
          <div class="grid">
            <div>
              <h3>Incident summary</h3><p class="callout">${{esc(record.public_summary)}}</p>
              <h3>Injury and condition</h3><p>${{esc(record.injury_summary)}}</p>
              <h3>Rescue and event sequence</h3><p>${{esc(record.human_group_context)}}</p>
              <h3>Evidence notes</h3>${{list(record.provenance_notes)}}
              <h3>Sources</h3>${{sources(record.source_links || [])}}
            </div>
            <aside>
              <h3>Species status</h3><p class="callout warning">${{esc(record.official_species_public_note)}}</p>
              <p><strong>Internal species hypotheses:</strong> ${{record.internal_species_hypotheses?.length || 0}}</p>
              <h3>Behavior</h3><p><strong>Primary:</strong> ${{label(record.primary_behavioral_hypothesis)}}</p><p><strong>Confidence:</strong> ${{label(record.behavioral_confidence)}}</p>
              <p><strong>Provisional alternatives:</strong></p>${{list((record.alternative_hypotheses || []).map(value => value.replaceAll("_", " ")))}}
              <h3>Boundaries</h3>${{list(Object.entries(data.side_effects).filter(([, enabled]) => !enabled).map(([name]) => name.replaceAll("_", " ")))}}
            </aside>
          </div>
        </div>
      </article>`).join("");
  </script>
</body>
</html>
"""


def write_registry_view(output: Path = DEFAULT_OUTPUT, *, include_mongo: bool = True) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_registry_html(build_registry_view_model(include_mongo=include_mongo)), encoding="utf-8")
    return output.resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Open the local AI1SAD incident registry viewer.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--no-mongo", action="store_true")
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args(argv)

    output = write_registry_view(args.output, include_mongo=not args.no_mongo)
    print(f"AI1SAD registry view: {output}")
    if not args.no_open:
        webbrowser.open(output.as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
