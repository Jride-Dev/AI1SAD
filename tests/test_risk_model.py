import unittest

from app.risk_model import REGIONAL_RISK_PROFILES, RISK_DISCLAIMER, nearest_profile, score_risk


class RiskModelTests(unittest.TestCase):
    def test_risk_increases_after_rainfall(self):
        baseline = score_risk(recent_rainfall_mm_24h=0)
        rainy = score_risk(recent_rainfall_mm_24h=50)
        self.assertGreater(rainy["score"], baseline["score"])

    def test_risk_increases_near_river_mouth(self):
        far = score_risk(river_mouth_distance_km=25)
        near = score_risk(river_mouth_distance_km=0.5)
        self.assertGreater(near["score"], far["score"])

    def test_risk_increases_with_fishing_activity(self):
        no_fishing = score_risk(fishing_activity=0)
        active_fishing = score_risk(fishing_activity=1)
        self.assertGreater(active_fishing["score"], no_fishing["score"])

    def test_disclaimer_is_returned(self):
        result = score_risk()
        self.assertEqual(result["disclaimer"], RISK_DISCLAIMER)
        self.assertIn("not an attack prediction", result["disclaimer"])

    def test_australia_january_is_summer_high_attention(self):
        profile = next(item for item in REGIONAL_RISK_PROFILES if item["region_key"] == "new_south_wales_australia")
        december = score_risk(month=12, human_water_activity=0.5, regional_profile=profile)
        january = score_risk(month=1, human_water_activity=0.5, regional_profile=profile)
        self.assertIn(1, profile["local_summer_high_exposure_months"])
        self.assertIn(1, profile["known_high_attention_months"])
        self.assertGreater(january["warning_score"], december["warning_score"])
        self.assertTrue(any(factor["factor"] == "australia_jan_feb_high_exposure" for factor in january["factors"]))

    def test_hawaii_october_applies_sharktober_multiplier(self):
        profile = next(item for item in REGIONAL_RISK_PROFILES if item["region_key"] == "hawaii")
        september = score_risk(month=9, human_water_activity=0.5, regional_profile=profile)
        october = score_risk(month=10, human_water_activity=0.5, regional_profile=profile)
        self.assertGreater(october["warning_score"], september["warning_score"])
        self.assertTrue(any(factor["factor"] == "hawaii_sharktober" for factor in october["factors"]))

    def test_florida_weekend_exposure_increases_human_activity_score(self):
        profile = next(item for item in REGIONAL_RISK_PROFILES if item["region_key"] == "florida")
        weekday = score_risk(month=11, human_water_activity=0.5, weekend=False, regional_profile=profile)
        weekend = score_risk(month=11, human_water_activity=0.5, weekend=True, regional_profile=profile)
        self.assertGreater(weekend["warning_score"], weekday["warning_score"])
        self.assertTrue(any(factor["factor"] == "florida_weekend_exposure" for factor in weekend["factors"]))

    def test_nearest_profile_finds_regional_profile(self):
        profile = nearest_profile(-33.9, 151.2)
        self.assertIsNotNone(profile)
        self.assertEqual(profile["region_key"], "new_south_wales_australia")

    def test_red_sea_profile_has_species_engine_fields(self):
        profile = next(item for item in REGIONAL_RISK_PROFILES if item["region_key"] == "red_sea")
        self.assertIn("oceanic whitetip shark", profile["species_weights"])
        self.assertIn("shipping influence", " ".join(profile["species_specific_risk_factors"]["oceanic whitetip shark"]))
        self.assertEqual(profile["warning_cache_ttl_minutes"], 30)


if __name__ == "__main__":
    unittest.main()
