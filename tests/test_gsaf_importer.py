from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api_v1 import router
from app.mongodb import get_database
from app.services.gsaf_importer import (
    build_baseline,
    compare_against_baseline,
    import_gsaf,
    read_gsaf_file,
    row_fingerprint,
)
from tests.test_public_api_privacy import FakeDB


IMPORTED_AT = "2026-06-25T00:00:00+00:00"


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    headers = [
        "Case Number",
        "Date",
        "Year",
        "Type",
        "Country",
        "Area",
        "Location",
        "Activity",
        "Sex",
        "Age",
        "Injury",
        "Fatal (Y/N)",
        "Time",
        "Species ",
        "Source",
        "pdf",
    ]
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(f'"{row.get(header, "")}"' for header in headers))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def fixture_rows() -> list[dict[str, str]]:
    return [
        {
            "Case Number": "2026.01.01",
            "Date": "2026-01-01",
            "Year": "2026",
            "Type": "Unprovoked",
            "Country": "USA",
            "Area": "Florida",
            "Location": "Test Beach",
            "Activity": "Surfing",
            "Sex": "M",
            "Age": "30",
            "Injury": "Laceration to foot",
            "Fatal (Y/N)": "N",
            "Time": "10h00",
            "Species ": "Blacktip shark",
            "Source": "Synthetic test fixture",
            "pdf": "case.pdf",
        },
        {
            "Case Number": "2026.01.02",
            "Date": "Summer 2026",
            "Year": "2026",
            "Type": "Questionable",
            "Country": "USA",
            "Area": "Florida",
            "Location": "Vague Beach",
            "Activity": "Swimming",
            "Injury": "Unconfirmed report",
            "Fatal (Y/N)": "N",
            "Source": "Unconfirmed synthetic source",
        },
    ]


