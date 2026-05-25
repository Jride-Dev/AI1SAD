import { mockDashboardData } from "./mockData";
import type { Alert, Coordinates, DashboardData, ProviderHealth, RegionalPack, ReplayResult, SurveillanceResponse, WarningResponse } from "../types";

const API_BASE_URL = import.meta.env.VITE_AI1SAD_API_BASE_URL ?? "http://localhost:8000";
const USE_MOCKS = import.meta.env.VITE_AI1SAD_USE_MOCKS !== "false";

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
  return requestJson(
    `/api/v1/surveillance/search-zones?${query({
      lat: coords.lat,
      lon: coords.lon,
      radius_km: 5,
      mission_type: "drone",
      lookback_hours: 72,
      activity_context: "spearfishing",
      suspected_species: "white shark",
    })}`,
    mockDashboardData.surveillance,
  );
}

export async function getAlerts(): Promise<Alert[]> {
  return requestJson("/api/v1/alerts/active", mockDashboardData.alerts);
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

export async function getDashboardData(coords: Coordinates): Promise<DashboardData> {
  const [warning, surveillance, alerts, providerHealth, packs, replay] = await Promise.all([
    getWarning(coords),
    getSurveillance(coords),
    getAlerts(),
    getProviderHealth(),
    getPacks(),
    getReplay(),
  ]);

  return { warning, surveillance, alerts, providerHealth, packs, replay };
}
