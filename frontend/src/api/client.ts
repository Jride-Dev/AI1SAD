import { mockDashboardData, mockDemoScenarios, mockDroneConsoleData, mockReplayLibrary, scenarioCoordinates } from "./mockData";
import type {
  Alert,
  AnalystReviewUpdate,
  Coordinates,
  DashboardData,
  DemoScenario,
  DemoStatus,
  DroneAttachment,
  DroneAttachmentPayload,
  DroneConsoleData,
  DroneConsoleMissionOption,
  DroneObservation,
  DroneObservationPayload,
  DroneSurveillanceFeed,
  ExplanationResponse,
  ProviderHealth,
  RegionalPack,
  ReplayLibraryItem,
  ReplayHeatmap,
  ReplayResult,
  SurveillanceResponse,
  WarningResponse,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_AI1SAD_API_BASE_URL ?? "http://localhost:8000";
const DEMO_MODE = import.meta.env.VITE_AI1SAD_DEMO_MODE === "true";
let mockModeOverride: boolean | null = null;

function useMocks(): boolean {
  if (mockModeOverride !== null) {
    return mockModeOverride;
  }
  return import.meta.env.VITE_AI1SAD_USE_MOCKS !== "false";
}

type Validator<T> = (value: unknown) => value is T;

async function requestJson<T>(path: string, fallback: T, validate?: Validator<T>, init?: RequestInit): Promise<T> {
  if (useMocks()) {
    return fallback;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    let detail = "";
    try {
      const errorPayload = await response.json();
      if (errorPayload && typeof errorPayload === "object" && "detail" in errorPayload) {
        detail = `: ${String((errorPayload as { detail: unknown }).detail)}`;
      }
    } catch {
      detail = "";
    }
    throw new Error(`Request failed (${response.status}) for ${path}${detail}`);
  }
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new Error(`Malformed JSON payload for ${path}`);
  }
  if (validate && !validate(payload)) {
    throw new Error(`Malformed API payload for ${path}`);
  }
  return payload as T;
}

function postJson<T>(path: string, payload: unknown, fallback: T, validate?: Validator<T>): Promise<T> {
  return requestJson(path, fallback, validate, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

function query(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined) {
      search.set(key, String(value));
    }
  });
  return search.toString();
}

export async function getWarning(coords: Coordinates): Promise<WarningResponse> {
  return requestJson(
    `/api/v1/warnings/location?${query({ lat: coords.lat, lon: coords.lon, bypass_cache: "true" })}`,
    mockDashboardData.warning,
    (value): value is WarningResponse => Boolean(value && typeof value === "object" && "warning_score" in value),
  );
}

export async function getSurveillance(coords: Coordinates): Promise<SurveillanceResponse> {
  const scenario = Object.values(scenarioCoordinates).find((item) => item.lat === coords.lat && item.lon === coords.lon);
  return requestJson(
    `/api/v1/surveillance/search-zones?${query({
      lat: coords.lat,
      lon: coords.lon,
      radius_km: 5,
      mission_type: "drone",
      lookback_hours: 72,
      activity_context: scenario?.activityContext ?? "spearfishing",
      suspected_species: scenario?.suspectedSpecies ?? "white shark",
    })}`,
    mockDashboardData.surveillance,
    (value): value is SurveillanceResponse => Boolean(value && typeof value === "object" && "zones" in value && Array.isArray((value as { zones: unknown }).zones)),
  );
}

export async function getExplanation(coords: Coordinates): Promise<ExplanationResponse> {
  const scenario = Object.values(scenarioCoordinates).find((item) => item.lat === coords.lat && item.lon === coords.lon);
  return requestJson(
    `/api/v1/explain/location?${query({
      lat: coords.lat,
      lon: coords.lon,
      radius_km: 10,
      activity_context: scenario?.activityContext ?? "spearfishing",
      suspected_species: scenario?.suspectedSpecies ?? "white shark",
    })}`,
    mockDashboardData.explanation,
    (value): value is ExplanationResponse => Boolean(value && typeof value === "object" && "factor_contributions" in value),
  );
}

