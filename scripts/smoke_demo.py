from __future__ import annotations

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def fetch_json(base_url: str, path: str) -> tuple[int, dict]:
    url = f"{base_url.rstrip('/')}{path}"
    request = Request(url, headers={"accept": "application/json"})
    with urlopen(request, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
        return response.status, payload


def check(base_url: str, label: str, path: str, required_keys: list[str]) -> bool:
    try:
        status, payload = fetch_json(base_url, path)
    except HTTPError as exc:
        print(f"FAIL {label}: HTTP {exc.code}")
        return False
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"FAIL {label}: {exc}")
        return False

    missing = [key for key in required_keys if key not in payload]
    if status != 200 or missing:
        print(f"FAIL {label}: status={status} missing={missing}")
        return False
    print(f"OK   {label}: {path}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check an AI1SAD public demo backend.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for the AI1SAD backend.")
    args = parser.parse_args()

    explain_query = urlencode(
        {
            "lat": -31.9827,
            "lon": 115.5153,
            "radius_km": 10,
            "activity_context": "spearfishing",
            "suspected_species": "white shark",
        }
    )
    checks = [
        ("health", "/health", ["status"]),
        ("demo status", "/api/v1/demo/status", ["demo_mode", "private_internal_data_exposed", "disclaimer"]),
        ("demo scenarios", "/api/v1/demo/scenarios", ["scenarios", "private_internal_data_exposed", "disclaimer"]),
        ("explain location", f"/api/v1/explain/location?{explain_query}", ["warning_score", "surveillance_priority_score", "disclaimer"]),
    ]

    results = [check(args.base_url, label, path, keys) for label, path, keys in checks]
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
