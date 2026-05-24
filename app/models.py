from __future__ import annotations

from datetime import datetime
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


class RiskSignals(BaseModel):
    historical_incident_count: int = 0
    recent_rainfall_mm_24h: float = 0
    river_mouth_distance_km: float | None = None
    sea_surface_temp_c: float | None = None
    fishing_activity: float = Field(default=0, ge=0, le=1)
    baitfish_prey_indicator: float = Field(default=0, ge=0, le=1)
    water_visibility_m: float | None = None
    human_water_activity: float = Field(default=0, ge=0, le=1)
    month: int | None = Field(default=None, ge=1, le=12)
    weekend: bool = False


class RiskFactorContribution(BaseModel):
    factor: str
    value: Any = None
    points: float
    max_points: float
    rationale: str


class PublicRiskResponse(BaseModel):
    location: PublicLocation
    score: float
    band: str
    warning_score: float
    warning_band: str
    confidence: float
    signals: RiskSignals
    factors: list[RiskFactorContribution]
    regional_profile: dict[str, Any] | None = None
    dominant_contributing_factors: list[RiskFactorContribution] = Field(default_factory=list)
    disclaimer: str


class RiskFactorDefinition(BaseModel):
    factor: str
    max_points: float
    description: str
    assumptions: str


class SignalSource(BaseModel):
    provider: str
    dataset: str | None = None
    url: str | None = None
    license: str | None = None
    citation: str | None = None


class SignalRelevance(BaseModel):
    score: float = Field(default=0, ge=0, le=1)
    factors: list[str] = Field(default_factory=list)
    rationale: str | None = None


class DataFreshness(BaseModel):
    status: str = "unknown"
    observed_at: datetime | None = None
    received_at: datetime | None = None
    age_hours: float | None = None
    max_age_hours: float | None = None


class Signal(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    signal_type: str
    species: str | None = None
    location: PublicLocation = Field(default_factory=PublicLocation)
    timestamp: datetime
    expires_at: datetime | None = None
    confidence: float = Field(default=0.5, ge=0, le=1)
    source: SignalSource
    data_freshness: DataFreshness = Field(default_factory=DataFreshness)
    risk_relevance: SignalRelevance = Field(default_factory=SignalRelevance)
    visibility: str = "public"
    value: Any = None
    units: str | None = None

    model_config = {"populate_by_name": True}


class ProviderRun(BaseModel):
    provider: str
    status: str = "success"
    started_at: datetime
    completed_at: datetime | None = None
    records_ingested: int = 0


class ProviderFailure(BaseModel):
    provider: str
    failed_at: datetime
    status: str = "failed"
    error_type: str | None = None
    error_summary: str | None = None


class SpeciesSeasonProfile(BaseModel):
    species: str
    region: str
    visibility: str = "public"
    active_months: list[int] = Field(default_factory=list)
    peak_months: list[int] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)


class MigrationWindow(BaseModel):
    species: str
    region: str
    visibility: str = "public"
    start_month: int = Field(ge=1, le=12)
    end_month: int = Field(ge=1, le=12)
    confidence: str = "unconfirmed"


class WarningSnapshot(BaseModel):
    visibility: str = "public"
    cache_key: str | None = None
    created_at: datetime
    expires_at: datetime | None = None
    location: PublicLocation = Field(default_factory=PublicLocation)
    response: dict[str, Any] = Field(default_factory=dict)


class User(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    email: str | None = None
    organization: str | None = None
    created_at: datetime | None = None
    status: str = "active"

    model_config = {"populate_by_name": True}


class ApiKey(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    user_id: str | None = None
    key_hash: str
    tier: str = "free"
    status: str = "active"
    created_at: datetime | None = None
    expires_at: datetime | None = None

    model_config = {"populate_by_name": True}


class UsageLog(BaseModel):
    api_key_id: str | None = None
    route: str
    method: str
    timestamp: datetime
    status_code: int | None = None
    tier: str = "free"


class BillingTier(BaseModel):
    tier: str
    monthly_request_limit: int | None = None
    rate_limit_per_minute: int
    allowed_route_groups: list[str] = Field(default_factory=list)
    commercial_use: bool = False


class RateLimit(BaseModel):
    tier: str
    route_group: str = "default"
    requests_per_minute: int


class SubscriptionStatus(BaseModel):
    user_id: str
    tier: str = "free"
    status: str = "active"
    current_period_end: datetime | None = None


class AlertZone(BaseModel):
    zone_id: str | None = None
    location: PublicLocation = Field(default_factory=PublicLocation)
    radius_km: float | None = None
    polygon: dict[str, Any] | None = None


class AlertTrigger(BaseModel):
    trigger_type: str
    threshold: float | None = None
    observed_value: float | None = None
    rationale: str | None = None


class AlertAudience(BaseModel):
    audiences: list[str] = Field(default_factory=lambda: ["api_users"])


class AlertDeliveryStatus(BaseModel):
    status: str = "not_sent"
    channels: list[str] = Field(default_factory=list)
    last_attempt_at: datetime | None = None


class AlertExpiration(BaseModel):
    created_at: datetime
    expires_at: datetime
    reason: str | None = None


class Alert(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    visibility: str = "public"
    status: str = "active"
    alert_type: str
    level: str
    title: str
    summary: str
    zone: AlertZone
    location: PublicLocation | None = None
    recommended_action: str
    dominant_factors: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    data_freshness: dict[str, Any] = Field(default_factory=dict)
    trigger: AlertTrigger
    audience: AlertAudience = Field(default_factory=AlertAudience)
    delivery_status: AlertDeliveryStatus = Field(default_factory=AlertDeliveryStatus)
    expiration: AlertExpiration
    expires_at: datetime | None = None
    disclaimer: str

    model_config = {"populate_by_name": True}


class RegionalPack(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    pack_id: str
    visibility: str = "public"
    name: str
    covered_regions: list[str] = Field(default_factory=list)
    dominant_species: list[str] = Field(default_factory=list)
    seasonal_windows: dict[str, Any] = Field(default_factory=dict)
    environmental_signals: list[str] = Field(default_factory=list)
    human_exposure_signals: list[str] = Field(default_factory=list)
    surveillance_rules: list[str] = Field(default_factory=list)
    alert_rules: list[str] = Field(default_factory=list)
    replay_scenarios: list[str] = Field(default_factory=list)
    docs_links: list[str] = Field(default_factory=list)
    required_access_tier: str = "free"
    features: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class PackEntitlement(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    visibility: str = "public"
    user_id: str | None = None
    organization: str | None = None
    pack_id: str
    access_tier: str = "free"
    status: str = "active"
    expires_at: datetime | None = None

    model_config = {"populate_by_name": True}


class PackFeature(BaseModel):
    pack_id: str
    feature_key: str
    visibility: str = "public"
    description: str | None = None
    enabled: bool = True


class PackReplayScenario(BaseModel):
    pack_id: str
    scenario_id: str
    visibility: str = "public"
    label: str | None = None
    tags: list[str] = Field(default_factory=list)


class PackSpeciesProfile(BaseModel):
    pack_id: str
    species: str
    visibility: str = "public"
    seasonal_windows: dict[str, Any] = Field(default_factory=dict)
    environmental_triggers: list[str] = Field(default_factory=list)
    surveillance_notes: list[str] = Field(default_factory=list)
