import { Layers, MousePointer2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import type * as Leaflet from "leaflet";

import type { Alert, DashboardData, DemoScenario, DominantFactor, ExplanationResponse, ReplayHeatmapCell, SurveillanceZone } from "../types";

type LayerKey = "surveillance" | "warning" | "activity" | "alerts" | "heatmap" | "scenarios";

type SelectedFeature = {
  label: string;
  coordinates: { lat: number; lon: number };
  layer: string;
  active_pack?: string;
  warning_score?: number;
  activity_hazard_score?: number;
  surveillance_priority_score?: number;
  dominant_factors: DominantFactor[];
  factor_contributions: DominantFactor[];
  confidence_breakdown: ExplanationResponse["confidence_breakdown"];
  recommended_action: string;
  recommended_surveillance_pattern: string;
  disclaimer: string;
};

const layerOptions: Array<{ key: LayerKey; label: string }> = [
  { key: "surveillance", label: "Surveillance priority" },
  { key: "warning", label: "Warning score" },
  { key: "activity", label: "Activity hazard" },
  { key: "alerts", label: "Active alerts" },
  { key: "heatmap", label: "Replay heatmap" },
  { key: "scenarios", label: "Demo scenarios" },
];

export function OperationalMap({
  data,
  selectedScenarioId,
  onSelectScenario,
}: {
  data: DashboardData;
  selectedScenarioId: string;
  onSelectScenario: (scenarioId: string) => void;
}) {
  const mapNode = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Leaflet.Map | null>(null);
  const layerRef = useRef<Leaflet.LayerGroup | null>(null);
  const [selectedFeature, setSelectedFeature] = useState<SelectedFeature>(() => buildFeatureFromExplanation(data.explanation));
  const [visibleLayers, setVisibleLayers] = useState<Record<LayerKey, boolean>>({
    surveillance: true,
    warning: true,
    activity: true,
    alerts: true,
    heatmap: true,
    scenarios: true,
  });

  const selectedScenario = data.demoScenarios.find((scenario) => scenario.scenario_id === selectedScenarioId) ?? data.demoScenarios[0];
  const mapCenter = useMemo<[number, number]>(() => {
    if (selectedScenario) return [selectedScenario.lat, selectedScenario.lon];
    const [lon, lat] = data.warning.location.geo.coordinates;
    return [lat, lon];
  }, [data.warning.location.geo.coordinates, selectedScenario]);

  useEffect(() => {
    setSelectedFeature(buildFeatureFromExplanation(data.explanation));
  }, [data]);

  useEffect(() => {
    let cancelled = false;
    async function initializeMap() {
      if (!mapNode.current || mapRef.current) return;
      const L = await import("leaflet");
      if (cancelled || !mapNode.current) return;
      mapRef.current = L.map(mapNode.current, { zoomControl: true, attributionControl: true }).setView(mapCenter, 11);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }).addTo(mapRef.current);
      layerRef.current = L.layerGroup().addTo(mapRef.current);
    }
    initializeMap();
    return () => {
      cancelled = true;
    };
  }, [mapCenter]);

  useEffect(() => {
    let cancelled = false;
    async function drawLayers() {
      const map = mapRef.current;
      const layers = layerRef.current;
      if (!map || !layers) return;
      const L = await import("leaflet");
      if (cancelled) return;

      layers.clearLayers();
      map.setView(mapCenter, 11);

      if (visibleLayers.heatmap) {
        data.replayHeatmap.cells.forEach((cell) => {
          const feature = buildFeatureFromHeatmapCell(cell, data.explanation);
          L.circleMarker([cell.lat, cell.lon], {
            radius: Math.max(7, Math.min(20, cell.surveillance_priority_score / 5)),
            color: bandColor(cell.surveillance_priority_band),
            fillColor: bandColor(cell.surveillance_priority_band),
            fillOpacity: 0.34,
            weight: 1,
          })
            .on("click", () => setSelectedFeature(feature))
            .addTo(layers);
        });
      }

      data.surveillance.zones.forEach((zone) => {
        const [lon, lat] = zone.center.geo.coordinates;
        if (visibleLayers.surveillance) {
          L.circle([lat, lon], {
            radius: zone.radius_km * 1000,
            color: bandColor(zone.surveillance_priority_band),
            fillColor: bandColor(zone.surveillance_priority_band),
            fillOpacity: 0.12,
            weight: 2,
          })
            .on("click", () => setSelectedFeature(buildFeatureFromZone(zone, data.explanation)))
            .addTo(layers);
        }
        if (visibleLayers.warning) {
          L.circleMarker([lat, lon], {
            radius: Math.max(6, zone.warning_score / 5),
            color: "#377b8a",
            fillColor: "#377b8a",
            fillOpacity: 0.72,
            weight: 1,
          })
            .on("click", () => setSelectedFeature(buildFeatureFromZone(zone, data.explanation, "Warning score marker")))
            .addTo(layers);
        }
        if (visibleLayers.activity) {
          L.circleMarker([lat, lon], {
            radius: Math.max(6, zone.activity_context_score / 5),
            color: "#9b5c1e",
            fillColor: "#d68a3c",
            fillOpacity: 0.72,
            weight: 1,
          })
            .on("click", () => setSelectedFeature(buildFeatureFromZone(zone, data.explanation, "Activity hazard marker")))
            .addTo(layers);
        }
      });

      if (visibleLayers.alerts) {
        data.alerts.forEach((alert) => {
          const coords = alert.zone?.location?.geo?.coordinates;
          if (!coords) return;
          const [lon, lat] = coords;
          L.circleMarker([lat, lon], {
            radius: 13,
            color: "#a7352a",
            fillColor: "#e04b39",
            fillOpacity: 0.82,
            weight: 2,
          })
            .on("click", () => setSelectedFeature(buildFeatureFromAlert(alert, data.explanation)))
            .addTo(layers);
        });
      }

      if (visibleLayers.scenarios) {
        data.demoScenarios.forEach((scenario) => {
          L.circleMarker([scenario.lat, scenario.lon], {
            radius: scenario.scenario_id === selectedScenarioId ? 11 : 8,
            color: "#1d4f43",
            fillColor: scenario.scenario_id === selectedScenarioId ? "#2da77b" : "#dcefe8",
            fillOpacity: 0.92,
            weight: 2,
          })
            .on("click", () => {
              onSelectScenario(scenario.scenario_id);
              setSelectedFeature(buildFeatureFromScenario(scenario, data.explanation));
            })
            .addTo(layers);
        });
      }
    }
    drawLayers();
    return () => {
      cancelled = true;
    };
  }, [data, mapCenter, onSelectScenario, selectedScenarioId, visibleLayers]);

  return (
    <div className="operational-map-layout">
      <section className="map-panel leaflet-panel">
        <div className="map-toolbar">
          <label>
            <span>Scenario</span>
            <select value={selectedScenarioId} onChange={(event) => onSelectScenario(event.target.value)}>
              {data.demoScenarios.map((scenario) => (
                <option key={scenario.scenario_id} value={scenario.scenario_id}>
                  {scenario.label}
                </option>
              ))}
            </select>
          </label>
          <div className="layer-toggle-group" aria-label="Map layers">
            {layerOptions.map((layer) => (
              <label key={layer.key}>
                <input
                  checked={visibleLayers[layer.key]}
                  onChange={(event) => setVisibleLayers((current) => ({ ...current, [layer.key]: event.target.checked }))}
                  type="checkbox"
                />
                <span>{layer.label}</span>
              </label>
            ))}
          </div>
        </div>
        <div className="leaflet-map" ref={mapNode} />
        <MapLegend />
      </section>

      <section className="panel why-panel">
        <div className="why-heading">
          <MousePointer2 size={18} aria-hidden="true" />
          <div>
            <p className="eyebrow">{selectedFeature.layer}</p>
            <h2>Why This Zone?</h2>
          </div>
        </div>
        <h3>{selectedFeature.label}</h3>
        <div className="coordinate-strip compact-strip">
          <span>Lat {selectedFeature.coordinates.lat.toFixed(4)}</span>
          <span>Lon {selectedFeature.coordinates.lon.toFixed(4)}</span>
          <span>{selectedFeature.active_pack ?? "core"}</span>
        </div>
        <div className="score-split-card">
          <ScoreBadge label="Warning" value={selectedFeature.warning_score ?? 0} />
          <ScoreBadge label="Activity Hazard" value={selectedFeature.activity_hazard_score ?? 0} />
          <ScoreBadge label="Surveillance Priority" value={selectedFeature.surveillance_priority_score ?? 0} />
        </div>
        {isLowWarningHighSurveillance(selectedFeature) ? (
          <p className="split-note">Low general warning with high activity/habitat-specific surveillance priority.</p>
        ) : null}
        <h3>Dominant Factors</h3>
        <FactorMiniList factors={selectedFeature.dominant_factors} />
        <h3>Factor Contributions</h3>
        <FactorMiniList factors={selectedFeature.factor_contributions} />
        <h3>Confidence</h3>
        <ConfidenceMini breakdown={selectedFeature.confidence_breakdown} />
        <h3>Recommended Action</h3>
        <p className="explain-text">{selectedFeature.recommended_action}</p>
        <div className="chip-row">
          <span className="chip">{selectedFeature.recommended_surveillance_pattern}</span>
        </div>
        <p className="disclaimer-text">{selectedFeature.disclaimer}</p>
      </section>
    </div>
  );
}