export async function getAlerts(): Promise<Alert[]> {
  const response = await requestJson<Alert[] | { results: Alert[] }>(
    "/api/v1/alerts/active",
    mockDashboardData.alerts,
    (value): value is Alert[] | { results: Alert[] } =>
      Array.isArray(value) || Boolean(value && typeof value === "object" && Array.isArray((value as { results?: unknown }).results)),
  );
  return Array.isArray(response) ? response : response.results;
}

export async function getProviderHealth(): Promise<ProviderHealth[]> {
  const response = await requestJson<ProviderHealth[] | { providers?: ProviderHealth[]; health?: ProviderHealth[] }>(
    "/api/v1/provider-health",
    mockDashboardData.providerHealth,
    (value): value is ProviderHealth[] | { providers?: ProviderHealth[]; health?: ProviderHealth[] } =>
      Array.isArray(value) ||
      Boolean(
        value &&
          typeof value === "object" &&
          (Array.isArray((value as { providers?: unknown }).providers) || Array.isArray((value as { health?: unknown }).health)),
      ),
  );
  return Array.isArray(response) ? response : response.providers ?? response.health ?? [];
}

export async function getPacks(): Promise<RegionalPack[]> {
  const response = await requestJson<RegionalPack[] | { packs: RegionalPack[] }>(
    "/api/v1/packs",
    mockDashboardData.packs,
    (value): value is RegionalPack[] | { packs: RegionalPack[] } =>
      Array.isArray(value) || Boolean(value && typeof value === "object" && Array.isArray((value as { packs?: unknown }).packs)),
  );
  return Array.isArray(response) ? response : response.packs;
}

export async function getReplay(): Promise<ReplayResult> {
  return requestJson(
    "/api/v1/replay/run?scenario_id=wa_spearfishing_reef_white",
    mockDashboardData.replay,
    (value): value is ReplayResult => Boolean(value && typeof value === "object" && "signal_decay_timeline" in value),
  );
}

export async function getReplayLibrary(): Promise<ReplayLibraryItem[]> {
  const response = await requestJson<ReplayLibraryItem[] | { results: ReplayLibraryItem[] }>(
    "/api/v1/replay/library",
    mockReplayLibrary,
    (value): value is ReplayLibraryItem[] | { results: ReplayLibraryItem[] } =>
      Array.isArray(value) || Boolean(value && typeof value === "object" && Array.isArray((value as { results?: unknown }).results)),
  );
  return Array.isArray(response) ? response : response.results;
}

export async function getReplayHeatmap(coords: Coordinates): Promise<ReplayHeatmap> {
  const scenario = Object.values(scenarioCoordinates).find((item) => item.lat === coords.lat && item.lon === coords.lon);
  return requestJson(
    `/api/v1/replay/heatmap?${query({
      lat: coords.lat,
      lon: coords.lon,
      radius_km: 8,
      grid_points: 7,
      activity_context: scenario?.activityContext ?? "spearfishing",
      suspected_species: scenario?.suspectedSpecies ?? "white shark",
      month: scenario?.month,
    })}`,
    mockDashboardData.replayHeatmap,
    (value): value is ReplayHeatmap => Boolean(value && typeof value === "object" && "cells" in value),
  );
}

export async function getDemoScenarios(): Promise<DemoScenario[]> {
  const response = await requestJson<DemoScenario[] | { scenarios: DemoScenario[] }>(
    "/api/v1/demo/scenarios",
    mockDemoScenarios,
    (value): value is DemoScenario[] | { scenarios: DemoScenario[] } =>
      Array.isArray(value) || Boolean(value && typeof value === "object" && Array.isArray((value as { scenarios?: unknown }).scenarios)),
  );
  const scenarios = Array.isArray(response) ? response : response.scenarios;
  return scenarios.map((scenario) => {
    const coords = scenarioCoordinates[scenario.scenario_id];
    return {
      ...scenario,
      lat: scenario.lat ?? coords?.lat ?? 0,
      lon: scenario.lon ?? coords?.lon ?? 0,
    };
  });
}

