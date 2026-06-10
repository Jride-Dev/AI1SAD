from __future__ import annotations

import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from app.replay.runner import ReplayRunner
from app.replay.scenarios import REPLAY_SCENARIOS


class PanamaCityDroneReplayTests(unittest.TestCase):
    def test_panama_city_fixture_preserves_analyst_probable_species_metadata(self):
        scenario = REPLAY_SCENARIOS["nsa_panama_city_florida_2026_drone_observation"]
        observation = scenario.drone_observations[0]
        self.assertEqual(observation["official_species_classification"], "unknown")
        self.assertEqual(observation["probable_species"], "bull shark")
        self.assertEqual(observation["scientific_name"], "Carcharhinus leucas")
        self.assertEqual(observation["species_assessment_source"], "analyst_visual_assessment")
        self.assertTrue(observation["human_approved"])
        self.assertFalse(observation["autonomous_flight_control"])

    def test_panama_city_replay_uses_drone_observation_without_direct_species_points(self):
        scenario = REPLAY_SCENARIOS["nsa_panama_city_florida_2026_drone_observation"]
        result = ReplayRunner().run_scenario(scenario)
        self.assertIsNone(result.error)
        zone = result.surveillance["zones"][0]
        self.assertIn("sighting_reports", zone["data_sources_used"])
        factors = zone["dominant_factors"]
        self.assertFalse(any(factor.get("factor") == "regional_species_match" for factor in factors))

    def test_case_study_artifacts_parse(self):
        root = Path(__file__).resolve().parents[1]
        for name in [
            "nsa_panama_city_florida_2026_replay.json",
            "nsa_panama_city_florida_2026_factor_summary.json",
        ]:
            with (root / "docs" / "assets" / "case_studies" / name).open("r", encoding="utf-8") as handle:
                json.load(handle)
        ET.parse(root / "docs" / "assets" / "case_studies" / "nsa_panama_city_florida_2026_heatmap.svg")

