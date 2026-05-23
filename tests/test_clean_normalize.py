import unittest

from scripts.clean_normalize import normalize_row, public_location


class NormalizeTests(unittest.TestCase):
    def test_excludes_private_identity_fields(self):
        row = {
            "Case Number": "2018.06.25",
            "Date": "25-Jun-18",
            "Year": "2018",
            "Type": "Boating",
            "Country": "USA",
            "Area": "California",
            "Location": "Oceanside, San Diego County",
            "Activity": "Paddling",
            "Name": "Private Person",
            "Sex ": "F",
            "Age": "57",
            "Injury": "Minor injury",
            "Fatal (Y/N)": "N",
            "Time": "18h00",
            "Species ": "White shark",
            "Investigator or Source": "Restricted notes",
        }
        record = normalize_row(row)
        self.assertIsNotNone(record)
        assert record is not None
        self.assertNotIn("Name", record)
        self.assertNotIn("Investigator or Source", record)
        self.assertEqual(record["country_normalized"], "USA")
        self.assertEqual(record["fatal"], 0)

    def test_location_redacts_street_addresses(self):
        self.assertEqual(public_location("123 Main Street, Beach Town, Florida"), "[redacted address], Beach Town")


if __name__ == "__main__":
    unittest.main()