class GsafImporterTests(unittest.TestCase):
    def test_parses_synthetic_csv_and_xlsx_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = root / "synthetic_gsaf.csv"
            xlsx_path = root / "synthetic_gsaf.xlsx"
            rows = fixture_rows()
            write_csv(csv_path, rows)
            pd.DataFrame(rows).to_excel(xlsx_path, index=False)

            csv_records, csv_malformed = read_gsaf_file(csv_path, imported_at=IMPORTED_AT)
            xlsx_records, xlsx_malformed = read_gsaf_file(xlsx_path, imported_at=IMPORTED_AT)

            self.assertEqual(csv_malformed, [])
            self.assertEqual(xlsx_malformed, [])
            self.assertEqual(len(csv_records), 2)
            self.assertEqual(len(xlsx_records), 2)
            self.assertEqual(csv_records[0]["source_file"], "synthetic_gsaf.csv")
            self.assertEqual(xlsx_records[0]["source_file"], "synthetic_gsaf.xlsx")
            self.assertEqual(csv_records[0]["date_normalized"], "2026-01-01")
            self.assertEqual(csv_records[0]["year"], 2026)

    def test_stable_fingerprint_generation_ignores_row_order_and_import_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "synthetic_gsaf.csv"
            write_csv(csv_path, [fixture_rows()[0]])
            first, _ = read_gsaf_file(csv_path, imported_at="2026-06-25T00:00:00+00:00")
            second, _ = read_gsaf_file(csv_path, imported_at="2026-06-26T00:00:00+00:00")
            second[0]["source_row_number"] = 99

            self.assertEqual(first[0]["row_fingerprint"], row_fingerprint(second[0]))

    def test_delta_detection_new_changed_removed_and_unchanged_rows(self):
        current = [
            {"match_key": "case:unchanged", "row_fingerprint": "same"},
            {"match_key": "case:changed", "row_fingerprint": "new-fingerprint"},
            {"match_key": "case:new", "row_fingerprint": "new"},
        ]
        baseline = {
            "case:unchanged": {"row_fingerprint": "same"},
            "case:changed": {"row_fingerprint": "old-fingerprint"},
            "case:removed": {"row_fingerprint": "gone"},
        }

        delta = compare_against_baseline(current, baseline)

        self.assertEqual(delta["new_rows"], 1)
        self.assertEqual(delta["changed_rows"], 1)
        self.assertEqual(delta["unchanged_rows"], 1)
        self.assertEqual(delta["possibly_removed_rows"], 1)

    def test_duplicate_case_number_detection_in_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = root / "synthetic_gsaf.csv"
            rows = fixture_rows()
            rows.append({**fixture_rows()[0], "Location": "Second Test Beach"})
            write_csv(csv_path, rows)

            report = import_gsaf(
                csv_path,
                staging_path=root / "staging.json",
                report_path=root / "report.json",
                baseline_path=root / "baseline.json",
                imported_at=IMPORTED_AT,
            )

            self.assertEqual(report["duplicate_case_numbers"], [{"case_number": "2026.01.01", "count": 2}])

    def test_malformed_source_rows_are_reported_without_staging_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = root / "synthetic_gsaf.csv"
            rows = fixture_rows() + [{"Sex": "M"}]
            write_csv(csv_path, rows)

            report = import_gsaf(
                csv_path,
                staging_path=root / "staging.json",
                report_path=root / "report.json",
                baseline_path=root / "baseline.json",
                imported_at=IMPORTED_AT,
            )
            staging = json.loads((root / "staging.json").read_text(encoding="utf-8"))

            self.assertEqual(report["malformed_rows"], 1)
            self.assertEqual(report["malformed_row_numbers"], [4])
            self.assertEqual(len(staging["records"]), 2)

    def test_vague_date_is_preserved_without_inventing_precise_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "synthetic_gsaf.csv"
            write_csv(csv_path, [fixture_rows()[1]])
            records, _ = read_gsaf_file(csv_path, imported_at=IMPORTED_AT)

            self.assertEqual(records[0]["source_date_raw"], "Summer 2026")
            self.assertIsNone(records[0]["date_normalized"])
            self.assertIn("date_vague_preserved", records[0]["normalization_warnings"])

    def test_questionable_records_remain_unknown_behavior(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "synthetic_gsaf.csv"
            write_csv(csv_path, [fixture_rows()[1]])
            records, _ = read_gsaf_file(csv_path, imported_at=IMPORTED_AT)

            self.assertEqual(records[0]["ai1sad_behavioral_hypothesis_candidate"], "unknown_insufficient_evidence")
            self.assertEqual(records[0]["ai1sad_behavior_confidence"], "unknown")
            self.assertTrue(records[0]["ai1sad_behavioral_hypothesis_provisional"])

    def test_behavior_mapping_does_not_default_to_mistaken_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "synthetic_gsaf.csv"
            row = {**fixture_rows()[0], "Activity": "Swimming", "Injury": "Minor bite to leg"}
            write_csv(csv_path, [row])
            records, _ = read_gsaf_file(csv_path, imported_at=IMPORTED_AT)

            self.assertNotEqual(records[0]["ai1sad_behavioral_hypothesis_candidate"], "mistaken_identity_candidate")
            self.assertEqual(records[0]["ai1sad_behavioral_hypothesis_candidate"], "unknown_insufficient_evidence")

    def test_competitive_food_response_for_spearfishing_bait_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "synthetic_gsaf.csv"
            row = {
                **fixture_rows()[0],
                "Activity": "Spearfishing with fish on stringer",
                "Injury": "Bitten after spearing fish near bait",
            }
            write_csv(csv_path, [row])
            records, _ = read_gsaf_file(csv_path, imported_at=IMPORTED_AT)

            self.assertEqual(records[0]["ai1sad_behavioral_hypothesis_candidate"], "competitive_food_response")
            self.assertEqual(records[0]["ai1sad_behavior_confidence"], "plausible")
            self.assertTrue(records[0]["ai1sad_behavioral_hypothesis_provisional"])

    def test_attempted_predation_candidate_remains_provisional(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "synthetic_gsaf.csv"
            row = {
                **fixture_rows()[0],
                "Injury": "FATAL, body not recovered after repeated engagement",
                "Fatal (Y/N)": "Y",
            }
            write_csv(csv_path, [row])
            records, _ = read_gsaf_file(csv_path, imported_at=IMPORTED_AT)

            self.assertEqual(records[0]["ai1sad_behavioral_hypothesis_candidate"], "attempted_predation_event")
            self.assertIn(records[0]["ai1sad_behavior_confidence"], {"weak", "plausible"})
            self.assertTrue(records[0]["ai1sad_behavioral_hypothesis_provisional"])
            self.assertIn("behavior_hypothesis_provisional", records[0]["normalization_warnings"])

    def test_import_writes_staging_report_and_optional_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = root / "synthetic_gsaf.csv"
            staging_path = root / "staging.json"
            report_path = root / "report.json"
            baseline_path = root / "baseline.json"
            write_csv(csv_path, fixture_rows())

            report = import_gsaf(
                csv_path,
                staging_path=staging_path,
                report_path=report_path,
                baseline_path=baseline_path,
                update_baseline=True,
                imported_at=IMPORTED_AT,
            )

            self.assertTrue(staging_path.exists())
            self.assertTrue(report_path.exists())
            self.assertTrue(baseline_path.exists())
            self.assertTrue(report["baseline_updated"])
            self.assertEqual(report["total_rows"], 2)
            self.assertEqual(json.loads(staging_path.read_text(encoding="utf-8"))["records"][0]["source_name"], "GSAF")
            self.assertEqual(json.loads(baseline_path.read_text(encoding="utf-8"))["source_name"], "GSAF")

    def test_baseline_builder_uses_match_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "synthetic_gsaf.csv"
            write_csv(csv_path, fixture_rows())
            records, _ = read_gsaf_file(csv_path, imported_at=IMPORTED_AT)
            baseline = build_baseline(records, generated_at=IMPORTED_AT)

            self.assertIn(records[0]["match_key"], baseline["rows"])
            self.assertEqual(
                baseline["rows"][records[0]["match_key"]]["row_fingerprint"],
                records[0]["row_fingerprint"],
            )

    def test_importer_does_not_write_replay_scoring_or_public_feed_systems(self):
        db = FakeDB()
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_database] = lambda: db
        client = TestClient(app)

        warning_before = client.get("/api/v1/warnings/location?lat=25&lon=-80&bypass_cache=true").json()
        replay_before = client.get("/api/v1/replay/library").json()
        feed_before = client.get("/api/v1/drone/surveillance-feed").json()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = root / "synthetic_gsaf.csv"
            write_csv(csv_path, fixture_rows())
            report = import_gsaf(
                csv_path,
                staging_path=root / "staging.json",
                report_path=root / "report.json",
                baseline_path=root / "baseline.json",
                imported_at=IMPORTED_AT,
            )

        warning_after = client.get("/api/v1/warnings/location?lat=25&lon=-80&bypass_cache=true").json()
        replay_after = client.get("/api/v1/replay/library").json()
        feed_after = client.get("/api/v1/drone/surveillance-feed").json()

        self.assertFalse(any(report["side_effects"].values()))
        self.assertEqual(warning_before["warning_score"], warning_after["warning_score"])
        self.assertEqual(warning_before["warning_band"], warning_after["warning_band"])
        self.assertEqual([item["id"] for item in replay_before["results"]], [item["id"] for item in replay_after["results"]])
        self.assertEqual(len(feed_before["results"]), len(feed_after["results"]))
        self.assertEqual(
            feed_before["surveillance"]["zones"][0]["surveillance_priority_score"],
            feed_after["surveillance"]["zones"][0]["surveillance_priority_score"],
        )


if __name__ == "__main__":
    unittest.main()
