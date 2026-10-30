from __future__ import annotations

import argparse
import csv
import json
import math
import re
import unicodedata
import urllib.request
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable

try:
    from scripts.validate_incident_globe_geocoding import CoastlineIndex
except ModuleNotFoundError:  # Direct `python scripts/...py` execution.
    from validate_incident_globe_geocoding import CoastlineIndex


GEONAMES_BASE_URL = "https://download.geonames.org/export/dump"
DEFAULT_GLOBE = Path("data/public/incident_globe_1990_2026.json")
DEFAULT_CONTEXT = Path("data/review/incident_globe_context_geocodes_1900_2026.csv")
DEFAULT_GEONAMES_DIR = Path("data/raw/geonames")
DEFAULT_REJECTIONS = Path("data/review/incident_globe_geonames_rejections.csv")

COUNTRY_ALIASES = {
    "australia": "AU",
    "bahamas": "BS",
    "canary islands": "ES",
    "cayman islands": "KY",
    "columbia": "CO",
    "cook islands": "CK",
    "diego garcia": "IO",
    "england": "GB",
    "french polynesia": "PF",
    "grand cayman": "KY",
    "guam": "GU",
    "hawaii": "US",
    "hong kong": "HK",
    "maldive islands": "MV",
    "maldives islands": "MV",
    "mauritus": "MU",
    "micronesia": "FM",
    "new caledonia": "NC",
    "new zealand": "NZ",
    "nz": "NZ",
    "palestinian territories": "PS",
    "phillipines": "PH",
    "png": "PG",
    "reunion": "RE",
    "reunion island": "RE",
    "scotland": "GB",
    "sinai penninsula": "EG",
    "south africa": "ZA",
    "south korea": "KR",
    "st helena british overseas territory": "SH",
    "st kitts nevis": "KN",
    "st martin": "MF",
    "st maartin": "MF",
    "taiwan": "TW",
    "tanzania": "TZ",
    "tobago": "TT",
    "trinidad": "TT",
    "trinidad tobago": "TT",
    "turks caicos": "TC",
    "turks and caicos": "TC",
    "united arab emirates uae": "AE",
    "united kingdom": "GB",
    "us virgin islands": "VI",
    "usa": "US",
    "wallis and futuna": "WF",
}

COASTAL_FEATURE_CODES = {
    "ATOL",
    "BAR",
    "BAY",
    "BAYS",
    "BCH",
    "BCHS",
    "BGHT",
    "CAPE",
    "CHN",
    "CHNM",
    "COVE",
    "GULF",
    "HBR",
    "HBRX",
    "INLT",
    "ISL",
    "ISLET",
    "ISLS",
    "LGN",
    "OCN",
    "PT",
    "PTS",
    "RF",
    "RFC",
    "SEA",
    "SHOR",
    "SPIT",
    "STRT",
}

ALLOWED_NON_COASTAL_FEATURE_CODES = {"PRK", "RKS"}

GENERIC_LOCATION_PREFIXES = (
    "approximately ",
    "near ",
    "off ",
    "offshore ",
    "at ",
)

ADMINISTRATIVE_SEGMENT_PATTERN = re.compile(
    r"\b(county|cty|district|province|state|governorate|municipality|department|region)\b"
)

REGION_ALIASES = {
    "AU": {
        "act": "australian capital territory",
        "nsw": "new south wales",
        "nt": "northern territory",
        "qld": "queensland",
        "sa": "south australia",
        "tas": "tasmania",
        "vic": "victoria",
        "wa": "western australia",
    },
    "ZA": {
        "ecp": "eastern cape",
        "kzn": "kwazulu natal",
        "wcp": "western cape",
    },
}

COASTAL_NAME_TOKENS = {
    "atoll",
    "bay",
    "beach",
    "cape",
    "cay",
    "channel",
    "coast",
    "cove",
    "gulf",
    "harbour",
    "harbor",
    "inlet",
    "island",
    "islands",
    "lagoon",
    "point",
    "reef",
    "rocks",
    "shore",
    "strait",
}


