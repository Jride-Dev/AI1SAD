import { Activity, AlertTriangle, Boxes, ExternalLink, HeartPulse, Map, Plane, Radar, RotateCcw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { getDashboardData } from "./api/client";
import { scenarioCoordinates } from "./api/mockData";
import { OperationalMap } from "./components/OperationalMap";
import type { DashboardData, DominantFactor, ExplanationResponse, ProviderHealth } from "./types";

const pages = [
  { id: "map", label: "Live Map", icon: Map },
  { id: "surveillance", label: "Surveillance", icon: Plane },
  { id: "replay", label: "Replay", icon: RotateCcw },
  { id: "alerts", label: "Alerts", icon: AlertTriangle },
  { id: "health", label: "Provider Health", icon: HeartPulse },
  { id: "packs", label: "Regional Packs", icon: Boxes },
] as const;

type PageId = (typeof pages)[number]["id"];

export default function App() {
  const [activePage, setActivePage] = useState<PageId>("map");
  const [selectedScenarioId, setSelectedScenarioId] = useState("horseshoe_reef_2026");
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const scenario = scenarioCoordinates[selectedScenarioId] ?? scenarioCoordinates.horseshoe_reef_2026;
    setLoading(true);
    setError(null);
    getDashboardData({ lat: scenario.lat, lon: scenario.lon })
      .then((payload) => {
        if (cancelled) return;
        setData(payload);
      })
      .catch((reason: unknown) => {
        if (cancelled) return;
        setError(reason instanceof Error ? reason.message : "Dashboard data could not be loaded.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedScenarioId]);

  const page = useMemo(() => pages.find((item) => item.id === activePage) ?? pages[0], [activePage]);

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <img src="/brand/logo-mark.svg" alt="AI1SAD logo" className="brand-mark" />
          <div>
            <strong>AI1SAD</strong>
            <span>Marine intelligence operations</span>
          </div>
        </div>
        <nav className="nav" aria-label="Dashboard views">
          {pages.map((item) => {
            const Icon = item.icon;
            return (
              <button key={item.id} className={item.id === activePage ? "active" : ""} onClick={() => setActivePage(item.id)} type="button">
                <Icon size={18} aria-hidden="true" />
                <span>{item.label}</span>
              </button>
            );
          })}
          <a href="http://localhost:8001" target="_blank" rel="noreferrer">
            <ExternalLink size={18} aria-hidden="true" />
            <span>Docs</span>
          </a>
        </nav>
      </aside>

      <section className="workspace">
        {data?.demoStatus.demo_mode ? <DemoBanner /> : null}
        <header className="topbar">
          <div className="topbar-title">
            <img src="/brand/avatar.svg" alt="" aria-hidden="true" className="topbar-avatar" />
            <div>
            <p className="eyebrow">Mock mode dashboard shell</p>
            <h1>{page.label}</h1>
            </div>
          </div>
          <div className="status-pill">
            <Activity size={16} aria-hidden="true" />
            Existing API outputs only
          </div>
        </header>

        {error ? <ErrorPanel message={error} /> : loading || !data ? <LoadingPanel /> : <DashboardPage page={activePage} data={data} selectedScenarioId={selectedScenarioId} onSelectScenario={setSelectedScenarioId} />}
      </section>
    </main>
  );
}

function DemoBanner() {
  return (
    <section className="demo-banner" aria-label="Demo environment notice">
      <strong>AI1SAD Demo Environment</strong>
      <span>Outputs are local operational intelligence examples, not beach closure or personal safety directives.</span>
    </section>
  );
}

function DashboardPage({
  page,
  data,
  selectedScenarioId,
  onSelectScenario,
}: {
  page: PageId;
  data: DashboardData;
  selectedScenarioId: string;
  onSelectScenario: (scenarioId: string) => void;
}) {
  if (page === "map") return <LiveWarningMap data={data} selectedScenarioId={selectedScenarioId} onSelectScenario={onSelectScenario} />;
  if (page === "surveillance") return <SurveillanceView data={data} />;
  if (page === "replay") return <ReplayExplorer data={data} />;
  if (page === "packs") return <RegionalPackExplorer data={data} />;
  if (page === "alerts") return <AlertsView data={data} />;
  return <ProviderHealthView providers={data.providerHealth} />;
}

function LoadingPanel() {
  return (
    <section className="panel state-panel" aria-live="polite">
      <Activity size={22} aria-hidden="true" />
      <div>
        <h2>Loading AI1SAD demo outputs</h2>
        <p>Fetching the selected scenario, map layers, replay data, and provider health.</p>
      </div>
    </section>
  );
}

function ErrorPanel({ message }: { message: string }) {
  return (
    <section className="panel state-panel error-state" role="alert">
      <AlertTriangle size={22} aria-hidden="true" />
      <div>
        <h2>Demo data unavailable</h2>
        <p>{message}</p>
        <p>Check the FastAPI service or enable frontend mock mode for local visual QA.</p>
      </div>
    </section>
  );
}

function LiveWarningMap({ data, selectedScenarioId, onSelectScenario }: { data: DashboardData; selectedScenarioId: string; onSelectScenario: (scenarioId: string) => void }) {
  const [lon, lat] = data.warning.location.geo.coordinates;
  const primaryZone = data.surveillance.zones[0];

  return (
    <div className="stack">
      <OperationalMap data={data} selectedScenarioId={selectedScenarioId} onSelectScenario={onSelectScenario} />
      <section className="panel">
        <h2>Score Split</h2>
        <ScoreExplainer />
        <ScoreRow label="Warning" value={data.warning.warning_score} />
        <ScoreRow label="Surveillance" value={primaryZone.surveillance_priority_score} />
        <ScoreRow label="Activity Hazard" value={data.warning.activity_context_score} />
        <h3>Dominant Factors</h3>
        <FactorList factors={data.warning.dominant_factors} />
        <ExplanationPanel explanation={data.explanation} compact />
      </section>
      <section className="panel">
        <h2>Selected Query</h2>
        <div className="coordinate-strip inline-strip">
          <span>Lat {lat.toFixed(4)}</span>
          <span>Lon {lon.toFixed(4)}</span>
          <span>{primaryZone.recommended_pattern}</span>
        </div>
      </section>
    </div>
  );
}

function SurveillanceView({ data }: { data: DashboardData }) {
  return (
    <div className="stack">
      {data.surveillance.zones.map((zone) => {
        const [lon, lat] = zone.center.geo.coordinates;
        return (
          <section className="panel zone-card" key={zone.zone_id}>
            <div>
              <p className="eyebrow">{zone.recommended_pattern}</p>
              <h2>{zone.zone_id}</h2>
              <p>Lat {lat.toFixed(4)} / Lon {lon.toFixed(4)} / Radius {zone.radius_km} km</p>
            </div>
            <div className="score-cluster">
              <Metric label="Priority" value={zone.surveillance_priority_score} />
              <Metric label="Warning" value={zone.warning_score} />
              <Metric label="Activity" value={zone.activity_context_score} />
              <Metric label="Confidence" value={Math.round(zone.confidence * 100)} suffix="%" />
            </div>
            <FactorList factors={zone.dominant_factors} />
            <WhyThisZone explanation={data.explanation} />
          </section>
        );
      })}
      {!data.surveillance.zones.length ? <EmptyState title="No surveillance zones" body="The backend returned no zones for this scenario." /> : null}
    </div>
  );
}

function ReplayExplorer({ data }: { data: DashboardData }) {
  const replay = data.replay;
  return (
    <div className="grid two">
      <section className="panel">
        <p className="eyebrow">{replay.region}</p>
        <h2>{replay.label}</h2>
        <ComparisonBars incident={replay.incident_day} quiet={replay.quiet_day} />
      </section>
      <section className="panel">
        <h2>Confidence Decomposition</h2>
        {Object.entries(replay.confidence_decomposition).map(([key, value]) => (
          <Progress key={key} label={key.replaceAll("_", " ")} value={value * 100} suffix="%" />
        ))}
        <h3>Signal Decay Timeline</h3>
        <div className="timeline">
          {replay.signal_decay_timeline.map((item) => (
            <div key={`${item.signal_type}-${item.age_hours}`}>
              <span>{item.signal_type}</span>
              <strong>{Math.round(item.decay_weight * 100)}%</strong>
              <small>{item.age_hours}h old</small>
            </div>
          ))}
        </div>
        <ExplanationPanel explanation={data.explanation} />
      </section>
    </div>
  );
}

function RegionalPackExplorer({ data }: { data: DashboardData }) {
  return (
    <div className="grid three">
      <section className="panel wide">
        <h2>Active Pack Context</h2>
        <div className="notice">
          <strong>{data.surveillance.active_pack ?? data.warning.active_pack ?? "core"}</strong>
          <span>{data.surveillance.pack_notice ?? data.warning.pack_notice ?? "No higher-resolution pack notice for this mock query."}</span>
        </div>
        <div className="chip-row">
          {(data.surveillance.pack_features_used ?? data.warning.pack_features_used ?? []).map((feature) => (
            <span className="chip" key={feature}>{feature}</span>
          ))}
        </div>
      </section>
      {data.packs.map((pack) => (
        <section className="panel pack-card" key={pack.pack_id}>
          <p className="eyebrow">{pack.required_access_tier ?? "free"}</p>
          <h2>{pack.name}</h2>
          <p>{pack.covered_regions.join(", ")}</p>
          <div className="chip-row">
            {pack.dominant_species.map((species) => (
              <span className="chip" key={species}>{species}</span>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function AlertsView({ data }: { data: DashboardData }) {
  return (
    <div className="stack">
      {data.alerts.map((alert) => (
        <section className="panel alert-card" key={`${alert.alert_type}-${alert.title}`}>
          <div>
            <p className={`level ${alert.level}`}>{alert.level}</p>
            <h2>{alert.title}</h2>
            <p>{alert.summary}</p>
            <strong>{alert.recommended_action}</strong>
          </div>
          <div className="score-cluster">
            <Metric label="Confidence" value={Math.round(alert.confidence * 100)} suffix="%" />
            <Metric label="Expires" value={new Date(alert.expires_at).getHours()} suffix="h" />
          </div>
          {alert.explanation_summary ? (
            <p className="explain-text">{alert.explanation_summary.operational_interpretation}</p>
          ) : null}
        </section>
      ))}
      {!data.alerts.length ? <EmptyState title="No active alerts" body="No public operational alerts were returned for the current demo scenario." /> : null}
    </div>
  );
}

function ProviderHealthView({ providers }: { providers: ProviderHealth[] }) {
  return (
    <div className="grid three">
      {providers.map((provider) => (
        <section className="panel provider-card" key={provider.provider}>
          <p className={`level ${provider.status}`}>{provider.status}</p>
          <h2>{provider.provider}</h2>
          <p>{provider.last_success ? `Last success ${provider.last_success}` : "No recent live success timestamp"}</p>
          <Metric label="Records" value={provider.records_ingested ?? 0} />
        </section>
      ))}
      {!providers.length ? <EmptyState title="No provider health rows" body="Provider health did not return any adapters for this local run." /> : null}
      <section className="panel wide">
        <h2>Provider Freshness</h2>
        <FreshnessGrid explanation={mockSafeExplanation(providers)} />
      </section>
    </div>
  );
}

function ScoreExplainer() {
  return (
    <div className="score-explainer">
      <div>
        <strong>warning_score</strong>
        <span>General public-facing warning signal for the selected location.</span>
      </div>
      <div>
        <strong>activity_hazard_score</strong>
        <span>Activity, habitat, season, species, and exposure context used by the backend.</span>
      </div>
      <div>
        <strong>surveillance_priority_score</strong>
        <span>Operational priority for where to look next with patrol or drone coverage.</span>
      </div>
      <p>Low warning with high surveillance priority means the public warning can remain calm while operators still have a focused reason to observe a zone.</p>
    </div>
  );
}

function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <section className="panel state-panel empty-state">
      <div>
        <h2>{title}</h2>
        <p>{body}</p>
      </div>
    </section>
  );
}

function ExplanationPanel({ explanation, compact = false }: { explanation: ExplanationResponse; compact?: boolean }) {
  return (
    <section className={compact ? "explain-block compact" : "explain-block"}>
      <h3>Why This Output?</h3>
      <p className="explain-text">{explanation.operational_interpretation}</p>
      <div className="chip-row">
        <span className="chip">{explanation.recommended_surveillance_pattern_label ?? explanation.recommended_surveillance_pattern}</span>
        <span className="chip">Model {explanation.metadata.model_version}</span>
      </div>
      {!compact ? (
        <>
          <h3>Factor Contributions</h3>
          <FactorList factors={explanation.factor_contributions} />
          <ConfidenceView explanation={explanation} />
          <FreshnessGrid explanation={explanation} />
        </>
      ) : null}
    </section>
  );
}

function WhyThisZone({ explanation }: { explanation: ExplanationResponse }) {
  return (
    <div className="why-zone">
      <h3>Why This Zone?</h3>
      <p>{explanation.recommended_action}</p>
      <div className="factor-cards">
        {explanation.factor_contributions.slice(0, 3).map((factor) => (
          <div key={factor.factor}>
            <span>{factor.factor.replaceAll("_", " ")}</span>
            <strong>{factor.points ? `${Math.round(factor.points)} pts` : `${Math.round((factor.contribution ?? 0) * 100)}%`}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

function ConfidenceView({ explanation }: { explanation: ExplanationResponse }) {
  const confidence = Math.round((explanation.confidence_breakdown.overall_confidence ?? 0) * 100);
  return (
    <div>
      <h3>Confidence</h3>
      <Progress label={explanation.confidence_breakdown.confidence_band ?? "overall"} value={confidence} suffix="%" />
    </div>
  );
}

function FreshnessGrid({ explanation }: { explanation: ExplanationResponse }) {
  return (
    <div className="freshness-grid">
      {Object.entries(explanation.data_freshness).map(([source, info]) => (
        <div key={source}>
          <span>{source.replaceAll("_", " ")}</span>
          <strong>{info?.status ?? "unknown"}</strong>
        </div>
      ))}
    </div>
  );
}

function mockSafeExplanation(providers: ProviderHealth[]): ExplanationResponse {
  return {
    ...mockDashboardFallbackExplanation,
    data_freshness: Object.fromEntries(providers.map((provider) => [provider.provider, { status: provider.status, last_success: provider.last_success }])),
  };
}

const mockDashboardFallbackExplanation: ExplanationResponse = {
  output_type: "provider_health",
  location: { geo: { type: "Point", coordinates: [0, 0] } },
  warning_score: 0,
  activity_hazard_score: 0,
  surveillance_priority_score: 0,
  dominant_factors: [],
  factor_contributions: [],
  confidence_breakdown: { overall_confidence: 0.5, confidence_band: "limited" },
  data_freshness: {},
  missing_data_sources: [],
  regional_rules_triggered: [],
  suppression_reasons: [],
  operational_interpretation: "Provider freshness is displayed from backend health and explanation responses.",
  recommended_action: "Review stale or missing providers before interpreting operational scores.",
  recommended_surveillance_pattern: "low_priority_observation",
  metadata: { model_version: "0.11.0", scoring_revision: "phase-11-explainability", provider_stack_version: "phase-9-static-live-adapters", generated_at: "" },
  disclaimer: "",
};

function ScoreRow({ label, value }: { label: string; value: number }) {
  return <Progress label={label} value={value} />;
}

function Progress({ label, value, suffix = "" }: { label: string; value: number; suffix?: string }) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className="progress-row">
      <div>
        <span>{label}</span>
        <strong>{Math.round(value)}{suffix}</strong>
      </div>
      <div className="track">
        <i style={{ width: `${clamped}%` }} />
      </div>
    </div>
  );
}

function Metric({ label, value, suffix = "" }: { label: string; value: number; suffix?: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{Math.round(value)}{suffix}</strong>
    </div>
  );
}

function FactorList({ factors }: { factors: DominantFactor[] }) {
  return (
    <div className="factor-list">
      {factors.map((factor) => (
        <div key={`${factor.factor}-${factor.points ?? factor.contribution ?? ""}`}>
          <span>{factor.factor.replaceAll("_", " ")}</span>
          <strong>{factor.points ? `${factor.points} pts` : factor.contribution ? `${Math.round(factor.contribution * 100)}%` : "context"}</strong>
        </div>
      ))}
    </div>
  );
}

function ComparisonBars({ incident, quiet }: { incident: { warning_score: number; surveillance_priority_score: number; activity_hazard_score: number }; quiet: { warning_score: number; surveillance_priority_score: number; activity_hazard_score: number } }) {
  return (
    <div className="comparison">
      <Progress label="Incident warning" value={incident.warning_score} />
      <Progress label="Quiet warning" value={quiet.warning_score} />
      <Progress label="Incident surveillance" value={incident.surveillance_priority_score} />
      <Progress label="Quiet surveillance" value={quiet.surveillance_priority_score} />
      <Progress label="Incident activity" value={incident.activity_hazard_score} />
      <Progress label="Quiet activity" value={quiet.activity_hazard_score} />
    </div>
  );
}
