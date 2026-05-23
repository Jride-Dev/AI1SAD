from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, HTTPException, Query

from app.database import fetch_all, fetch_one, get_db_path


app = FastAPI(
    title="Shark Attack Data API",
    version="0.1.0",
    description="Public, privacy-preserving API for normalized shark attack incident records.",
)


def ensure_database() -> None:
    if not get_db_path().exists():
        raise HTTPException(
            status_code=503,
            detail="Database not found. Run `python scripts/export_public.py` first.",
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "database": str(get_db_path())}


@app.get("/incidents")
def incidents(
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    year: int | None = None,
    country: str | None = None,
    activity: str | None = None,
    fatal: bool | None = None,
    species: str | None = None,
) -> dict[str, object]:
    ensure_database()
    clauses: list[str] = []
    params: dict[str, object] = {"limit": limit, "offset": offset}
    if year is not None:
        clauses.append("year = :year")
        params["year"] = year
    if country:
        clauses.append("country_normalized = :country")
        params["country"] = country.upper()
    if activity:
        clauses.append("activity_normalized = :activity")
        params["activity"] = activity.lower()
    if fatal is not None:
        clauses.append("fatal = :fatal")
        params["fatal"] = 1 if fatal else 0
    if species:
        clauses.append("species_normalized LIKE :species")
        params["species"] = f"%{species.lower()}%"
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = fetch_all(
        f"""
        SELECT *
        FROM public_incidents
        {where}
        ORDER BY year DESC, incident_id DESC
        LIMIT :limit OFFSET :offset
        """,
        params,
    )
    total = fetch_one(f"SELECT COUNT(*) AS count FROM public_incidents {where}", params)
    return {"count": total["count"] if total else 0, "limit": limit, "offset": offset, "results": rows}


@app.get("/incidents/{incident_id}")
def incident(incident_id: str) -> dict[str, object]:
    ensure_database()
    row = fetch_one("SELECT * FROM public_incidents WHERE incident_id = :incident_id", {"incident_id": incident_id})
    if not row:
        raise HTTPException(status_code=404, detail="Incident not found")
    return row


@app.get("/stats/yearly")
def yearly_stats() -> list[dict[str, object]]:
    ensure_database()
    return fetch_all(
        """
        SELECT year, COUNT(*) AS incidents, SUM(fatal) AS fatalities,
               ROUND(100.0 * SUM(fatal) / COUNT(*), 2) AS fatality_rate_percent
        FROM public_incidents
        WHERE year IS NOT NULL
        GROUP BY year
        ORDER BY year DESC
        """
    )


@app.get("/stats/countries")
def country_stats(limit: Annotated[int, Query(ge=1, le=250)] = 50) -> list[dict[str, object]]:
    ensure_database()
    return fetch_all(
        """
        SELECT country_normalized AS country, COUNT(*) AS incidents, SUM(fatal) AS fatalities,
               ROUND(100.0 * SUM(fatal) / COUNT(*), 2) AS fatality_rate_percent
        FROM public_incidents
        WHERE country_normalized IS NOT NULL
        GROUP BY country_normalized
        ORDER BY incidents DESC, country ASC
        LIMIT :limit
        """,
        {"limit": limit},
    )


@app.get("/stats/activities")
def activity_stats(limit: Annotated[int, Query(ge=1, le=250)] = 50) -> list[dict[str, object]]:
    ensure_database()
    return fetch_all(
        """
        SELECT activity_normalized AS activity, COUNT(*) AS incidents, SUM(fatal) AS fatalities
        FROM public_incidents
        WHERE activity_normalized IS NOT NULL
        GROUP BY activity_normalized
        ORDER BY incidents DESC, activity ASC
        LIMIT :limit
        """,
        {"limit": limit},
    )


@app.get("/stats/fatality-rate")
def fatality_rate() -> dict[str, object]:
    ensure_database()
    row = fetch_one(
        """
        SELECT COUNT(*) AS incidents, SUM(fatal) AS fatalities,
               ROUND(100.0 * SUM(fatal) / COUNT(*), 2) AS fatality_rate_percent
        FROM public_incidents
        """
    )
    return row or {"incidents": 0, "fatalities": 0, "fatality_rate_percent": None}


@app.get("/species")
def species(limit: Annotated[int, Query(ge=1, le=250)] = 100) -> list[dict[str, object]]:
    ensure_database()
    return fetch_all(
        """
        SELECT species_normalized AS species, COUNT(*) AS incidents
        FROM public_incidents
        WHERE species_normalized IS NOT NULL
        GROUP BY species_normalized
        ORDER BY incidents DESC, species ASC
        LIMIT :limit
        """,
        {"limit": limit},
    )


@app.get("/locations")
def locations(
    country: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[dict[str, object]]:
    ensure_database()
    params: dict[str, object] = {"limit": limit}
    where = ""
    if country:
        where = "WHERE country_normalized = :country"
        params["country"] = country.upper()
    return fetch_all(
        f"""
        SELECT country_normalized AS country, area_normalized AS area, location_public AS location,
               COUNT(*) AS incidents
        FROM public_incidents
        {where}
        GROUP BY country_normalized, area_normalized, location_public
        ORDER BY incidents DESC, country ASC, area ASC
        LIMIT :limit
        """,
        params,
    )

