export type Coordinates = {
  lat: number;
  lon: number;
};

export type DominantFactor = {
  factor: string;
  value?: string | number | boolean | string[] | null;
  points?: number;
  contribution?: number;
  rationale?: string;
  contexts?: string[];
};

export type WarningResponse = {
  location: { geo: { type: "Point"; coordinates: [number, number] } };
  warning_score: number;
  warning_band: string;
  activity_context_score: number;
  activity_context_band: string;
  surveillance_priority_score?: number;
  confidence: number;
  dominant_factors: DominantFactor[];
  data_sources_used: string[];
  missing_data_sources: string[];
  active_pack?: string;
  pack_features_used?: string[];
  pack_notice?: string;
  disclaimer: string;
};

export type SurveillanceZone = {
  zone_id: string;
  surveillance_priority_score: number;
  surveillance_priority_band: string;
  warning_score: number;
  activity_context_score: number;
  center: { geo: { type: "Point"; coordinates: [number, number] } };
  radius_km: number;
  recommended_pattern: string;
  dominant_factors: DominantFactor[];
  confidence: number;
};

export type SurveillanceResponse = {
  zones: SurveillanceZone[];
  active_pack?: string;
  pack_features_used?: string[];
  pack_notice?: string;
  disclaimer: string;
};

export type Alert = {
  alert_type: string;
  level: string;
  title: string;
  summary: string;
  recommended_action: string;
  confidence: number;
  expires_at: string;
  zone?: { location?: { geo?: { coordinates: [number, number] } }; radius_km?: number };
  dominant_factors?: DominantFactor[];
  explanation_summary?: {
    operational_interpretation: string;
    recommended_surveillance_pattern?: string;
    dominant_factors?: DominantFactor[];
  };
  disclaimer?: string;
};

export type ReplayHeatmapCell = {
  lat: number;
  lon: number;
  surveillance_priority_score: number;
  surveillance_priority_band: string;
  warning_score?: number;
  warning_band?: string;
  activity_hazard_score?: number;
  activity_hazard_band?: string;
};

export type ReplayHeatmap = {
  score_type?: string;
  config: {
    center_lat: number;
    center_lon: number;
    radius_km: number;
    grid_cells: number;
  };
  cells: ReplayHeatmapCell[];
  statistics: {
    min_score: number;
    max_score: number;
    avg_score: number;
    median_score: number;
  };
};

export type DemoScenario = {
  scenario_id: string;
  label: string;
  region: string;
  context: string;
  activity_context: string;
  lat: number;
  lon: number;
  public_case_study?: string | null;
};

export type DemoStatus = {
  demo_mode: boolean;
  mode: string;
  database_configured?: boolean;
  admin_writes_enabled?: boolean | string;
  private_internal_data_exposed?: boolean;
  disclaimer?: string;
};

export type ProviderHealth = {
  provider: string;
  status: string;
  last_success?: string | null;
  last_error?: string | null;
  records_ingested?: number;
};

export type ExplanationResponse = {
  output_type: string;
  location: { geo: { type: "Point"; coordinates: [number, number] } };
  active_pack?: string;
  pack_notice?: string;
  pack_features_used?: string[];
  warning_score: number;
  activity_hazard_score: number;
  surveillance_priority_score: number;
  dominant_factors: DominantFactor[];
  factor_contributions: DominantFactor[];
  confidence_breakdown: {
    overall_confidence?: number;
    confidence_band?: string;
    components?: Record<string, unknown>;
  };
  data_freshness: Record<string, { status?: string; last_success?: string | null; last_error?: string | null }>;
  missing_data_sources: string[];
  regional_rules_triggered: string[];
  suppression_reasons: string[];
  operational_interpretation: string;
  recommended_action: string;
  recommended_surveillance_pattern: string;
  recommended_surveillance_pattern_label?: string;
  metadata: {
    model_version: string;
    scoring_revision: string;
    provider_stack_version: string;
    generated_at: string;
    replay_asset_version?: string;
  };
  disclaimer: string;
};

export type RegionalPack = {
  pack_id: string;
  name: string;
  covered_regions: string[];
  dominant_species: string[];
  features?: string[];
  required_access_tier?: string;
};

export type ReplayResult = {
  scenario_id: string;
  label: string;
  region: string;
  incident_day: {
    warning_score: number;
    surveillance_priority_score: number;
    activity_hazard_score: number;
    confidence: number;
  };
  quiet_day: {
    warning_score: number;
    surveillance_priority_score: number;
    activity_hazard_score: number;
    confidence: number;
  };
  confidence_decomposition: Record<string, number>;
  signal_decay_timeline: Array<{ signal_type: string; age_hours: number; decay_weight: number; decayed_value?: number }>;
  active_pack?: string;
  pack_features_used?: string[];
  pack_notice?: string;
};

