import { mockDashboardData, mockDemoScenarios, scenarioCoordinates } from "./mockData";
import type {
  Alert,
  Coordinates,
  DashboardData,
  DemoScenario,
  DemoStatus,
  ExplanationResponse,
  ProviderHealth,
  RegionalPack,
  ReplayHeatmap,
  ReplayResult,
  SurveillanceResponse,
  WarningResponse,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_AI1SAD_API_BASE_URL ?? "http://localhost:8000";
const USE_MOCKS = import.meta.env.VITE_AI1SAD_USE_MOCKS !== "false";
const DEMO_MODE = import.meta.env.VITE_AI1SAD_DEMO_MODE === "true";

async function requestJson<T>(path: string, fallback: T): Promise<T> {
  if (USE_MOCKS) {
    return fallback;
  }

  try {
    const response = await fetch(`${API_BASE_URL}${path}`);
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
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
  return requestJson(`/api/v1/warnings/location?${query({ lat: coords.lat, lon: coords.lon, bypass_cache: "true" })}`, mockDashboardData.warning);
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
  );
}

export async function getAlerts(): Promise<Alert[]> {
  const fallback = mockDashboardData.alerts;
  const response = await requestJson<Alert[] | { results?: Alert[] }>("/api/v1/alerts/active", fallback);
  return Array.isArray(response) ? response : response.results ?? fallback;
}

export async function getProviderHealth(): Promise<ProviderHealth[]> {
  const fallback = mockDashboardData.providerHealth;
  const response = await requestJson<ProviderHealth[] | { providers?: ProviderHealth[]; health?: ProviderHealth[] }>("/api/v1/provider-health", fallback);
  return Array.isArray(response) ? response : response.providers ?? response.health ?? fallback;
}

export async function getPacks(): Promise<RegionalPack[]> {
  const fallback = mockDashboardData.packs;
  const response = await requestJson<RegionalPack[] | { packs?: RegionalPack[] }>("/api/v1/packs", fallback);
  return Array.isArray(response) ? response : response.packs ?? fallback;
}

export async function getReplay(): Promise<ReplayResult> {
  return requestJson("/api/v1/replay/run?scenario_id=wa_spearfishing_reef_white", mockDashboardData.replay);
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
  );
}

export async function getDemoScenarios(): Promise<DemoScenario[]> {
  const response = await requestJson<DemoScenario[] | { scenarios?: DemoScenario[] }>("/api/v1/demo/scenarios", mockDemoScenarios);
  const scenarios = Array.isArray(response) ? response : response.scenarios ?? mockDemoScenarios;
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
  return requestJson("/api/v1/demo/status", fallback);
}

export async function getDashboardData(coords: Coordinates): Promise<DashboardData> {
  const [warning, surveillance, explanation, alerts, providerHealth, packs, replay, replayHeatmap, demoScenarios, demoStatus] = await Promise.all([
    getWarning(coords),
    getSurveillance(coords),
    getExplanation(coords),
    getAlerts(),
    getProviderHealth(),
    getPacks(),
    getReplay(),
    getReplayHeatmap(coords),
    getDemoScenarios(),
    getDemoStatus(),
  ]);

  return { warning, surveillance, explanation, alerts, providerHealth, packs, replay, replayHeatmap, demoScenarios, demoStatus };
}