export async function getDemoStatus(): Promise<DemoStatus> {
  const fallback = { ...mockDashboardData.demoStatus, demo_mode: DEMO_MODE || mockDashboardData.demoStatus.demo_mode };
  return requestJson(
    "/api/v1/demo/status",
    fallback,
    (value): value is DemoStatus => Boolean(value && typeof value === "object" && "demo_mode" in value),
  );
}

export async function getDashboardData(coords: Coordinates): Promise<DashboardData> {
  const [warning, surveillance, explanation, alerts, providerHealth, packs, replay, replayLibrary, replayHeatmap, demoScenarios, demoStatus] = await Promise.all([
    getWarning(coords),
    getSurveillance(coords),
    getExplanation(coords),
    getAlerts(),
    getProviderHealth(),
    getPacks(),
    getReplay(),
    getReplayLibrary(),
    getReplayHeatmap(coords),
    getDemoScenarios(),
    getDemoStatus(),
  ]);

  return {
    warning,
    surveillance,
    explanation,
    alerts,
    providerHealth,
    packs,
    replay,
    replayLibrary,
    replayHeatmap,
    demoScenarios,
    demoStatus,
    data_source: useMocks() ? "mock" : "live",
  };
}

export async function getDroneSurveillanceFeed(): Promise<DroneSurveillanceFeed> {
  return requestJson(
    "/api/v1/drone/surveillance-feed",
    mockDroneConsoleData.feed,
    (value): value is DroneSurveillanceFeed =>
      Boolean(value && typeof value === "object" && Array.isArray((value as { results?: unknown }).results)),
  );
}

export async function getDroneActiveObservations(): Promise<DroneObservation[]> {
  const response = await requestJson<DroneObservation[] | { results: DroneObservation[] }>(
    "/api/v1/drone/active-observations",
    mockDroneConsoleData.observations,
    (value): value is DroneObservation[] | { results: DroneObservation[] } =>
      Array.isArray(value) || Boolean(value && typeof value === "object" && Array.isArray((value as { results?: unknown }).results)),
  );
  return Array.isArray(response) ? response : response.results;
}

export async function getDroneMission(missionId: string): Promise<DroneConsoleMissionOption> {
  const fallback = mockDroneConsoleData.missions.find((item) => item.mission.mission_id === missionId) ?? mockDroneConsoleData.missions[0];
  const response = await requestJson<{ mission: DroneConsoleMissionOption["mission"] }>(
    `/api/v1/drone/missions/${encodeURIComponent(missionId)}`,
    { mission: fallback.mission },
    (value): value is { mission: DroneConsoleMissionOption["mission"] } =>
      Boolean(value && typeof value === "object" && "mission" in value),
  );
  return { mission: response.mission, latestTelemetry: fallback.latestTelemetry ?? null };
}

export async function getDroneMissionObservations(missionId: string): Promise<DroneObservation[]> {
  const fallback = mockDroneConsoleData.observations.filter((item) => item.mission_id === missionId);
  const response = await requestJson<DroneObservation[] | { results: DroneObservation[] }>(
    `/api/v1/drone/missions/${encodeURIComponent(missionId)}/observations`,
    fallback,
    (value): value is DroneObservation[] | { results: DroneObservation[] } =>
      Array.isArray(value) || Boolean(value && typeof value === "object" && Array.isArray((value as { results?: unknown }).results)),
  );
  return Array.isArray(response) ? response : response.results;
}

export async function getDroneConsoleData(): Promise<DroneConsoleData> {
  if (useMocks()) {
    return mockDroneConsoleData;
  }
  const [feed, observations] = await Promise.all([getDroneSurveillanceFeed(), getDroneActiveObservations()]);
  const missionIds = Array.from(new Set([...feed.results.map((item) => item.mission_id), ...observations.map((item) => item.mission_id)].filter(Boolean)));
  const missions: DroneConsoleMissionOption[] = missionIds.map((missionId) => {
    const observation = observations.find((item) => item.mission_id === missionId);
    const feedItem = feed.results.find((item) => item.mission_id === missionId);
    return {
      mission: {
        mission_id: missionId,
        drone_id: observation?.drone_id ?? "unknown",
        status: "active",
        mission_type: feedItem?.recommended_surveillance_pattern ?? "manual_observation_patrol",
        recommended_pattern: feedItem?.recommended_surveillance_pattern,
        pack_id: observation?.active_pack ?? feedItem?.active_pack,
        human_approved: true,
        autonomous_flight_control: false,
        source: observation?.source ?? "drone_observation_intake",
        visibility: observation?.visibility ?? "public",
      },
      latestTelemetry: null,
    };
  });
  return { missions, observations, feed, data_source: "live" };
}