export type ReplayLibraryItem = {
  id: string;
  title: string;
  region: string;
  coordinates: Coordinates;
  observed_at?: string | null;
  activity_context: string;
  species_context: string;
  replay_output: {
    warning_score: number;
    warning_band: string;
    activity_hazard_score: number;
    activity_hazard_band: string;
    surveillance_priority_score: number;
    surveillance_priority_band: string;
    confidence: number;
  };
  quiet_day_comparison: {
    warning_score: number;
    activity_hazard_score: number;
    surveillance_priority_score: number;
    confidence: number;
    summary: string;
  };
  factor_summary: DominantFactor[];
  explanation_summary: string;
  heatmap_asset?: string | null;
  model_version: string;
  scoring_revision: string;
  provider_stack_version: string;
  generated_at: string;
  disclaimer: string;
};

export type DashboardData = {
  warning: WarningResponse;
  surveillance: SurveillanceResponse;
  explanation: ExplanationResponse;
  alerts: Alert[];
  providerHealth: ProviderHealth[];
  packs: RegionalPack[];
  replay: ReplayResult;
  replayLibrary: ReplayLibraryItem[];
  replayHeatmap: ReplayHeatmap;
  demoScenarios: DemoScenario[];
  demoStatus: DemoStatus;
  data_source?: "mock" | "live";
};

export type DroneMission = {
  mission_id: string;
  drone_id: string;
  operator_role?: string;
  region?: string;
  pack_id?: string;
  mission_type?: string;
  started_at?: string;
  ended_at?: string | null;
  status?: string;
  recommended_pattern?: string;
  human_approved?: boolean;
  autonomous_flight_control?: boolean;
  source?: string;
  visibility?: string;
  notes_public?: string;
};

export type DroneTelemetrySummary = {
  timestamp?: string;
  latitude?: number;
  longitude?: number;
  altitude_m?: number | null;
  heading_deg?: number | null;
  groundspeed_mps?: number | null;
  battery_percent?: number | null;
  gps_fix_quality?: string | null;
  source?: string;
  source_type?: string;
};

export type DroneObservation = {
  observation_id?: string;
  mission_id: string;
  drone_id?: string;
  timestamp: string;
  latitude: number;
  longitude: number;
  observation_type: string;
  count?: number;
  estimated_length_m?: number | null;
  probable_species?: string | null;
  species_assessment_source?: string | null;
  species_confidence?: number | null;
  observed_behavior?: string | null;
  behavior_source?: string | null;
  evidence_type?: string | null;
  media_reference?: string | null;
  media_reference_type?: string | null;
  media_timestamp?: string | null;
  analyst_review_status?: string | null;
  analyst_reviewed_at?: string | null;
  analyst_reviewer_role?: string | null;
  analyst_notes_private?: string | null;
  public_review_summary?: string | null;
  review_outcome?: string | null;
  evidence_confidence?: number | null;
  confidence: number;
  review_status: string;
  source: string;
  source_type: string;
  visibility?: string;
  public_visibility?: boolean | string;
  active_pack?: string;
  recommended_surveillance_pattern?: string;
};

export type DroneFeedItem = {
  latitude: number;
  longitude: number;
  timestamp: string;
  observation_type: string;
  review_status: string;
  confidence: number;
  mission_id: string;
  source_type: string;
  active_pack?: string;
  explanation_summary?: string;
  recommended_action?: string;
  recommended_surveillance_pattern?: string;
  expires_at?: string;
  data_freshness?: { status?: string; source?: string };
};

export type DroneSurveillanceFeed = {
  disclaimer?: string;
  results: DroneFeedItem[];
  surveillance?: SurveillanceResponse;
  alerts?: Alert[];
  flight_control?: {
    autonomous_flight_control: boolean;
    commands_exposed: boolean;
    human_approval_required: boolean;
  };
};

export type DroneConsoleMissionOption = {
  mission: DroneMission;
  latestTelemetry?: DroneTelemetrySummary | null;
};

export type AnalystReviewUpdate = {
  analyst_review_status?: string | null;
  review_outcome?: string | null;
  public_review_summary?: string | null;
  analyst_notes_private?: string | null;
  analyst_reviewer_role?: string | null;
  media_reference_type?: string | null;
  evidence_confidence?: number | null;
  analyst_reviewed_at?: string | null;
};

export type DroneAttachment = {
  attachment_id: string;
  observation_id: string;
  mission_id: string;
  media_reference_type?: string | null;
  storage_backend?: "local_private_filesystem";
  media_kind: string;
  mime_type?: string | null;
  file_size_bytes?: number | null;
  captured_at?: string | null;
  uploaded_at?: string | null;
  review_visibility: string;
  public_release_status: string;
  analyst_review_status: string;
  public_summary?: string | null;
  evidence_confidence?: number | null;
  attachment_scope?: string;
  private_by_default?: boolean;
  public_feed_exposed?: boolean;
  media_analysis_performed?: boolean;
  sighting_created?: boolean;
};

