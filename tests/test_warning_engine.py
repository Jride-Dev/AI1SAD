import unittest
from datetime import datetime, timedelta, timezone

from app.risk_model import REGIONAL_RISK_PROFILES
from app.services.activity_hazard import activity_hazard_score
from app.services.warning_engine import calculate_warning, provider_health_document


class WarningEngineTests(unittest.TestCase):
    def test_rainfall_in_last_72h_increases_score(self):
        dry = calculate_warning(lat=25, lon=-80, rainfall_72h_mm=0)
        wet = calculate_warning(lat=25, lon=-80, rainfall_72h_mm=75)
        self.assertGreater(wet["warning_score"], dry["warning_score"])
        self.assertGreater(wet["signals"]["rainfall_intensity_score"], dry["signals"]["rainfall_intensity_score"])

    def test_whale_carcass_nearby_increases_biological_event_score(self):
        event = {
            "event_type": "whale_carcass",
            "visibility": "public",
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }
        result = calculate_warning(lat=25, lon=-80, biological_events=[event])
        self.assertGreater(result["signals"]["biological_event_score"], 0)

    def test_stale_biological_events_expire(self):
        event = {
            "event_type": "whale_carcass",
            "visibility": "public",
            "observed_at": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
        }
        result = calculate_warning(lat=25, lon=-80, biological_events=[event])
        self.assertEqual(result["signals"]["biological_event_score"], 0)

    def test_australia_january_seasonal_multiplier_applies(self):
        result = calculate_warning(lat=-33.9, lon=151.2, rainfall_72h_mm=25, month=1, profiles=REGIONAL_RISK_PROFILES)
        self.assertEqual(result["regional_profile"]["region_key"], "new_south_wales_australia")
        self.assertGreater(result["signals"]["regional_seasonal_multiplier"], 1)
        self.assertTrue(any(factor["factor"] == "australia_jan_feb_high_exposure" for factor in result["dominant_factors"] + result["dominant_factors"]))

    def test_hawaii_october_multiplier_applies(self):
        result = calculate_warning(lat=21.3, lon=-157.8, rainfall_72h_mm=25, month=10, profiles=REGIONAL_RISK_PROFILES)
        self.assertEqual(result["regional_profile"]["region_key"], "hawaii")
        self.assertGreater(result["signals"]["regional_seasonal_multiplier"], 1)
        self.assertTrue(any(factor["factor"] == "hawaii_sharktober" for factor in result["dominant_factors"]))

    def test_missing_provider_data_lowers_confidence_instead_of_crashing(self):
        missing = calculate_warning(lat=25, lon=-80)
        complete = calculate_warning(
            lat=25,
            lon=-80,
            rainfall_72h_mm=10,
            sea_surface_temp_c=26,
            sst_anomaly_c=1,
            vessel_activity_index=0.5,
            biological_events=[{"event_type": "baitfish", "visibility": "public", "observed_at": datetime.now(timezone.utc).isoformat()}],
            human_exposure_index=0.5,
        )
        self.assertLess(missing["confidence"], complete["confidence"])
        self.assertIn("missing_data_sources", missing)

    def test_dominant_factors_include_contribution(self):
        result = calculate_warning(
            lat=25,
            lon=-80,
            rainfall_72h_mm=75,
            river_mouth_distance_km=1,
            vessel_activity_index=0.8,
        )
        self.assertTrue(result["dominant_factors"])
        self.assertIn("contribution", result["dominant_factors"][0])
        self.assertGreater(result["dominant_factors"][0]["contribution"], 0)

    def test_stale_provider_data_lowers_confidence(self):
        fresh = calculate_warning(
            lat=25,
            lon=-80,
            rainfall_72h_mm=20,
            provider_status={"weather_observations": "ok"},
        )
        stale = calculate_warning(
            lat=25,
            lon=-80,
            rainfall_72h_mm=20,
            provider_status={"weather_observations": "stale"},
        )
        self.assertLess(stale["confidence"], fresh["confidence"])
        self.assertIn("weather_observations:stale", stale["missing_data_sources"])

    def test_provider_health_document_shape(self):
        doc = provider_health_document(
            "open_meteo",
            status="healthy",
            records_ingested=483,
            last_success="2026-05-23T06:21:00Z",
        )
        self.assertEqual(doc["_id"], "open_meteo")
        self.assertEqual(doc["status"], "healthy")
        self.assertEqual(doc["records_ingested"], 483)

    def test_activity_hazard_does_not_raise_environmental_warning_score_without_live_signals(self):
        result = calculate_warning(
            lat=-31.9826564,
            lon=115.5153234,
            activity_context="spearfishing",
            reef_habitat=True,
            suspected_species="white shark",
            month=5,
            profiles=REGIONAL_RISK_PROFILES,
        )
        self.assertEqual(result["warning_score"], 0)
        self.assertEqual(result["warning_band"], "low")
        self.assertGreaterEqual(result["activity_context_score"], 50)
        self.assertIn("score_split", result)

    def test_activity_hazard_scores_high_risk_water_activity_contexts(self):
        profile = next(item for item in REGIONAL_RISK_PROFILES if item["region_key"] == "western_australia")
        result = activity_hazard_score(
            activity_context="spearfishing",
            reef_habitat=True,
            suspected_species="white shark",
            regional_profile=profile,
        )
        self.assertGreaterEqual(result["activity_context_score"], 50)
        self.assertIn("not attack probability", result["disclaimer"])


if __name__ == "__main__":
    unittest.main()