def normalize(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(character for character in text if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def candidate_phrases(location: str) -> list[tuple[str, float]]:
    raw_parts = [part.strip() for part in re.split(r"[,;/]", location) if part.strip()]
    ordered = [location, *raw_parts]
    phrases: list[tuple[str, float]] = []
    seen: set[str] = set()
    for index, raw in enumerate(ordered):
        normalized = normalize(raw)
        for prefix in GENERIC_LOCATION_PREFIXES:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix) :]
                break
        if not normalized or normalized in seen or len(normalized) < 3:
            continue
        if index > 1 and ADMINISTRATIVE_SEGMENT_PATTERN.search(normalized):
            continue
        seen.add(normalized)
        quality = 1.0 if index <= 1 else 0.96
        phrases.append((normalized, quality))
    return phrases


@dataclass(frozen=True)
class Query:
    key: tuple[str, str, str]
    location: str
    region: str
    country: str
    iso_code: str
    phrases: tuple[tuple[str, float], ...]


@dataclass(frozen=True)
class Feature:
    geoname_id: str
    name: str
    latitude: float
    longitude: float
    feature_class: str
    feature_code: str
    country_code: str
    admin1_code: str
    admin2_code: str


@dataclass(frozen=True)
class Match:
    query: Query
    feature: Feature
    matched_name: str
    matched_phrase: str
    name_ratio: float
    phrase_quality: float
    region_supported: bool
    score: float
    coast_distance_km: float


def download(url: str, destination: Path) -> None:
    if destination.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "AI1SAD/1.0 (info@ai1sad.org)"})
    with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as handle:
        while chunk := response.read(1024 * 1024):
            handle.write(chunk)


def ensure_reference_files(directory: Path) -> tuple[Path, Path, Path]:
    country_info = directory / "countryInfo.txt"
    admin1 = directory / "admin1CodesASCII.txt"
    admin2 = directory / "admin2Codes.txt"
    download(f"{GEONAMES_BASE_URL}/countryInfo.txt", country_info)
    download(f"{GEONAMES_BASE_URL}/admin1CodesASCII.txt", admin1)
    download(f"{GEONAMES_BASE_URL}/admin2Codes.txt", admin2)
    return country_info, admin1, admin2


def country_codes(path: Path) -> dict[str, str]:
    result = dict(COUNTRY_ALIASES)
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 5:
                continue
            iso, iso3, country = fields[0], fields[1], fields[4]
            result[normalize(country)] = iso
            result[normalize(iso)] = iso
            result[normalize(iso3)] = iso
    return result


def admin_names(admin1_path: Path, admin2_path: Path) -> tuple[dict[str, str], dict[str, str]]:
    admin1: dict[str, str] = {}
    admin2: dict[str, str] = {}
    with admin1_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if len(fields) >= 3:
                admin1[fields[0]] = normalize(f"{fields[1]} {fields[2]}")
    with admin2_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if len(fields) >= 3:
                admin2[fields[0]] = normalize(f"{fields[1]} {fields[2]}")
    return admin1, admin2


def unresolved_queries(globe_path: Path, codes: dict[str, str]) -> tuple[list[Query], Counter[str]]:
    payload = json.loads(globe_path.read_text(encoding="utf-8"))
    contexts: dict[tuple[str, str, str], dict[str, str]] = {}
    incidents = Counter()
    for record in payload.get("records", []):
        if record.get("mapped") and record.get("coordinate_source") != "geonames_contextual":
            continue
        location = clean(record.get("location"))
        region = clean(record.get("region"))
        country = clean(record.get("country"))
        key = (normalize(location), normalize(region), normalize(country))
        incidents[key] += 1
        contexts.setdefault(key, {"location": location, "region": region, "country": country})

    queries: list[Query] = []
    skipped = Counter()
    for key, context in contexts.items():
        if not key[0]:
            skipped["blank_location"] += incidents[key]
            continue
        iso_code = codes.get(key[2])
        if not iso_code:
            skipped["unknown_country"] += incidents[key]
            continue
        phrases = tuple(candidate_phrases(context["location"]))
        if not phrases:
            skipped["unusable_location"] += incidents[key]
            continue
        queries.append(
            Query(
                key=key,
                location=context["location"],
                region=context["region"],
                country=context["country"],
                iso_code=iso_code,
                phrases=phrases,
            )
        )
    return queries, skipped


def reviewed_rejections(path: Path) -> set[tuple[str, str, str]]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {
            (
                normalize(row.get("location")),
                normalize(row.get("region")),
                normalize(row.get("country")),
            )
            for row in csv.DictReader(handle)
        }