export async function submitDroneObservation(missionId: string, payload: DroneObservationPayload): Promise<DroneObservation> {
  const fallback: DroneObservation = {
    ...mockDroneConsoleData.observations[0],
    ...payload,
    mission_id: missionId,
    observation_id: `mock-${payload.observation_type}-${Date.now()}`,
    drone_id: mockDroneConsoleData.missions.find((item) => item.mission.mission_id === missionId)?.mission.drone_id,
  };
  const response = await postJson<{ observation: DroneObservation }>(
    `/api/v1/drone/missions/${encodeURIComponent(missionId)}/observations`,
    payload,
    { observation: fallback },
    (value): value is { observation: DroneObservation } =>
      Boolean(value && typeof value === "object" && "observation" in value),
  );
  return response.observation;
}

export async function submitObservationReview(missionId: string, observationId: string, payload: AnalystReviewUpdate): Promise<DroneObservation> {
  const fallback: DroneObservation = {
    ...mockDroneConsoleData.observations.find((item) => item.observation_id === observationId) ?? mockDroneConsoleData.observations[0],
    mission_id: missionId,
    ...payload,
  };
  const response = await requestJson<{ observation: DroneObservation }>(
    `/api/v1/drone/missions/${encodeURIComponent(missionId)}/observations/${encodeURIComponent(observationId)}`,
    { observation: fallback },
    (value): value is { observation: DroneObservation } =>
      Boolean(value && typeof value === "object" && "observation" in value),
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
  return response.observation;
}

export async function getObservationAttachments(observationId: string): Promise<DroneAttachment[]> {
  const fallback: DroneAttachment[] = [];
  const response = await requestJson<DroneAttachment[] | { results: DroneAttachment[] }>(
    `/api/v1/drone/observations/${encodeURIComponent(observationId)}/attachments`,
    fallback,
    (value): value is DroneAttachment[] | { results: DroneAttachment[] } =>
      Array.isArray(value) || Boolean(value && typeof value === "object" && Array.isArray((value as { results?: unknown }).results)),
  );
  return Array.isArray(response) ? response : response.results;
}

export async function submitObservationAttachment(observationId: string, payload: DroneAttachmentPayload): Promise<DroneAttachment> {
  const fallback: DroneAttachment = {
    attachment_id: `mock-attachment-${Date.now()}`,
    observation_id: observationId,
    mission_id: mockDroneConsoleData.observations.find((item) => item.observation_id === observationId)?.mission_id ?? "mock-mission",
    media_kind: payload.media_kind,
    media_reference_type: payload.media_reference_type,
    mime_type: payload.mime_type,
    file_size_bytes: payload.file_size_bytes,
    captured_at: payload.captured_at,
    uploaded_at: new Date().toISOString(),
    review_visibility: payload.review_visibility ?? "analyst_only",
    public_release_status: payload.public_release_status ?? "not_reviewed",
    analyst_review_status: "unreviewed",
    public_summary: payload.public_summary,
    evidence_confidence: payload.evidence_confidence,
    attachment_scope: "metadata_only_local",
    private_by_default: true,
    public_feed_exposed: false,
    media_analysis_performed: false,
    sighting_created: false,
  };
  const response = await postJson<{ attachment: DroneAttachment }>(
    `/api/v1/drone/observations/${encodeURIComponent(observationId)}/attachments`,
    payload,
    { attachment: fallback },
    (value): value is { attachment: DroneAttachment } =>
      Boolean(value && typeof value === "object" && "attachment" in value),
  );
  return response.attachment;
}

export function __setMockModeForTests(value: boolean | null): void {
  mockModeOverride = value;
}