function buildFeatureFromExplanation(explanation: ExplanationResponse): SelectedFeature {
  const [lon, lat] = explanation.location.geo.coordinates;
  return {
    label: "Selected operational location",
    coordinates: { lat, lon },
    layer: "Explanation endpoint",
    active_pack: explanation.active_pack,
    warning_score: explanation.warning_score,
    activity_hazard_score: explanation.activity_hazard_score,
    surveillance_priority_score: explanation.surveillance_priority_score,
    dominant_factors: explanation.dominant_factors,
    factor_contributions: explanation.factor_contributions,
    confidence_breakdown: explanation.confidence_breakdown,
    recommended_action: explanation.recommended_action,
    recommended_surveillance_pattern: explanation.recommended_surveillance_pattern_label ?? explanation.recommended_surveillance_pattern,
    disclaimer: explanation.disclaimer,
  };
}

function buildFeatureFromZone(zone: SurveillanceZone, explanation: ExplanationResponse, layer = "Surveillance priority zone"): SelectedFeature {
  const [lon, lat] = zone.center.geo.coordinates;
  return {
    ...buildFeatureFromExplanation(explanation),
    label: zone.zone_id,
    coordinates: { lat, lon },
    layer,
    warning_score: zone.warning_score,
    activity_hazard_score: zone.activity_context_score,
    surveillance_priority_score: zone.surveillance_priority_score,
    dominant_factors: zone.dominant_factors,
    recommended_surveillance_pattern: zone.recommended_pattern,
  };
}

