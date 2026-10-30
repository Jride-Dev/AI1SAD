from __future__ import annotations

import csv
import json
import zipfile

from scripts.resolve_incident_globe_geonames import (
    Feature,
    Match,
    Query,
    candidate_phrases,
    feature_coast_limit,
    iter_country_features,
    merge_context_rows,
    normalize,
    reviewed_rejections,
    region_support,
    unresolved_queries,
)


def test_geonames_normalization_handles_accents_and_punctuation():
    assert normalize("Ouvéa") == "ouvea"
    assert normalize("Port St. John's") == "port st john s"


def test_candidate_phrases_preserve_full_and_compound_place_names():
    phrases = candidate_phrases("Ponce Inlet, New Smyrna Beach")

    assert phrases[0] == ("ponce inlet new smyrna beach", 1.0)
    assert ("ponce inlet", 1.0) in phrases
    assert ("new smyrna beach", 0.96) in phrases


def test_candidate_phrases_do_not_promote_administrative_descriptors():
    phrases = candidate_phrases("Stuart Beach, Martin County")

    assert ("stuart beach", 1.0) in phrases
    assert all(phrase != "martin county" for phrase, _ in phrases)


def test_candidate_phrases_remove_only_bounded_location_prefixes():
    assert candidate_phrases("Off Lovers Point, Pacific Grove")[0][0] == "lovers point pacific grove"


def test_country_archive_reader_skips_readme(tmp_path):
    archive_path = tmp_path / "US.zip"
    row = "1\tJacksonville Beach\tJacksonville Beach\t\t30.29\t-81.39\tP\tPPL\tUS\t\tFL\t031\t\t\t0\t\t\tAmerica/New_York\t2026-01-01\n"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("readme.txt", "not the data table")
        archive.writestr("US.txt", row)

    [(feature, names)] = list(iter_country_features(archive_path))

    assert feature.name == "Jacksonville Beach"
    assert names[0] == "Jacksonville Beach"


def test_feature_coast_limits_keep_city_centroids_close_to_water():
    city = Feature("1", "Jacksonville", 30.3, -81.6, "P", "PPL", "US", "FL", "031")
    bay = Feature("2", "Moreton Bay", -27.2, 153.2, "H", "BAY", "AU", "04", "")

    assert feature_coast_limit(city, 25.0) == 5.0
    assert feature_coast_limit(bay, 25.0) == 25.0


def test_region_support_recognizes_source_state_abbreviation():
    query = Query(
        ("daytona beach", "velusa cty fl", "usa"),
        "Daytona Beach",
        "Velusa Cty, Fl",
        "USA",
        "US",
        (("daytona beach", 1.0),),
    )
    feature = Feature("1", "Daytona Beach", 29.2, -81.0, "P", "PPL", "US", "FL", "127")

    assert region_support(query, feature, {}, {}) is True


def test_region_support_expands_australian_state_abbreviation():
    query = Query(
        ("bondi beach", "nsw", "australia"),
        "Bondi Beach",
        "NSW",
        "Australia",
        "AU",
        (("bondi beach", 1.0),),
    )
    feature = Feature("1", "Bondi Beach", -33.89, 151.27, "T", "BCH", "AU", "02", "")

    assert region_support(query, feature, {"AU.02": "new south wales"}, {}) is True


def test_reviewed_rejections_are_context_specific(tmp_path):
    path = tmp_path / "rejections.csv"
    path.write_text(
        "location,region,country,reason\n"
        "Buffels Bay,WCP,SOUTH AFRICA,ambiguous place name\n",
        encoding="utf-8",
    )

    assert reviewed_rejections(path) == {("buffels bay", "wcp", "south africa")}


def test_merge_removes_stale_generated_geonames_rows(tmp_path):
    context = tmp_path / "context.csv"
    output = tmp_path / "output.csv"
    context.write_text(
        "query_id,location,region,country,latitude,longitude,relevance,coast_distance_km,"
        "validation_status,provider,provider_country,provider_match_level\n"
        "geonames:1,Bunkers,California,USA,25.7,-171.7,1,0.1,validated,GeoNames,US,exact\n"
        "csv:1,Daytona Beach,Florida,USA,29.2,-81.0,1,0.1,validated,CSV2GEO,US,exact\n",
        encoding="utf-8",
    )

    assert merge_context_rows(context, output, []) == 0
    with output.open(encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    assert [row["provider"] for row in rows] == ["CSV2GEO"]


def test_existing_geonames_points_are_rechecked(tmp_path):
    globe = tmp_path / "globe.json"
    globe.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "mapped": True,
                        "coordinate_source": "geonames_contextual",
                        "location": "Daytona Beach",
                        "region": "Florida",
                        "country": "USA",
                    },
                    {
                        "mapped": True,
                        "coordinate_source": "source_coordinate",
                        "location": "Miami Beach",
                        "region": "Florida",
                        "country": "USA",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    queries, _ = unresolved_queries(globe, {"usa": "US"})

    assert [query.location for query in queries] == ["Daytona Beach"]


def test_merge_deduplicates_generated_geonames_contexts(tmp_path):
    context = tmp_path / "context.csv"
    output = tmp_path / "output.csv"
    header = (
        "query_id,location,region,country,latitude,longitude,relevance,coast_distance_km,"
        "validation_status,provider,provider_country,provider_match_level\n"
    )
    duplicate = (
        "geonames:1,Daytona Beach,Florida,USA,29.2,-81.0,1,0.1,"
        "validated,GeoNames,US,exact\n"
    )
    context.write_text(header + duplicate + duplicate, encoding="utf-8")
    query = Query(
        ("daytona beach", "florida", "usa"),
        "Daytona Beach",
        "Florida",
        "USA",
        "US",
        (("daytona beach", 1.0),),
    )
    feature = Feature("2", "Daytona Beach", 29.2, -81.0, "P", "PPL", "US", "FL", "127")
    match = Match(query, feature, "daytona beach", "daytona beach", 1.0, 1.0, True, 1.0, 0.1)

    assert merge_context_rows(context, output, [match]) == 1
    with output.open(encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1
    assert rows[0]["query_id"] == "geonames:2"
