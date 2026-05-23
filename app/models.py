from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class IncidentDate(BaseModel):
    text: str | None = None
    year: int | None = None
    month: int | None = None
    day: int | None = None


class GeoPoint(BaseModel):
    type: str = "Point"
    coordinates: list[float] = Field(default_factory=list)


class PublicLocation(BaseModel):
    name: str | None = None
    geo: GeoPoint | None = None


class PublicSpecies(BaseModel):
    common: str | None = None
    scientific: str | None = None


class PublicSourceRef(BaseModel):
    name: str | None = None
    row_number: int | None = None
    source_record_id: str | None = None


class DuplicateInfo(BaseModel):
    is_duplicate: bool = False
    duplicate_of: str | None = None


class PublicIncident(BaseModel):
    id: str = Field(alias="_id")
    canonical_key: str | None = None
    date: IncidentDate = Field(default_factory=IncidentDate)
    incident_type: str | None = None
    country: str | None = None
    region: str | None = None
    location: PublicLocation = Field(default_factory=PublicLocation)
    activity: str | None = None
    sex: str | None = None
    age: str | None = None
    injury_summary: str | None = None
    fatal: bool = False
    species: PublicSpecies = Field(default_factory=PublicSpecies)
    source: PublicSourceRef = Field(default_factory=PublicSourceRef)
    duplicate: DuplicateInfo = Field(default_factory=DuplicateInfo)
    visibility: str = "public"

    model_config = {"populate_by_name": True}


class PaginatedIncidents(BaseModel):
    count: int
    limit: int
    offset: int
    results: list[PublicIncident]


class StatRow(BaseModel):
    key: Any = None
    incidents: int
    fatalities: int = 0
    fatality_rate_percent: float | None = None

