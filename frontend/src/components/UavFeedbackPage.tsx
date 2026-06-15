import { CheckCircle2, Send } from "lucide-react";
import type { FormEvent } from "react";
import { useState } from "react";

import { submitUavOperatorFeedback } from "../api/client";
import {
  UAV_MEDIA_WORKFLOWS,
  UAV_ORGANIZATION_TYPES,
  UAV_SUBMITTER_ROLES,
  UAV_TELEMETRY_OPTIONS,
} from "../types";
import type { UavOperatorFeedback, UavOperatorFeedbackPayload } from "../types";

type UavFeedbackFormState = {
  submitter_role: string;
  organization_type: string;
  region: string;
  country: string;
  contact_allowed: boolean;
  contact_reference: string;
  drone_platform: string;
  drone_model: string;
  flight_app: string;
  telemetry_available: string;
  telemetry_export_format: string;
  media_workflow: string;
  no_sighting_patrols_logged: boolean;
  observation_fields_used: string;
  privacy_constraints: string;
  controlled_airspace_notes: string;
  operator_pain_points: string;
  requested_features: string;
  suggested_observation_types: string;
  workflow_notes: string;
  public_summary: string;
  internal_notes_private: string;
  requirements_tags: string;
};

const SECRET_PATTERN = /(sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|(?:api[_-]?key|secret|token)\s*[:=]\s*[A-Za-z0-9_.-]{12,})/i;
const CONTACT_PATTERN = /([\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\+?\d[\d .()/-]{7,}\d)/;

function initialForm(): UavFeedbackFormState {
  return {
    submitter_role: "uav_operator",
    organization_type: "unknown",
    region: "",
    country: "",
    contact_allowed: false,
    contact_reference: "",
    drone_platform: "",
    drone_model: "",
    flight_app: "",
    telemetry_available: "unknown",
    telemetry_export_format: "",
    media_workflow: "unknown",
    no_sighting_patrols_logged: false,
    observation_fields_used: "",
    privacy_constraints: "",
    controlled_airspace_notes: "",
    operator_pain_points: "",
    requested_features: "",
    suggested_observation_types: "",
    workflow_notes: "",
    public_summary: "",
    internal_notes_private: "",
    requirements_tags: "",
  };
}

function listFromText(value: string): string[] {
  return value
    .split(/\r?\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function optionalText(value: string): string | undefined {
  const text = value.trim();
  return text || undefined;
}

export function buildUavFeedbackPayload(form: UavFeedbackFormState): UavOperatorFeedbackPayload {
  return {
    submitter_role: form.submitter_role,
    organization_type: form.organization_type,
    region: optionalText(form.region),
    country: optionalText(form.country),
    contact_allowed: form.contact_allowed,
    contact_reference: optionalText(form.contact_reference),
    drone_platform: optionalText(form.drone_platform),
    drone_model: optionalText(form.drone_model),
    flight_app: optionalText(form.flight_app),
    telemetry_available: form.telemetry_available,
    telemetry_export_format: optionalText(form.telemetry_export_format),
    media_workflow: form.media_workflow,
    no_sighting_patrols_logged: form.no_sighting_patrols_logged,
    observation_fields_used: listFromText(form.observation_fields_used),
    privacy_constraints: listFromText(form.privacy_constraints),
    controlled_airspace_notes: optionalText(form.controlled_airspace_notes),
    operator_pain_points: listFromText(form.operator_pain_points),
    requested_features: listFromText(form.requested_features),
    suggested_observation_types: listFromText(form.suggested_observation_types),
    workflow_notes: optionalText(form.workflow_notes),
    public_summary: optionalText(form.public_summary),
    internal_notes_private: optionalText(form.internal_notes_private),
    requirements_tags: listFromText(form.requirements_tags),
  };
}

export function validateUavFeedbackForm(form: UavFeedbackFormState): string[] {
  const errors: string[] = [];
  if (!UAV_SUBMITTER_ROLES.includes(form.submitter_role as (typeof UAV_SUBMITTER_ROLES)[number])) errors.push("Submitter role is not supported.");
  if (!UAV_ORGANIZATION_TYPES.includes(form.organization_type as (typeof UAV_ORGANIZATION_TYPES)[number])) errors.push("Organization type is not supported.");
  if (!UAV_TELEMETRY_OPTIONS.includes(form.telemetry_available as (typeof UAV_TELEMETRY_OPTIONS)[number])) errors.push("Telemetry availability is not supported.");
  if (!UAV_MEDIA_WORKFLOWS.includes(form.media_workflow as (typeof UAV_MEDIA_WORKFLOWS)[number])) errors.push("Media workflow is not supported.");
  if (form.region.length > 120) errors.push("Region must be 120 characters or fewer.");
  if (form.country.length > 80) errors.push("Country must be 80 characters or fewer.");
  if (form.contact_reference.length > 240) errors.push("Contact reference must be 240 characters or fewer.");
  if (/^(http:\/\/|javascript:|data:|file:|ftp:)/i.test(form.contact_reference.trim())) errors.push("Contact reference must not use unsafe URL schemes.");
  if (form.workflow_notes.length > 1200) errors.push("Workflow notes must be 1200 characters or fewer.");
  if (form.internal_notes_private.length > 1200) errors.push("Private notes must be 1200 characters or fewer.");
  if (form.public_summary.length > 500) errors.push("Public summary must be 500 characters or fewer.");
  if (CONTACT_PATTERN.test(form.public_summary)) errors.push("Public summary must not include contact details.");
  if (SECRET_PATTERN.test(JSON.stringify(form))) errors.push("Feedback must not include API keys, tokens, or secrets.");
  return errors;
}

export function UavFeedbackPage({ initialError = null }: { initialError?: string | null }) {
  const [form, setForm] = useState<UavFeedbackFormState>(() => initialForm());
  const [errors, setErrors] = useState<string[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [backendError, setBackendError] = useState<string | null>(initialError);
  const [lastFeedback, setLastFeedback] = useState<UavOperatorFeedback | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const updateField = (field: keyof UavFeedbackFormState, value: string | boolean) => {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors([]);
    setBackendError(null);
    setMessage(null);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextErrors = validateUavFeedbackForm(form);
    if (nextErrors.length) {
      setErrors(nextErrors);
      return;
    }
    setSubmitting(true);
    setBackendError(null);
    setMessage(null);
    try {
      const created = await submitUavOperatorFeedback(buildUavFeedbackPayload(form));
      setLastFeedback(created);
      setMessage("Feedback recorded as research input.");
      setForm(initialForm());
    } catch (reason) {
      setBackendError(reason instanceof Error ? reason.message : "UAV feedback backend unavailable.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="stack drone-console">
      <section className="panel drone-console-hero">
        <p className="eyebrow">UAV Feedback</p>
        <h2>Operator Feedback Intake</h2>
        <p>Feedback records are research inputs, not live surveillance observations.</p>
        <p>Submitting feedback does not create a sighting, warning, or public alert.</p>
        <p>Contact details are optional and private by default.</p>
      </section>

      {errors.length ? (
        <section className="validation-box" role="alert">
          {errors.map((item) => <p key={item}>{item}</p>)}
        </section>
      ) : null}
      {backendError ? (
        <section className="validation-box" role="alert">
          <p>UAV feedback backend unavailable.</p>
          <p>{backendError}</p>
        </section>
      ) : null}
      {message ? (
        <section className="success-box" role="status">
          <CheckCircle2 size={16} aria-hidden="true" />
          <span>{message}</span>
        </section>
      ) : null}

      <section className="panel">
        <form className="analyst-review-form attachment-form" onSubmit={handleSubmit}>
          <label>
            Submitter Role
            <select value={form.submitter_role} onChange={(event) => updateField("submitter_role", event.target.value)}>
              {UAV_SUBMITTER_ROLES.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>
          <label>
            Organization Type
            <select value={form.organization_type} onChange={(event) => updateField("organization_type", event.target.value)}>
              {UAV_ORGANIZATION_TYPES.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>
          <label>
            Region
            <input value={form.region} onChange={(event) => updateField("region", event.target.value)} placeholder="Coastal region or patrol area" />
          </label>
          <label>
            Country
            <input value={form.country} onChange={(event) => updateField("country", event.target.value)} placeholder="Country" />
          </label>
          <label>
            Drone Platform
            <input value={form.drone_platform} onChange={(event) => updateField("drone_platform", event.target.value)} placeholder="Consumer quadcopter, agency drone, helicopter report" />
          </label>
          <label>
            Drone Model
            <input value={form.drone_model} onChange={(event) => updateField("drone_model", event.target.value)} placeholder="Optional model/platform description" />
          </label>
          <label>
            Flight App
            <input value={form.flight_app} onChange={(event) => updateField("flight_app", event.target.value)} placeholder="App or workflow used by the operator" />
          </label>
          <label>
            Telemetry Available
            <select value={form.telemetry_available} onChange={(event) => updateField("telemetry_available", event.target.value)}>
              {UAV_TELEMETRY_OPTIONS.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>
          <label>
            Telemetry Export Format
            <input value={form.telemetry_export_format} onChange={(event) => updateField("telemetry_export_format", event.target.value)} placeholder="CSV, JSON, KML, app-only, none" />
          </label>
          <label>
            Media Workflow
            <select value={form.media_workflow} onChange={(event) => updateField("media_workflow", event.target.value)}>
              {UAV_MEDIA_WORKFLOWS.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>
          <label>
            <input type="checkbox" checked={form.no_sighting_patrols_logged} onChange={(event) => updateField("no_sighting_patrols_logged", event.target.checked)} />
            No-sighting patrols are logged today
          </label>
          <label>
            <input type="checkbox" checked={form.contact_allowed} onChange={(event) => updateField("contact_allowed", event.target.checked)} />
            Contact allowed for follow-up
          </label>
          <label>
            Private Contact Reference
            <input value={form.contact_reference} onChange={(event) => updateField("contact_reference", event.target.value)} placeholder="Optional; private by default" />
          </label>
          <label>
            Observation Fields Used
            <textarea value={form.observation_fields_used} onChange={(event) => updateField("observation_fields_used", event.target.value)} placeholder="Comma-separated or one per line" />
          </label>
          <label>
            Privacy Constraints
            <textarea value={form.privacy_constraints} onChange={(event) => updateField("privacy_constraints", event.target.value)} placeholder="Agency, operator, media, or location restrictions" />
          </label>
          <label>
            Controlled-Airspace Notes
            <textarea value={form.controlled_airspace_notes} onChange={(event) => updateField("controlled_airspace_notes", event.target.value)} placeholder="Airport or authorization constraints" />
          </label>
          <label>
            Pain Points
            <textarea value={form.operator_pain_points} onChange={(event) => updateField("operator_pain_points", event.target.value)} placeholder="Workflow problems to track as requirements" />
          </label>
          <label>
            Requested Features
            <textarea value={form.requested_features} onChange={(event) => updateField("requested_features", event.target.value)} placeholder="Features operators want AI1SAD to consider" />
          </label>
          <label>
            Suggested Observation Types
            <textarea value={form.suggested_observation_types} onChange={(event) => updateField("suggested_observation_types", event.target.value)} placeholder="Potential future observation categories" />
          </label>
          <label>
            Workflow Notes
            <textarea value={form.workflow_notes} onChange={(event) => updateField("workflow_notes", event.target.value)} placeholder="Research notes only; not live surveillance data" />
          </label>
          <label>
            Public Summary
            <textarea value={form.public_summary} onChange={(event) => updateField("public_summary", event.target.value)} placeholder="Public-safe summary; no contact details or private identifiers" />
          </label>
          <label>
            Private Internal Notes
            <textarea value={form.internal_notes_private} onChange={(event) => updateField("internal_notes_private", event.target.value)} placeholder="Private by default; not public output" />
          </label>
          <label>
            Requirements Tags
            <input value={form.requirements_tags} onChange={(event) => updateField("requirements_tags", event.target.value)} placeholder="uav_workflow, privacy, telemetry" />
          </label>
          <button type="submit" disabled={submitting}>
            <Send size={16} aria-hidden="true" />
            {submitting ? "Submitting" : "Submit Feedback"}
          </button>
        </form>
      </section>

      {lastFeedback ? (
        <section className="panel">
          <p className="eyebrow">Recorded</p>
          <h2>{lastFeedback.feedback_id}</h2>
          <div className="inline-strip coordinate-strip">
            <span>{lastFeedback.review_status}</span>
            <span>{lastFeedback.research_input_only ? "research input only" : "unexpected live data"}</span>
            <span>{lastFeedback.creates_sighting ? "creates sighting" : "no sighting created"}</span>
            <span>{lastFeedback.creates_public_alert ? "creates alert" : "no public alert"}</span>
          </div>
          <p className="explain-text">{lastFeedback.public_summary ?? "No public summary supplied."}</p>
        </section>
      ) : null}
    </div>
  );
}