def iter_country_features(zip_path: Path) -> Iterable[tuple[Feature, list[str]]]:
    with zipfile.ZipFile(zip_path) as archive:
        text_names = [name for name in archive.namelist() if name.lower().endswith(".txt")]
        if not text_names:
            return
        expected_name = f"{zip_path.stem}.txt".casefold()
        data_name = next(
            (name for name in text_names if Path(name).name.casefold() == expected_name),
            max(text_names, key=lambda name: archive.getinfo(name).file_size),
        )
        with archive.open(data_name) as handle:
            for raw_line in handle:
                fields = raw_line.decode("utf-8", errors="replace").rstrip("\n").split("\t")
                if len(fields) < 14:
                    continue
                try:
                    latitude = float(fields[4])
                    longitude = float(fields[5])
                except ValueError:
                    continue
                feature = Feature(
                    geoname_id=fields[0],
                    name=fields[1],
                    latitude=latitude,
                    longitude=longitude,
                    feature_class=fields[6],
                    feature_code=fields[7],
                    country_code=fields[8],
                    admin1_code=fields[10],
                    admin2_code=fields[11],
                )
                names = [fields[1], fields[2]]
                if fields[3]:
                    names.extend(fields[3].split(","))
                yield feature, names


def region_support(
    query: Query,
    feature: Feature,
    admin1: dict[str, str],
    admin2: dict[str, str],
) -> bool:
    region = normalize(query.region)
    if not region:
        return False
    expanded_region = REGION_ALIASES.get(query.iso_code, {}).get(region, region)
    region_tokens = set(expanded_region.split())
    if normalize(feature.admin1_code) in region_tokens:
        return True
    names = " ".join(
        filter(
            None,
            [
                admin1.get(f"{feature.country_code}.{feature.admin1_code}"),
                admin2.get(
                    f"{feature.country_code}.{feature.admin1_code}.{feature.admin2_code}"
                ),
            ],
        )
    )
    meaningful_tokens = {token for token in region_tokens if len(token) > 2}
    return bool(meaningful_tokens and any(token in names.split() for token in meaningful_tokens))


def collect_candidates(
    queries: list[Query],
    zip_path: Path,
    admin1: dict[str, str],
    admin2: dict[str, str],
) -> dict[
    tuple[str, str, str],
    list[tuple[Feature, str, str, float, float, bool, float]],
]:
    exact: defaultdict[str, list[tuple[Query, float]]] = defaultdict(list)
    prefixes: defaultdict[str, list[tuple[Query, str, float]]] = defaultdict(list)
    for query in queries:
        for phrase, quality in query.phrases:
            exact[phrase].append((query, quality))
            prefixes[phrase[:4]].append((query, phrase, quality))

    candidates: defaultdict[
        tuple[str, str, str],
        list[tuple[Feature, str, str, float, float, bool, float]],
    ] = defaultdict(list)
    seen: set[tuple[tuple[str, str, str], str, str]] = set()
    for feature, raw_names in iter_country_features(zip_path):
        for raw_name in raw_names:
            name = normalize(raw_name)
            if len(name) < 3:
                continue
            possible: list[tuple[Query, str, str, float, float]] = [
                (query, name, name, 1.0, quality) for query, quality in exact.get(name, [])
            ]
            for query, phrase, quality in prefixes.get(name[:4], []):
                if abs(len(phrase) - len(name)) > max(3, math.ceil(len(phrase) * 0.12)):
                    continue
                ratio = SequenceMatcher(None, phrase, name).ratio()
                if ratio >= 0.88:
                    possible.append((query, name, phrase, ratio, quality))
            for query, matched_name, matched_phrase, ratio, quality in possible:
                unique_key = (query.key, feature.geoname_id, matched_phrase)
                if unique_key in seen:
                    continue
                seen.add(unique_key)
                supported = region_support(query, feature, admin1, admin2)
                if feature.feature_code.startswith("ADM"):
                    continue
                if (
                    feature.feature_class != "P"
                    and feature.feature_code not in COASTAL_FEATURE_CODES
                    and feature.feature_code not in ALLOWED_NON_COASTAL_FEATURE_CODES
                ):
                    continue
                if query.region and not supported:
                    continue
                if (
                    not query.region
                    and feature.feature_class == "P"
                    and not set(query.key[0].split()).intersection(COASTAL_NAME_TOKENS)
                ):
                    continue
                if ratio < 0.94 or (ratio < 1.0 and not supported):
                    continue
                if (
                    ratio < 1.0
                    and feature.feature_code not in COASTAL_FEATURE_CODES
                    and feature.feature_class != "P"
                    and feature.feature_code != "PRK"
                ):
                    continue
                score = ratio * quality
                score += 0.07 if supported else 0.0
                score += 0.03 if feature.feature_code in COASTAL_FEATURE_CODES else 0.0
                candidates[query.key].append(
                    (
                        feature,
                        matched_name,
                        matched_phrase,
                        ratio,
                        quality,
                        supported,
                        score,
                    )
                )
    return candidates