function buildFeatureFromHeatmapCell(cell: ReplayHeatmapCell, explanation: ExplanationResponse): SelectedFeature {
  return {
    ...buildFeatureFromExplanation(explanation),
    label: "Replay heatmap cell",
    coordinates: { lat: cell.lat, lon: cell.lon },
    layer: "Replay surveillance heatmap",
    warning_score: cell.warning_score,
    activity_hazard_score: cell.activity_hazard_score,
    surveillance_priority_score: cell.surveillance_priority_score,
  };
}

function buildFeatureFromScenario(scenario: DemoScenario, explanation: ExplanationResponse): SelectedFeature {
  return {
    ...buildFeatureFromExplanation(explanation),
    label: scenario.label,
    coordinates: { lat: scenario.lat, lon: scenario.lon },
    layer: "Demo scenario point",
    recommended_action: scenario.context,
  };
}

function buildFeatureFromAlert(alert: Alert, explanation: ExplanationResponse): SelectedFeature {
  const coords = alert.zone?.location?.geo?.coordinates ?? explanation.location.geo.coordinates;
  const [lon, lat] = coords;
  return {
    ...buildFeatureFromExplanation(explanation),
    label: alert.title,
    coordinates: { lat, lon },
    layer: "Active alert",
    dominant_factors: alert.dominant_factors ?? explanation.dominant_factors,
    recommended_action: alert.recommended_action,
    disclaimer: alert.disclaimer ?? explanation.disclaimer,
  };
}

function bandColor(band: string | undefined): string {
  if (band === "urgent_surveillance" || band === "high") return "#c43d2c";
  if (band === "elevated") return "#d6872e";
  if (band === "moderate") return "#d5b23f";
  if (band === "low") return "#32886f";
  return "#5d7370";
}

function isLowWarningHighSurveillance(feature: SelectedFeature): boolean {
  return (feature.warning_score ?? 0) < 35 && (feature.surveillance_priority_score ?? 0) >= 70;
}

function MapLegend() {
  const items = [
    ["low", "#32886f"],
    ["moderate", "#d5b23f"],
    ["elevated", "#d6872e"],
    ["high", "#c43d2c"],
    ["urgent surveillance", "#7f1d1d"],
  ];
  return (
    <div className="map-legend">
      <Layers size={16} aria-hidden="true" />
      {items.map(([label, color]) => (
        <span key={label}>
          <i style={{ background: color }} />
          {label}
        </span>
      ))}
    </div>
  );
}

function ScoreBadge({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{Math.round(value)}</strong>
    </div>
  );
}

function FactorMiniList({ factors }: { factors: DominantFactor[] }) {
  if (!factors.length) return <p className="explain-text">No factor details were returned for this feature.</p>;
  return (
    <div className="factor-list compact-factor-list">
      {factors.slice(0, 4).map((factor) => (
        <div key={`${factor.factor}-${factor.points ?? factor.contribution ?? ""}`}>
          <span>{factor.factor.replaceAll("_", " ")}</span>
          <strong>{factor.points ? `${Math.round(factor.points)} pts` : factor.contribution ? `${Math.round(factor.contribution * 100)}%` : "context"}</strong>
        </div>
      ))}
    </div>
  );
}

function ConfidenceMini({ breakdown }: { breakdown: ExplanationResponse["confidence_breakdown"] }) {
  const confidence = Math.round((breakdown.overall_confidence ?? 0) * 100);
  return (
    <div className="confidence-mini">
      <span>{breakdown.confidence_band ?? "limited"}</span>
      <strong>{confidence}%</strong>
    </div>
  );
}
