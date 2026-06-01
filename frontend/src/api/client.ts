import { mockDashboardData, mockDemoScenarios, mockReplayLibrary, scenarioCoordinates } from "./mockData";
import type {
  Alert,
  Coordinates,
  DashboardData,
  DemoScenario,
  DemoStatus,
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

async function requestJson<T>(path: string, fallback: T, validate?: Validator<T>): Promise<T> {
  if (useMocks()) {
    return fallback;
  }

  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed (${response.status}) for ${path}`);
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

export function __setMockModeForTests(value: boolean | null): void {
  mockModeOverride = value;
}
