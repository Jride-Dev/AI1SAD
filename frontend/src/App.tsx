import { Activity, AlertTriangle, Boxes, HeartPulse, Map, Plane, Radar, RotateCcw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { getDashboardData } from "./api/client";
import type { DashboardData, DominantFactor, ProviderHealth } from "./types";

const pages = [
  { id: "map", label: "Live Warning Map", icon: Map },
  { id: "surveillance", label: "Surveillance Priority", icon: Plane },
  { id: "replay", label: "Replay Explorer", icon: RotateCcw },
  { id: "packs", label: "Regional Packs", icon: Boxes },
  { id: "alerts", label: "Alerts", icon: AlertTriangle },
  { id: "health", label: "Provider Health", icon: HeartPulse },
] as const;

type PageId = (typeof pages)[number]["id"];

const target = { lat: -31.983, lon: 115.515 };

export default function App() {
  const [activePage, setActivePage] = useState<PageId>("map");
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardData(target).then((payload) => {
      setData(payload);
      setLoading(false);
    });
  }, []);

  const page = useMemo(() => pages.find((item) => item.id === activePage) ?? pages[0], [activePage]);

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <Radar size={26} aria-hidden="true" />
          <div>
            <strong>AI1SAD</strong>
            <span>Encounter warning ops</span>
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
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Mock mode dashboard shell</p>
            <h1>{page.label}</h1>
          </div>
          <div className="status-pill">
            <Activity size={16} aria-hidden="true" />
            Existing API outputs only
          </div>
        </header>

        {loading || !data ? <LoadingPanel /> : <DashboardPage page={activePage} data={data} />}
      </section>
    </main>
  );
}

function DashboardPage({ page, data }: { page: PageId; data: DashboardData }) {
  if (page === "map") return <LiveWarningMap data={data} />;
  if (page === "surveillance") return <SurveillanceView data={data} />;
  if (page === "replay") return <ReplayExplorer data={data} />;
  if (page === "packs") return <RegionalPackExplorer data={data} />;
  if (page === "alerts") return <AlertsView data={data} />;
  return <ProviderHealthView providers={data.providerHealth} />;
}

function LoadingPanel() {
  return <section className="panel loading">Loading dashboard outputs...</section>;
}

function LiveWarningMap({ data }: { data: DashboardData }) {
  const [lon, lat] = data.warning.location.geo.coordinates;
  const primaryZone = data.surveillance.zones[0];

  return (
    <div className="grid two">
      <section className="map-panel">
        <div className="map-canvas">
          <div className="map-grid" />
          <div className="zone zone-primary" />
          <div className="zone zone-secondary" />
          <div className="pin" />
        </div>
        <div className="coordinate-strip">
          <span>Lat {lat.toFixed(4)}</span>
          <span>Lon {lon.toFixed(4)}</span>
          <span>{primaryZone.recommended_pattern}</span>
        </div>
      </section>
      <section className="panel">
        <h2>Score Split</h2>
        <ScoreRow label="Warning" value={data.warning.warning_score} />
        <ScoreRow label="Surveillance" value={primaryZone.surveillance_priority_score} />
        <ScoreRow label="Activity Hazard" value={data.warning.activity_context_score} />
        <h3>Dominant Factors</h3>
        <FactorList factors={data.warning.dominant_factors} />
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
          </section>
        );
      })}
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
        </section>
      ))}
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
    </div>
  );
}

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