def distance_km(a: Feature, b: Feature) -> float:
    latitude = math.radians((a.latitude + b.latitude) / 2)
    delta_latitude = (a.latitude - b.latitude) * 110.57
    delta_longitude = (a.longitude - b.longitude) * 111.32 * math.cos(latitude)
    return math.hypot(delta_latitude, delta_longitude)


def feature_coast_limit(feature: Feature, maximum_coast_distance_km: float) -> float:
    if feature.feature_code in {"ATOL", "BAY", "BAYS", "GULF", "ISL", "ISLET", "ISLS"}:
        return maximum_coast_distance_km
    if feature.feature_code == "PRK":
        return min(maximum_coast_distance_km, 10.0)
    return min(maximum_coast_distance_km, 5.0)


def choose_matches(
    queries: list[Query],
    candidates: dict[
        tuple[str, str, str],
        list[tuple[Feature, str, str, float, float, bool, float]],
    ],
    coastline: CoastlineIndex,
    maximum_coast_distance_km: float,
) -> tuple[list[Match], Counter[str]]:
    accepted: list[Match] = []
    rejected = Counter()
    for query in queries:
        viable: list[Match] = []
        query_candidates = candidates.get(query.key, [])
        for feature, matched_name, matched_phrase, ratio, quality, supported, score in query_candidates:
            distance = coastline.distance_km(feature.latitude, feature.longitude)
            if not math.isfinite(distance) or distance > feature_coast_limit(
                feature, maximum_coast_distance_km
            ):
                continue
            compound_parts = query.phrases[1:]
            if len(compound_parts) > 1 and matched_phrase != query.phrases[0][0]:
                context_supported = any(
                    other_phrase != matched_phrase
                    and distance_km(feature, other_feature) <= 50.0
                    for other_feature, _, other_phrase, _, _, _, _ in query_candidates
                )
                if not context_supported:
                    continue
                score += 0.04
            viable.append(
                Match(
                    query=query,
                    feature=feature,
                    matched_name=matched_name,
                    matched_phrase=matched_phrase,
                    name_ratio=ratio,
                    phrase_quality=quality,
                    region_supported=supported,
                    score=score - min(distance, maximum_coast_distance_km) / 1000.0,
                    coast_distance_km=distance,
                )
            )
        viable.sort(key=lambda item: (item.score, item.region_supported, -item.coast_distance_km), reverse=True)
        if not viable:
            rejected["no_coastal_match"] += 1
            continue
        best = viable[0]
        distinct = [
            item
            for item in viable[1:]
            if (item.feature.latitude, item.feature.longitude)
            != (best.feature.latitude, best.feature.longitude)
        ]
        if distinct and best.score - distinct[0].score < 0.035:
            rejected["ambiguous_match"] += 1
            continue
        accepted.append(best)
    return accepted, rejected


def context_row(match: Match) -> dict[str, Any]:
    return {
        "query_id": f"geonames:{match.feature.geoname_id}",
        "location": match.query.location,
        "region": match.query.region,
        "country": match.query.country,
        "latitude": match.feature.latitude,
        "longitude": match.feature.longitude,
        "relevance": round(min(match.score, 1.0), 4),
        "coast_distance_km": round(match.coast_distance_km, 3),
        "validation_status": "validated",
        "provider": "GeoNames",
        "provider_country": match.feature.country_code,
        "provider_match_level": (
            f"{'exact' if match.name_ratio == 1.0 else 'fuzzy'};"
            f"feature={match.feature.feature_code};region_supported={str(match.region_supported).lower()};"
            f"phrase={match.matched_phrase};name={match.matched_name}"
        ),
    }


