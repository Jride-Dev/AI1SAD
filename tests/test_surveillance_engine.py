import unittest
from datetime import datetime, timezone

from app.risk_model import REGIONAL_RISK_PROFILES
from app.services.surveillance_engine import SURVEILLANCE_DISCLAIMER, score_surveillance_zones


class SurveillanceEngineTests(unittest.TestCase):
    def test_recent_interaction_increases_nearby_zone_priority(self):
        baseline = score_surveillance_zones(
            lat=25,
            lon=-80,
            radius_km=10,
            mission_type="drone_search",
            lookback_hours=72,
            profiles=REGIONAL_RISK_PROFILES,
        )
        recent = score_surveillance_zones(
            lat=25,
            lon=-80,
            radius_km=10,
            mission_type="drone_search",
            lookback_hours=72,
            profiles=REGIONAL_RISK_PROFILES,
            recent_interactions=[
                {
                    "visibility": "public",
                    "observed_at": datetime.now(timezone.utc).isoformat(),
                    "fatal": False,
                }
            ],
        )
        self.assertGreater(recent["zones"][0]["priority_score"], baseline["zones"][0]["priority_score"])

    def test_spearfishing_context_increases_reef_zone_priority(self):
        reefs = [{"visibility": "public", "feature_type": "reef", "location": {"geo": {"type": "Point", "coordinates": [115.86, -31.95]}}}]
        general = score_surveillance_zones(
            lat=-31.95,
            lon=115.86,
            radius_km=10,
            mission_type="drone_search",
            lookback_hours=72,
            activity_context="swimming",
            profiles=REGIONAL_RISK_PROFILES,
            reef_features=reefs,
        )
        spearfishing = score_surveillance_zones(
            lat=-31.95,
            lon=115.86,
            radius_km=10,
            mission_type="drone_search",
            lookback_hours=72,
            activity_context="spearfishing",
            suspected_species="white shark",
            profiles=REGIONAL_RISK_PROFILES,
            reef_features=reefs,
        )
        self.assertGreater(spearfishing["zones"][0]["priority_score"], general["zones"][0]["priority_score"])
        self.assertEqual(spearfishing["zones"][0]["recommended_pattern"], "reef-edge expanding grid")

    def test_river_mouth_weighting_stronger_for_nsw_bull_than_wa_white_context(self):
        nsw = score_surveillance_zones(
            lat=-33.9,
            lon=151.2,
            radius_km=10,
            mission_type="drone_search",
            lookback_hours=72,
            suspected_species="bull shark",
            river_mouth_distance_km=0.5,
            profiles=REGIONAL_RISK_PROFILES,
        )
        wa = score_surveillance_zones(
            lat=-31.95,
            lon=115.86,
            radius_km=10,
            mission_type="drone_search",
            lookback_hours=72,
            suspected_species="white shark",
            river_mouth_distance_km=0.5,
            profiles=REGIONAL_RISK_PROFILES,
        )
        nsw_factors = {factor["factor"]: factor["points"] for factor in nsw["zones"][0]["dominant_factors"]}
        self.assertIn("nsw_bull_shark_river_runoff_context", nsw_factors)
        self.assertGreater(nsw["zones"][0]["priority_score"], wa["zones"][0]["priority_score"])

    def test_zones_include_explanations_and_disclaimer(self):
        result = score_surveillance_zones(
            lat=21.3,
            lon=-157.8,
            radius_km=10,
            mission_type="drone_search",
            lookback_hours=72,
            activity_context="surfing",
            suspected_species="tiger shark",
            month=10,
            profiles=REGIONAL_RISK_PROFILES,
        )
        zone = result["zones"][0]
        self.assertEqual(result["disclaimer"], SURVEILLANCE_DISCLAIMER)
        self.assertTrue(zone["dominant_factors"])
        self.assertIn("contribution", zone["dominant_factors"][0])
        self.assertIn("does not predict", zone["disclaimer"])

    def test_wa_spearfishing_reef_raises_surveillance_not_environmental_warning(self):
        reefs = [{"visibility": "public", "feature_type": "reef", "location": {"geo": {"type": "Point", "coordinates": [115.5153234, -31.9826564]}}}]
        result = score_surveillance_zones(
            lat=-31.9826564,
            lon=115.5153234,
            radius_km=10,
            mission_type="drone_search",
            lookback_hours=72,
            activity_context="spearfishing",
            suspected_species="white shark",
            month=5,
            profiles=REGIONAL_RISK_PROFILES,
            reef_features=reefs,
        )
        zone = result["zones"][0]
        self.assertEqual(zone["warning_score"], 0)
        self.assertEqual(zone["warning_band"], "low")
        self.assertGreaterEqual(zone["activity_context_score"], 50)
        self.assertGreaterEqual(zone["surveillance_priority_score"], 75)
        self.assertIn("score_split", zone)
        self.assertTrue(any(factor["factor"] == "activity_hazard_score" for factor in zone["dominant_factors"]))


if __name__ == "__main__":
    unittest.main()