export type DroneAttachmentPayload = {
  media_kind: string;
  media_reference_type?: string | null;
  original_filename?: string | null;
  mime_type?: string | null;
  file_size_bytes?: number | null;
  captured_at?: string | null;
  uploaded_by_role?: string | null;
  review_visibility?: string | null;
  public_release_status?: string | null;
  public_summary?: string | null;
  evidence_confidence?: number | null;
};

export const MEDIA_REFERENCE_TYPES = [
  "local_filename",
  "drone_clip_id",
  "camera_card_reference",
  "external_url",
  "agency_evidence_id",
  "private_case_reference",
  "none",
] as const;

export const ANALYST_REVIEW_STATUSES = [
  "unreviewed",
  "needs_review",
  "in_review",
  "reviewed",
  "rejected",
  "inconclusive",
] as const;

export const REVIEW_OUTCOMES = [
  "no_public_change",
  "confirms_operator_observation",
  "downgrades_operator_observation",
  "upgrades_operator_observation",
  "species_uncertain",
  "false_positive",
  "duplicate",
  "unusable_media",
] as const;

export const ATTACHMENT_MEDIA_KINDS = [
  "image",
  "video",
  "telemetry_snapshot",
  "observation_note",
  "agency_report_reference",
  "unknown",
] as const;

export const ATTACHMENT_VISIBILITIES = [
  "private_internal",
  "analyst_only",
  "operator_visible",
  "public_summary_only",
] as const;

export const UAV_SUBMITTER_ROLES = [
  "uav_operator",
  "lifeguard",
  "coastal_authority",
  "researcher",
  "agency_staff",
  "citizen_scientist",
  "project_owner",
  "unknown",
] as const;

export const UAV_ORGANIZATION_TYPES = [
  "government",
  "lifeguard_service",
  "research",
  "nonprofit",
  "private_operator",
  "volunteer",
  "independent",
  "unknown",
] as const;

export const UAV_TELEMETRY_OPTIONS = [
  "none",
  "unknown",
  "app_only",
  "export_file",
  "mavlink",
  "vendor_sdk",
  "manual_notes",
] as const;

export const UAV_MEDIA_WORKFLOWS = [
  "none",
  "sd_card",
  "app_gallery",
  "screen_recording",
  "agency_evidence_system",
  "external_reference",
  "local_reference_only",
  "unknown",
] as const;

export const UAV_FEEDBACK_REVIEW_STATUSES = [
  "new",
  "triaged",
  "needs_follow_up",
  "accepted_requirement",
  "rejected",
  "archived",
] as const;

export type UavOperatorFeedbackPayload = {
  submitter_role: string;
  organization_type: string;
  region?: string | null;
  country?: string | null;
  contact_allowed?: boolean;
  contact_reference?: string | null;
  drone_platform?: string | null;
  drone_model?: string | null;
  flight_app?: string | null;
  telemetry_available: string;
  telemetry_export_format?: string | null;
  media_workflow: string;
  no_sighting_patrols_logged?: boolean;
  observation_fields_used?: string[];
  privacy_constraints?: string[];
  controlled_airspace_notes?: string | null;
  operator_pain_points?: string[];
  requested_features?: string[];
  suggested_observation_types?: string[];
  workflow_notes?: string | null;
  public_summary?: string | null;
  internal_notes_private?: string | null;
  requirements_tags?: string[];
};

export type UavOperatorFeedback = UavOperatorFeedbackPayload & {
  feedback_id: string;
  submitted_at?: string;
  review_status: string;
  research_input_only: boolean;
  creates_sighting: boolean;
  creates_public_alert: boolean;
  alters_scoring: boolean;
  alters_replay: boolean;
};

export type DroneConsoleData = {
  missions: DroneConsoleMissionOption[];
  observations: DroneObservation[];
  feed: DroneSurveillanceFeed;
  data_source: "mock" | "live";
};

export type DroneObservationPayload = {
  timestamp: string;
  latitude: number;
  longitude: number;
  observation_type: string;
  count?: number;
  estimated_length_m?: number | null;
  probable_species?: string | null;
  species_assessment_source?: string | null;
  species_confidence?: number | null;
  observed_behavior?: string | null;
  behavior_source?: string | null;
  evidence_type?: string | null;
  media_reference?: string | null;
  media_reference_type?: string | null;
  media_timestamp?: string | null;
  analyst_notes?: string | null;
  analyst_review_status?: string | null;
  analyst_reviewed_at?: string | null;
  analyst_reviewer_role?: string | null;
  analyst_notes_private?: string | null;
  public_review_summary?: string | null;
  review_outcome?: string | null;
  evidence_confidence?: number | null;
  internal_notes?: string | null;
  confidence: number;
  review_status: string;
  source: string;
  source_type: string;
  public_visibility?: boolean | string;
};