def merge_context_rows(context_path: Path, output_path: Path, matches: list[Match]) -> int:
    with context_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    if not fieldnames:
        fieldnames = [
            "query_id",
            "location",
            "region",
            "country",
            "latitude",
            "longitude",
            "relevance",
            "coast_distance_km",
            "validation_status",
            "provider",
            "provider_country",
            "provider_match_level",
        ]
    replacements = {match.query.key: context_row(match) for match in matches}
    merged: list[dict[str, Any]] = []
    replaced: set[tuple[str, str, str]] = set()
    for row in rows:
        key = (normalize(row.get("location")), normalize(row.get("region")), normalize(row.get("country")))
        generated_geonames_row = (
            normalize(row.get("provider")) == "geonames"
            and str(row.get("query_id") or "").startswith("geonames:")
        )
        if generated_geonames_row:
            if key in replacements and key not in replaced:
                merged.append(replacements[key])
                replaced.add(key)
            continue
        if (
            key in replacements
            and key not in replaced
            and row.get("validation_status") != "validated"
        ):
            merged.append(replacements[key])
            replaced.add(key)
        else:
            merged.append(row)
    for key, row in replacements.items():
        if key not in replaced and not any(
            (normalize(item.get("location")), normalize(item.get("region")), normalize(item.get("country"))) == key
            for item in rows
        ):
            merged.append(row)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged)
    return len(replacements)


def resolve(
    globe_path: Path,
    context_path: Path,
    output_path: Path,
    geonames_dir: Path,
    coastline_path: Path,
    rejection_path: Path = DEFAULT_REJECTIONS,
    maximum_coast_distance_km: float = 25.0,
) -> dict[str, Any]:
    country_info, admin1_path, admin2_path = ensure_reference_files(geonames_dir)
    codes = country_codes(country_info)
    admin1, admin2 = admin_names(admin1_path, admin2_path)
    queries, skipped = unresolved_queries(globe_path, codes)
    considered = len(queries)
    rejected_keys = reviewed_rejections(rejection_path)
    reviewed_rejection_count = sum(query.key in rejected_keys for query in queries)
    queries = [query for query in queries if query.key not in rejected_keys]
    by_country: defaultdict[str, list[Query]] = defaultdict(list)
    for query in queries:
        by_country[query.iso_code].append(query)

    coastline = CoastlineIndex(coastline_path)
    accepted: list[Match] = []
    rejected = Counter()
    for iso_code, country_queries in sorted(by_country.items()):
        zip_path = geonames_dir / f"{iso_code}.zip"
        download(f"{GEONAMES_BASE_URL}/{iso_code}.zip", zip_path)
        candidates = collect_candidates(country_queries, zip_path, admin1, admin2)
        country_matches, country_rejections = choose_matches(
            country_queries,
            candidates,
            coastline,
            maximum_coast_distance_km,
        )
        accepted.extend(country_matches)
        rejected.update(country_rejections)

    merged = merge_context_rows(context_path, output_path, accepted)
    return {
        "unresolved_unique_contexts_considered": considered,
        "accepted_contexts": len(accepted),
        "merged_contexts": merged,
        "reviewed_rejection_contexts": reviewed_rejection_count,
        "skipped_incidents": dict(skipped),
        "rejected_contexts": dict(rejected),
        "countries_processed": len(by_country),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resolve Incident Globe locations against offline GeoNames country gazetteers."
    )
    parser.add_argument("--globe", type=Path, default=DEFAULT_GLOBE)
    parser.add_argument("--context", type=Path, default=DEFAULT_CONTEXT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--geonames-dir", type=Path, default=DEFAULT_GEONAMES_DIR)
    parser.add_argument("--coastline", type=Path, required=True)
    parser.add_argument("--rejections", type=Path, default=DEFAULT_REJECTIONS)
    parser.add_argument("--maximum-coast-distance-km", type=float, default=25.0)
    args = parser.parse_args()
    summary = resolve(
        args.globe,
        args.context,
        args.output,
        args.geonames_dir,
        args.coastline,
        args.rejections,
        args.maximum_coast_distance_km,
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
