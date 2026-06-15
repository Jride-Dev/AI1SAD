import { AlertTriangle, CheckCircle2, RefreshCw, Send, ShieldCheck } from "lucide-react";
import type { FormEvent, ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";

import { getDroneConsoleData, getDroneMission, getDroneMissionObservations, submitDroneObservation } from "../api/client";
import type { DroneConsoleData, DroneConsoleMissionOption, DroneFeedItem, DroneObservation, DroneObservationPayload } from "../types";

export const OBSERVATION_TYPE_OPTIONS = [
  "SHARK_SIGHTING",
  "UNKNOWN_LARGE_MARINE_ANIMAL",
  "NO_SIGHTING_PATROL",
  "CARCASS",
  "BAITFISH_CONGREGATION",
  "MARINE_MAMMAL_ACTIVITY",
  "POOR_VISIBILITY",
  "SURF_LINE_ACTIVITY",
  "SWIMMER_DENSITY",
  "VESSEL_ACTIVITY",
  "OTHER",
] as const;

const PROVENANCE_OPTIONS = [
  "drone_operator_visual",
  "lifeguard_visual",
  "analyst_reviewed_visual",
  "official_agency_report",
  "project_owner_analyst_visual_assessment",
  "demo_fixture",
] as const;

const OBSERVER_ROLES = ["drone_operator", "lifeguard", "analyst", "coastal_observer", "agency_observer"] as const;

type ObservationFormState = {
  mission_id: string;
  observation_type: string;
  observed_at: string;
  latitude: string;
  longitude: string;
  observer_role: string;
  visual_confidence: string;
  provenance: string;
  estimated_size_m: string;
  estimated_count: string;
  species_guess: string;
  species_confidence: string;
  behavior_notes: string;
  visibility_notes: string;
  surf_zone_notes: string;
  media_reference: string;
  operator_notes: string;
  public_summary: string;
  public_visibility: boolean;
};

export function toApiObservationType(value: string): string {
  return {
    SHARK_SIGHTING: "shark_sighting",
    UNKNOWN_LARGE_MARINE_ANIMAL: "unknown_large_marine_animal",
    NO_SIGHTING_PATROL: "no_sighting_patrol_result",
    CARCASS: "carcass",
    BAITFISH_CONGREGATION: "baitfish_congregation",
    MARINE_MAMMAL_ACTIVITY: "marine_mammal_activity",
    POOR_VISIBILITY: "water_clarity_observation",
    SURF_LINE_ACTIVITY: "surf_line_activity",
    SWIMMER_DENSITY: "swimmer_density",
    VESSEL_ACTIVITY: "vessel_activity",
    OTHER: "other",
  }[value] ?? "other";
}

export function validateDroneObservationForm(form: ObservationFormState): string[] {
  const errors: string[] = [];
  const lat = Number(form.latitude);
  const lon = Number(form.longitude);
  const confidence = Number(form.visual_confidence);
  if (!form.mission_id.trim()) errors.push("Mission is required.");
  if (!form.observation_type.trim()) errors.push("Observation type is required.");
  if (!form.observed_at.trim() || Number.isNaN(Date.parse(form.observed_at))) errors.push("Observed time must be a valid timestamp.");
  if (!Number.isFinite(lat) || lat < -90 || lat > 90) errors.push("Latitude must be between -90 and 90.");
  if (!Number.isFinite(lon) || lon < -180 || lon > 180) errors.push("Longitude must be between -180 and 180.");
  if (!form.observer_role.trim()) errors.push("Observer role is required.");
  if (!Number.isFinite(confidence) || confidence < 0 || confidence > 1) errors.push("Visual confidence must be between 0 and 1.");
  if (!form.provenance.trim()) errors.push("Provenance is required.");
  if (form.species_confidence && (Number(form.species_confidence) < 0 || Number(form.species_confidence) > 1)) errors.push("Species confidence must be between 0 and 1.");
  if (form.estimated_size_m && Number(form.estimated_size_m) <= 0) errors.push("Estimated size must be greater than 0 when provided.");
  if (form.estimated_count && Number(form.estimated_count) < 0) errors.push("Estimated count cannot be negative.");
  return errors;
}

export function buildDroneObservationPayload(form: ObservationFormState): DroneObservationPayload {
  const observationType = toApiObservationType(form.observation_type);
  const notes = [
    form.public_summary ? `Public summary: ${form.public_summary}` : "",
    form.visibility_notes ? `Visibility: ${form.visibility_notes}` : "",
    form.surf_zone_notes ? `Surf zone: ${form.surf_zone_notes}` : "",
  ]
    .filter(Boolean)
    .join(" | ");
  const count = observationType === "no_sighting_patrol_result" ? 0 : optionalNumber(form.estimated_count);
  return removeUndefined({
    timestamp: new Date(form.observed_at).toISOString(),
    latitude: Number(form.latitude),
    longitude: Number(form.longitude),
    observation_type: observationType,
    count,
    estimated_length_m: optionalNumber(form.estimated_size_m),
    probable_species: form.species_guess.trim() || undefined,
    species_assessment_source: form.species_guess.trim() ? "operator_visual_assessment" : undefined,
    species_confidence: optionalNumber(form.species_confidence),
    observed_behavior: form.behavior_notes.trim() || undefined,
    behavior_source: form.behavior_notes.trim() ? form.provenance : undefined,
    evidence_type: form.media_reference.trim() ? "media_reference" : "visual_observation",
    media_reference: form.media_reference.trim() || undefined,
    analyst_notes: notes || undefined,
    internal_notes: form.operator_notes.trim() || undefined,
    confidence: Number(form.visual_confidence),
    review_status: "operator_reviewed",
    source: form.provenance,
    source_type: form.observer_role,
    public_visibility: form.public_visibility,
  });
}

function optionalNumber(value: string): number | undefined {
  if (!value.trim()) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function removeUndefined<T extends Record<string, unknown>>(value: T): T {
  return Object.fromEntries(Object.entries(value).filter(([, item]) => item !== undefined)) as T;
}

function defaultObservedAt(): string {
  return new Date(Date.now() - new Date().getTimezoneOffset() * 60_000).toISOString().slice(0, 16);
}

function initialForm(mission?: DroneConsoleMissionOption): ObservationFormState {
  const telemetry = mission?.latestTelemetry;
  return {
    mission_id: mission?.mission.mission_id ?? "",
    observation_type: "NO_SIGHTING_PATROL",
    observed_at: defaultObservedAt(),
    latitude: telemetry?.latitude !== undefined ? String(telemetry.latitude) : "",
    longitude: telemetry?.longitude !== undefined ? String(telemetry.longitude) : "",
    observer_role: "drone_operator",
    visual_confidence: "0.6",
    provenance: "drone_operator_visual",
    estimated_size_m: "",
    estimated_count: "",
    species_guess: "",
    species_confidence: "",
    behavior_notes: "",
    visibility_notes: "",
    surf_zone_notes: "",
    media_reference: "",
    operator_notes: "",
    public_summary: "",
    public_visibility: true,
  };
}

export function DroneOperatorConsole({ initialData = null }: { initialData?: DroneConsoleData | null }) {
  const initialMission = initialData?.missions[0];
  const [consoleData, setConsoleData] = useState<DroneConsoleData | null>(initialData);
  const [selectedMissionId, setSelectedMissionId] = useState(initialMission?.mission.mission_id ?? "");
  const [manualMissionId, setManualMissionId] = useState(initialMission?.mission.mission_id ?? "");
  const [form, setForm] = useState<ObservationFormState>(() => initialForm(initialMission));
  const [loading, setLoading] = useState(!initialData);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitMessage, setSubmitMessage] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  const loadConsole = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await getDroneConsoleData();
      setConsoleData(payload);
      const mission = payload.missions[0];
      setSelectedMissionId(mission?.mission.mission_id ?? "");
      setManualMissionId(mission?.mission.mission_id ?? "");
      setForm(initialForm(mission));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Drone console data could not be loaded.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialData) return;
    void loadConsole();
  }, [initialData]);

  const selectedMission = useMemo(
    () => consoleData?.missions.find((item) => item.mission.mission_id === selectedMissionId) ?? null,
    [consoleData, selectedMissionId],
  );
  const recentItems = useMemo(
    () => (consoleData?.feed.results ?? []).filter((item) => !selectedMissionId || item.mission_id === selectedMissionId),
    [consoleData, selectedMissionId],
  );
  const missionObservations = useMemo(
    () => (consoleData?.observations ?? []).filter((item) => !selectedMissionId || item.mission_id === selectedMissionId),
    [consoleData, selectedMissionId],
  );

  const updateField = (field: keyof ObservationFormState, value: string | boolean) => {
    setForm((current) => ({ ...current, [field]: value }));
    setSubmitMessage(null);
    setValidationErrors([]);
  };

  const chooseMission = (missionId: string) => {
    const mission = consoleData?.missions.find((item) => item.mission.mission_id === missionId);
    setSelectedMissionId(missionId);
    setManualMissionId(missionId);
    setForm((current) => ({ ...initialForm(mission ?? undefined), ...current, mission_id: missionId }));
  };

  const fetchManualMission = async () => {
    if (!manualMissionId.trim()) {
      setValidationErrors(["Mission ID is required before fetching live mission detail."]);
      return;
    }
    setError(null);
    try {
      const mission = await getDroneMission(manualMissionId.trim());
      const observations = await getDroneMissionObservations(mission.mission.mission_id);
      setConsoleData((current) => {
        const base = current ?? { missions: [], observations: [], feed: { results: [] }, data_source: "live" as const };
        const missions = [mission, ...base.missions.filter((item) => item.mission.mission_id !== mission.mission.mission_id)];
        const retainedObservations = base.observations.filter((item) => item.mission_id !== mission.mission.mission_id);
        return { ...base, missions, observations: [...observations, ...retainedObservations] };
      });
      chooseMission(mission.mission.mission_id);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Mission detail could not be loaded.");
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const errors = validateDroneObservationForm(form);
    setValidationErrors(errors);
    setSubmitMessage(null);
    if (errors.length) return;

    setSubmitting(true);
    setError(null);
    try {
      const created = await submitDroneObservation(form.mission_id, buildDroneObservationPayload(form));
      setSubmitMessage(`Observation recorded for ${created.mission_id}.`);
      setConsoleData((current) => {
        if (!current) return current;
        const updatedFeedItem = observationToFeedItem(created);
        return {
          ...current,
          observations: [created, ...current.observations],
          feed: { ...current.feed, results: [updatedFeedItem, ...current.feed.results] },
        };
      });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Observation could not be submitted.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <section className="panel state-panel">
        <RefreshCw size={22} aria-hidden="true" />
        <div>
          <h2>Loading Drone Operator Console</h2>
          <p>Fetching mission context, active observations, and map-ready surveillance feed.</p>
        </div>
      </section>
    );
  }

  return (
    <div className="stack drone-console">
      <section className="panel drone-console-hero">
        <div>
          <p className="eyebrow">Human Observation Intake</p>
          <h2>Drone Operator Console</h2>
          <p>AI1SAD records human observations and recommends surveillance attention. It does not control aircraft or predict individual shark attacks.</p>
        </div>
        <div className="safety-badges">
          <span><ShieldCheck size={16} aria-hidden="true" /> Human-entered observations</span>
          <span>No autonomous flight control</span>
          <span>{consoleData?.data_source === "mock" ? "Mock demo data" : "Live backend data"}</span>
        </div>
      </section>

      {error ? (
        <section className="panel state-panel error-state" role="alert">
          <AlertTriangle size={22} aria-hidden="true" />
          <div>
            <h2>Drone console backend unavailable</h2>
            <p>{error}</p>
            <p>Live mode fails closed. Enable mock mode only when intentionally reviewing demo fixtures.</p>
          </div>
        </section>
      ) : null}

      <section className="grid two drone-console-grid">
        <MissionPanel
          missions={consoleData?.missions ?? []}
          selectedMission={selectedMission}
          selectedMissionId={selectedMissionId}
          manualMissionId={manualMissionId}
          onSelectMission={chooseMission}
          onManualMissionId={setManualMissionId}
          onFetchMission={fetchManualMission}
        />

        <section className="panel safety-copy">
          <h2>Safety Boundaries</h2>
          <p>Observations are human-entered. AI1SAD recommends missions; humans approve missions; drone operators fly missions; AI1SAD ingests observations.</p>
          <p>No-sighting patrols reduce uncertainty only within the observed patrol area, time window, and visibility conditions. They do not prove an area is safe.</p>
          <p>Species guesses are provisional unless confirmed by an official source or qualified review.</p>
        </section>
      </section>

      <form className="panel drone-form" onSubmit={handleSubmit}>
        <div className="form-heading">
          <div>
            <p className="eyebrow">Observation form</p>
            <h2>Record Patrol Observation</h2>
          </div>
          <button type="submit" disabled={submitting}>
            <Send size={16} aria-hidden="true" />
            {submitting ? "Submitting" : "Submit Observation"}
          </button>
        </div>

        {validationErrors.length ? (
          <div className="validation-box" role="alert">
            {validationErrors.map((item) => (
              <p key={item}>{item}</p>
            ))}
          </div>
        ) : null}
        {submitMessage ? (
          <div className="success-box" role="status">
            <CheckCircle2 size={16} aria-hidden="true" />
            <span>{submitMessage}</span>
          </div>
        ) : null}

        <div className="form-grid">
          <Field label="Mission ID" required>
            <input value={form.mission_id} onChange={(event) => updateField("mission_id", event.target.value)} />
          </Field>
          <Field label="Observation Type" required>
            <select value={form.observation_type} onChange={(event) => updateField("observation_type", event.target.value)}>
              {OBSERVATION_TYPE_OPTIONS.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </Field>
          <Field label="Observed At" required>
            <input type="datetime-local" value={form.observed_at} onChange={(event) => updateField("observed_at", event.target.value)} />
          </Field>
          <Field label="Latitude" required>
            <input inputMode="decimal" value={form.latitude} onChange={(event) => updateField("latitude", event.target.value)} />
          </Field>
          <Field label="Longitude" required>
            <input inputMode="decimal" value={form.longitude} onChange={(event) => updateField("longitude", event.target.value)} />
          </Field>
          <Field label="Observer Role" required>
            <select value={form.observer_role} onChange={(event) => updateField("observer_role", event.target.value)}>
              {OBSERVER_ROLES.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </Field>
          <Field label="Visual Confidence" required>
            <input type="number" min="0" max="1" step="0.05" value={form.visual_confidence} onChange={(event) => updateField("visual_confidence", event.target.value)} />
          </Field>
          <Field label="Provenance" required>
            <select value={form.provenance} onChange={(event) => updateField("provenance", event.target.value)}>
              {PROVENANCE_OPTIONS.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </Field>
          <Field label="Estimated Size (m)">
            <input inputMode="decimal" value={form.estimated_size_m} onChange={(event) => updateField("estimated_size_m", event.target.value)} />
          </Field>
          <Field label="Estimated Count">
            <input inputMode="numeric" value={form.estimated_count} onChange={(event) => updateField("estimated_count", event.target.value)} />
          </Field>
          <Field label="Species Guess">
            <input value={form.species_guess} onChange={(event) => updateField("species_guess", event.target.value)} placeholder="Provisional only" />
          </Field>
          <Field label="Species Confidence">
            <input type="number" min="0" max="1" step="0.05" value={form.species_confidence} onChange={(event) => updateField("species_confidence", event.target.value)} />
          </Field>
        </div>

        <div className="form-grid notes-grid">
          <Field label="Behavior Notes">
            <textarea value={form.behavior_notes} onChange={(event) => updateField("behavior_notes", event.target.value)} />
          </Field>
          <Field label="Visibility Notes">
            <textarea value={form.visibility_notes} onChange={(event) => updateField("visibility_notes", event.target.value)} />
          </Field>
          <Field label="Surf Zone Notes">
            <textarea value={form.surf_zone_notes} onChange={(event) => updateField("surf_zone_notes", event.target.value)} />
          </Field>
          <Field label="Media Reference">
            <input value={form.media_reference} onChange={(event) => updateField("media_reference", event.target.value)} placeholder="Reference only; no upload in Phase 25C" />
          </Field>
          <Field label="Operator Notes">
            <textarea value={form.operator_notes} onChange={(event) => updateField("operator_notes", event.target.value)} />
          </Field>
          <Field label="Public Summary">
            <textarea value={form.public_summary} onChange={(event) => updateField("public_summary", event.target.value)} />
          </Field>
        </div>

        <label className="checkbox-field">
          <input type="checkbox" checked={form.public_visibility} onChange={(event) => updateField("public_visibility", event.target.checked)} />
          <span>Public-safe observation. Internal/operator notes remain filtered from public feed output.</span>
        </label>
      </form>

      <RecentObservationsPanel items={recentItems} observations={missionObservations} />
    </div>
  );
}

function MissionPanel({
  missions,
  selectedMission,
  selectedMissionId,
  manualMissionId,
  onSelectMission,
  onManualMissionId,
  onFetchMission,
}: {
  missions: DroneConsoleMissionOption[];
  selectedMission: DroneConsoleMissionOption | null;
  selectedMissionId: string;
  manualMissionId: string;
  onSelectMission: (missionId: string) => void;
  onManualMissionId: (missionId: string) => void;
  onFetchMission: () => void;
}) {
  const mission = selectedMission?.mission;
  const telemetry = selectedMission?.latestTelemetry;
  return (
    <section className="panel mission-panel">
      <h2>Mission Selector</h2>
      {missions.length ? (
        <label>
          Active mission
          <select value={selectedMissionId} onChange={(event) => onSelectMission(event.target.value)}>
            {missions.map((item) => (
              <option key={item.mission.mission_id} value={item.mission.mission_id}>
                {item.mission.mission_id}
              </option>
            ))}
          </select>
        </label>
      ) : (
        <p className="explain-text">No active mission choices were returned by the public feed. Enter a known mission ID to fetch it from the backend.</p>
      )}
      <div className="manual-mission-row">
        <input value={manualMissionId} onChange={(event) => onManualMissionId(event.target.value)} placeholder="Known mission ID" />
        <button type="button" onClick={onFetchMission}>Fetch</button>
      </div>
      {mission ? (
        <div className="freshness-grid mission-facts">
          <div><span>Mission ID</span><strong>{mission.mission_id}</strong></div>
          <div><span>Drone ID</span><strong>{mission.drone_id}</strong></div>
          <div><span>Status</span><strong>{mission.status ?? "unknown"}</strong></div>
          <div><span>Pattern</span><strong>{mission.recommended_pattern ?? mission.mission_type ?? "manual_observation_patrol"}</strong></div>
        </div>
      ) : null}
      <h3>Latest Telemetry Summary</h3>
      {telemetry ? (
        <div className="freshness-grid mission-facts">
          <div><span>Timestamp</span><strong>{telemetry.timestamp ?? "unknown"}</strong></div>
          <div><span>Position</span><strong>{formatCoord(telemetry.latitude, telemetry.longitude)}</strong></div>
          <div><span>Altitude</span><strong>{telemetry.altitude_m ?? "n/a"} m</strong></div>
          <div><span>Battery</span><strong>{telemetry.battery_percent ?? "n/a"}%</strong></div>
        </div>
      ) : (
        <p className="explain-text">Latest telemetry is unavailable from the current public API for this mission. Read-only bridge telemetry remains context and never creates a sighting by itself.</p>
      )}
    </section>
  );
}

function Field({ label, required = false, children }: { label: string; required?: boolean; children: ReactNode }) {
  return (
    <label>
      <span>{label}{required ? " *" : ""}</span>
      {children}
    </label>
  );
}

function RecentObservationsPanel({ items, observations }: { items: DroneFeedItem[]; observations: DroneObservation[] }) {
  return (
    <section className="panel recent-observations">
      <div className="form-heading">
        <div>
          <p className="eyebrow">Map-ready feed</p>
          <h2>Recent Observations</h2>
        </div>
        <span className="status-pill">{items.length} feed items</span>
      </div>
      <div className="observation-list">
        {items.map((item) => {
          const observation = observations.find((candidate) => candidate.timestamp === item.timestamp && candidate.mission_id === item.mission_id);
          const visibility = observation?.visibility ?? (observation?.public_visibility === false ? "private" : "public");
          return (
            <article key={`${item.mission_id}-${item.timestamp}-${item.observation_type}`}>
              <div>
                <strong>{item.observation_type.replaceAll("_", " ")}</strong>
                <span>{item.timestamp}</span>
              </div>
              <div className="coordinate-strip inline-strip">
                <span>{formatCoord(item.latitude, item.longitude)}</span>
                <span>Confidence {Math.round(item.confidence * 100)}%</span>
                <span>{visibility}</span>
                <span>{observation?.source ?? item.source_type}</span>
              </div>
              {item.explanation_summary ? <p>{item.explanation_summary}</p> : null}
            </article>
          );
        })}
      </div>
      {!items.length ? <p className="explain-text">No recent observations are available for this mission.</p> : null}
    </section>
  );
}

function observationToFeedItem(observation: DroneObservation): DroneFeedItem {
  return {
    latitude: observation.latitude,
    longitude: observation.longitude,
    timestamp: observation.timestamp,
    observation_type: observation.observation_type,
    review_status: observation.review_status,
    confidence: observation.confidence,
    mission_id: observation.mission_id,
    source_type: observation.source_type,
    active_pack: observation.active_pack,
    recommended_surveillance_pattern: observation.recommended_surveillance_pattern,
    explanation_summary:
      observation.observation_type === "no_sighting_patrol_result"
        ? "No-sighting patrol result reduces uncertainty only inside documented coverage and time window."
        : `Drone ${observation.observation_type} report is source-attributed and review status is ${observation.review_status}.`,
  };
}

function formatCoord(lat?: number, lon?: number): string {
  if (lat === undefined || lon === undefined) return "Position unavailable";
  return `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
}
