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

export type DashboardData = {
  warning: WarningResponse;
  surveillance: SurveillanceResponse;
  explanation: ExplanationResponse;
  alerts: Alert[];
  providerHealth: ProviderHealth[];
  packs: RegionalPack[];
  replay: ReplayResult;
};
