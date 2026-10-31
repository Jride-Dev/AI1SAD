import {
  CircleDot,
  ExternalLink,
  HeartPulse,
  ImageOff,
  ListFilter,
  LocateFixed,
  MapPinOff,
  Minus,
  Plus,
  RotateCcw,
  Search,
  ShieldCheck,
  Skull,
  X,
} from "lucide-react";
import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react";
import * as THREE from "three";

import { getIncidentGlobe } from "../api/client";
import type { GlobeIncident, GlobeOutcome, GlobeProvocation, IncidentGlobeData } from "../types";

const outcomeConfig: Record<GlobeOutcome, { label: string; color: string; icon: typeof Skull }> = {
  fatal: { label: "Fatal", color: "#f34b5f", icon: Skull },
  fatal_consumed: { label: "Fatal, body not recovered / consumed", color: "#8f1d36", icon: CircleDot },
  non_fatal: { label: "Non-fatal injury", color: "#ffbe3d", icon: HeartPulse },
  no_injury: { label: "No injury", color: "#2ed3b7", icon: ShieldCheck },
};

const decades = [
  { value: null, label: "All 1990–2026" },
  { value: 1990, label: "1990s" },
  { value: 2000, label: "2000s" },
  { value: 2010, label: "2010s" },
  { value: 2020, label: "2020–2026" },
] as const;

const provocationOptions: Array<{ value: "all" | GlobeProvocation; label: string }> = [
  { value: "all", label: "All" },
  { value: "unprovoked", label: "Unprovoked" },
  { value: "provoked", label: "Provoked" },
  { value: "unknown", label: "Unknown" },
  { value: "conflicted", label: "Conflicted" },
];

export function IncidentGlobePage() {
  const [data, setData] = useState<IncidentGlobeData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<GlobeIncident | null>(null);
  const [hovered, setHovered] = useState<GlobeIncident | null>(null);
  const [decade, setDecade] = useState<number | null>(null);
  const [provocation, setProvocation] = useState<"all" | GlobeProvocation>("all");
  const [outcomes, setOutcomes] = useState<Set<GlobeOutcome>>(new Set(Object.keys(outcomeConfig) as GlobeOutcome[]));
  const [autoRotate, setAutoRotate] = useState(true);
  const [showUnmapped, setShowUnmapped] = useState(false);
  const globeRef = useRef<GlobeHandle>(null);

  useEffect(() => {
    let active = true;
    getIncidentGlobe()
      .then((payload) => active && setData(payload))
      .catch((reason: unknown) => active && setError(reason instanceof Error ? reason.message : "Globe data unavailable."));
    return () => {
      active = false;
    };
  }, []);

  const filtered = useMemo(() => {
    if (!data) return [];
    return data.records.filter(
      (record) =>
        (decade === null || record.decade === decade) &&
        (provocation === "all" || record.provocation === provocation) &&
        outcomes.has(record.outcome_category),
    );
  }, [data, decade, outcomes, provocation]);
  const mapped = useMemo(() => filtered.filter((record) => record.mapped && record.coordinates), [filtered]);
  const unmapped = useMemo(() => filtered.filter((record) => !record.mapped || !record.coordinates), [filtered]);
  const counts = useMemo(
    () =>
      filtered.reduce<Record<string, number>>((acc, record) => {
        acc[record.outcome_category] = (acc[record.outcome_category] ?? 0) + 1;
        return acc;
      }, {}),
    [filtered],
  );

  const toggleOutcome = (outcome: GlobeOutcome) => {
    setOutcomes((current) => {
      const next = new Set(current);
      if (next.has(outcome)) next.delete(outcome);
      else next.add(outcome);
      return next;
    });
  };

  return (
    <section className="incident-globe-page" aria-label="Global shark incident explorer">
      {error ? <GlobeError message={error} /> : null}
      {!data && !error ? <div className="globe-loading">Building incident globe…</div> : null}
      <GlobeCanvas ref={globeRef} records={mapped} autoRotate={autoRotate} onSelect={setSelected} onHover={setHovered} />

      <header className="globe-heading">
        <p className="eyebrow">AI1SAD incident atlas</p>
        <h2>Shark incidents, 1990–2026</h2>
        <p>Deduplicated source records from the AI1SAD database, GSAF-derived files, ASID, and Hal / Sharks Happen.</p>
      </header>

      <div className="globe-toolbar" aria-label="Globe filters">
        <div className="globe-filter-group">
          <span>Decade</span>
          <div className="segmented-control">
            {decades.map((item) => (
              <button key={item.label} type="button" className={decade === item.value ? "active" : ""} onClick={() => setDecade(item.value)}>
                {item.label}
              </button>
            ))}
          </div>
        </div>
        <div className="globe-filter-group">
          <span>Incident context</span>
          <div className="segmented-control compact">
            {provocationOptions.map((item) => (
              <button key={item.value} type="button" className={provocation === item.value ? "active" : ""} onClick={() => setProvocation(item.value)}>
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="globe-summary" aria-live="polite">
        <strong>{filtered.length.toLocaleString()}</strong><span>records</span>
        <strong>{mapped.length.toLocaleString()}</strong><span>mapped</span>
        <strong>{unmapped.length.toLocaleString()}</strong><span>location unresolved</span>
        <button
          type="button"
          className="unmapped-open"
          onClick={() => { setSelected(null); setShowUnmapped(true); }}
          disabled={!unmapped.length}
        >
          <ListFilter size={15} /> Browse records
        </button>
      </div>

      <div className="globe-legend" aria-label="Outcome marker legend">
        {(Object.entries(outcomeConfig) as Array<[GlobeOutcome, (typeof outcomeConfig)[GlobeOutcome]]>).map(([key, config]) => {
          const Icon = config.icon;
          return (
            <label key={key} className={outcomes.has(key) ? "enabled" : "disabled"}>
              <input type="checkbox" checked={outcomes.has(key)} onChange={() => toggleOutcome(key)} />
              <span className="legend-symbol" style={{ color: config.color }}><Icon size={16} /></span>
              <span>{config.label}</span>
              <b>{(counts[key] ?? 0).toLocaleString()}</b>
            </label>
          );
        })}
        <small>Globe imagery: NASA Blue Marble. Drag to rotate; wheel to zoom.</small>
      </div>

      <div className="globe-actions">
        <button type="button" onClick={() => globeRef.current?.zoomIn()} title="Zoom in" aria-label="Zoom in"><Plus size={18} /></button>
        <button type="button" onClick={() => globeRef.current?.zoomOut()} title="Zoom out" aria-label="Zoom out"><Minus size={18} /></button>
        <button type="button" onClick={() => globeRef.current?.reset()} title="Reset globe" aria-label="Reset globe"><LocateFixed size={18} /></button>
        <button type="button" className={autoRotate ? "active" : ""} onClick={() => setAutoRotate((value) => !value)} title="Toggle rotation" aria-label="Toggle rotation"><RotateCcw size={18} /></button>
      </div>

      {hovered && !selected ? <div className="globe-tooltip"><strong>{formatLocation(hovered)}</strong><span>{formatDate(hovered)} · {outcomeConfig[hovered.outcome_category].label}</span></div> : null}
      {showUnmapped ? (
        <UnmappedIncidentDrawer
          records={unmapped}
          onClose={() => setShowUnmapped(false)}
          onSelect={(incident) => { setShowUnmapped(false); setSelected(incident); }}
        />
      ) : null}
      {selected ? <IncidentInfographic incident={selected} onClose={() => setSelected(null)} /> : null}
    </section>
  );
}

export default IncidentGlobePage;

type GlobeHandle = { reset: () => void; zoomIn: () => void; zoomOut: () => void };

const GlobeCanvas = forwardRef<GlobeHandle, {
  records: GlobeIncident[];
  autoRotate: boolean;
  onSelect: (incident: GlobeIncident) => void;
  onHover: (incident: GlobeIncident | null) => void;
}>(function GlobeCanvas({ records, autoRotate, onSelect, onHover }, ref) {
  const mountRef = useRef<HTMLDivElement>(null);
  const recordsRef = useRef(records);
  const autoRotateRef = useRef(autoRotate);
  const globeGroupRef = useRef<THREE.Group | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);

  useEffect(() => { recordsRef.current = records; }, [records]);
  useEffect(() => { autoRotateRef.current = autoRotate; }, [autoRotate]);
  useImperativeHandle(ref, () => ({
    reset: () => {
      if (globeGroupRef.current) globeGroupRef.current.rotation.set(0.15, -0.75, 0);
      if (cameraRef.current) cameraRef.current.position.z = 5.5;
    },
    zoomIn: () => { if (cameraRef.current) cameraRef.current.position.z = Math.max(3.3, cameraRef.current.position.z - 0.45); },
    zoomOut: () => { if (cameraRef.current) cameraRef.current.position.z = Math.min(8, cameraRef.current.position.z + 0.45); },
  }), []);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#02080d");
    const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
    camera.position.set(0, 0, 5.5);
    cameraRef.current = camera;
    const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    mount.appendChild(renderer.domElement);

    const globeGroup = new THREE.Group();
    globeGroup.rotation.set(0.15, -0.75, 0);
    globeGroupRef.current = globeGroup;
    scene.add(globeGroup);
    scene.add(new THREE.AmbientLight(0x8fb8c7, 1.1));
    const sun = new THREE.DirectionalLight(0xffffff, 2.2);
    sun.position.set(4, 2, 5);
    scene.add(sun);

    const texture = new THREE.TextureLoader().load("/data/earth-blue-marble.png");
    texture.colorSpace = THREE.SRGBColorSpace;
    const earth = new THREE.Mesh(
      new THREE.SphereGeometry(2, 96, 64),
      new THREE.MeshPhongMaterial({ map: texture, shininess: 8, specular: new THREE.Color("#366477") }),
    );
    globeGroup.add(earth);
    const atmosphere = new THREE.Mesh(
      new THREE.SphereGeometry(2.035, 96, 64),
      new THREE.MeshBasicMaterial({ color: 0x4fd5ff, transparent: true, opacity: 0.08, side: THREE.BackSide }),
    );
    scene.add(atmosphere);

    const starsGeometry = new THREE.BufferGeometry();
    const starPositions = new Float32Array(1200 * 3);
    for (let index = 0; index < starPositions.length; index += 3) {
      const radius = 14 + Math.random() * 18;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      starPositions[index] = radius * Math.sin(phi) * Math.cos(theta);
      starPositions[index + 1] = radius * Math.cos(phi);
      starPositions[index + 2] = radius * Math.sin(phi) * Math.sin(theta);
    }
    starsGeometry.setAttribute("position", new THREE.BufferAttribute(starPositions, 3));
    scene.add(new THREE.Points(starsGeometry, new THREE.PointsMaterial({ color: 0x8ca7b7, size: 0.018, transparent: true, opacity: 0.65 })));

    const markerRoot = new THREE.Group();
    globeGroup.add(markerRoot);
    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    let dragging = false;
    let moved = false;
    let startX = 0;
    let startY = 0;
    let lastX = 0;
    let lastY = 0;

    let renderedRecords = recordsRef.current;
    const rebuildMarkers = () => {
      while (markerRoot.children.length) {
        const child = markerRoot.children.pop() as THREE.InstancedMesh;
        const material = child.material as THREE.MeshBasicMaterial;
        material.map?.dispose();
        child.geometry.dispose();
        material.dispose();
      }
      (Object.keys(outcomeConfig) as GlobeOutcome[]).forEach((outcome) => {
        const subset = recordsRef.current.filter((record) => record.outcome_category === outcome && record.coordinates);
        if (!subset.length) return;
        const textureMap = markerTexture(outcomeConfig[outcome].color, outcome === "fatal_consumed");
        const mesh = new THREE.InstancedMesh(
          new THREE.PlaneGeometry(0.13, 0.13),
          new THREE.MeshBasicMaterial({
            map: textureMap,
            transparent: true,
            alphaTest: 0.08,
            side: THREE.FrontSide,
            depthTest: true,
            depthWrite: false,
          }),
          subset.length,
        );
        const dummy = new THREE.Object3D();
        subset.forEach((record, index) => {
          const [lon, lat] = record.coordinates!.coordinates;
          const position = latLonToVector(lat, lon, 2.045);
          dummy.position.copy(position);
          dummy.lookAt(position.clone().multiplyScalar(2));
          dummy.updateMatrix();
          mesh.setMatrixAt(index, dummy.matrix);
        });
        mesh.instanceMatrix.needsUpdate = true;
        mesh.userData.records = subset;
        markerRoot.add(mesh);
      });
    };
    rebuildMarkers();

    const updatePointer = (event: PointerEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    };
    const pick = (event: PointerEvent): GlobeIncident | null => {
      updatePointer(event);
      raycaster.setFromCamera(pointer, camera);
      const hit = raycaster.intersectObjects(markerRoot.children, false)[0];
      if (!hit || hit.instanceId === undefined) return null;
      return (hit.object.userData.records as GlobeIncident[])[hit.instanceId] ?? null;
    };
    const pointerDown = (event: PointerEvent) => {
      dragging = true; moved = false; startX = lastX = event.clientX; startY = lastY = event.clientY;
      renderer.domElement.setPointerCapture(event.pointerId);
    };
    const pointerMove = (event: PointerEvent) => {
      if (dragging) {
        const dx = event.clientX - lastX;
        const dy = event.clientY - lastY;
        if (Math.hypot(event.clientX - startX, event.clientY - startY) > 4) moved = true;
        globeGroup.rotation.y += dx * 0.005;
        globeGroup.rotation.x = THREE.MathUtils.clamp(globeGroup.rotation.x + dy * 0.004, -1.2, 1.2);
        lastX = event.clientX; lastY = event.clientY;
      } else {
        const incident = pick(event);
        renderer.domElement.style.cursor = incident ? "pointer" : "grab";
        onHover(incident);
      }
    };
    const pointerUp = (event: PointerEvent) => {
      if (!moved) {
        const incident = pick(event);
        if (incident) onSelect(incident);
      }
      dragging = false;
      renderer.domElement.releasePointerCapture(event.pointerId);
    };
    const wheel = (event: WheelEvent) => {
      event.preventDefault();
      camera.position.z = THREE.MathUtils.clamp(camera.position.z + event.deltaY * 0.003, 3.3, 8);
    };
    renderer.domElement.addEventListener("pointerdown", pointerDown);
    renderer.domElement.addEventListener("pointermove", pointerMove);
    renderer.domElement.addEventListener("pointerup", pointerUp);
    renderer.domElement.addEventListener("wheel", wheel, { passive: false });

    const resize = () => {
      const width = mount.clientWidth;
      const height = mount.clientHeight;
      renderer.setSize(width, height, false);
      camera.aspect = width / Math.max(height, 1);
      camera.updateProjectionMatrix();
    };
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(mount);
    resize();
    let animationFrame = 0;
    const animate = () => {
      if (autoRotateRef.current && !dragging) globeGroup.rotation.y += 0.0007;
      renderer.render(scene, camera);
      animationFrame = requestAnimationFrame(animate);
    };
    animate();

    const markerInterval = window.setInterval(() => {
      if (recordsRef.current !== renderedRecords) {
        renderedRecords = recordsRef.current;
        rebuildMarkers();
      }
    }, 250);
    return () => {
      window.clearInterval(markerInterval);
      cancelAnimationFrame(animationFrame);
      resizeObserver.disconnect();
      renderer.domElement.removeEventListener("pointerdown", pointerDown);
      renderer.domElement.removeEventListener("pointermove", pointerMove);
      renderer.domElement.removeEventListener("pointerup", pointerUp);
      renderer.domElement.removeEventListener("wheel", wheel);
      texture.dispose();
      renderer.dispose();
      mount.removeChild(renderer.domElement);
    };
  }, [onHover, onSelect]);

  return <div className="incident-globe-canvas" ref={mountRef} />;
});

function markerTexture(color: string, consumed: boolean): THREE.CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = 96;
  const context = canvas.getContext("2d")!;
  context.translate(48, 48);
  context.rotate(Math.PI / 4);
  context.fillStyle = color;
  context.shadowColor = color;
  context.shadowBlur = 16;
  context.fillRect(-24, -24, 48, 48);
  context.shadowBlur = 0;
  context.strokeStyle = "rgba(255,255,255,.9)";
  context.lineWidth = 5;
  context.strokeRect(-24, -24, 48, 48);
  if (consumed) {
    context.fillStyle = "#07090c";
    context.beginPath();
    context.arc(0, 0, 11, 0, Math.PI * 2);
    context.fill();
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function latLonToVector(lat: number, lon: number, radius: number): THREE.Vector3 {
  const phi = THREE.MathUtils.degToRad(90 - lat);
  const theta = THREE.MathUtils.degToRad(lon + 180);
  return new THREE.Vector3(
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta),
  );
}

function IncidentInfographic({ incident, onClose }: { incident: GlobeIncident; onClose: () => void }) {
  const outcome = outcomeConfig[incident.outcome_category];
  const Icon = outcome.icon;
  return (
    <aside className="incident-infographic" aria-label="Incident details">
      <button className="infographic-close" type="button" onClick={onClose} aria-label="Close incident details"><X size={20} /></button>
      <div className="infographic-outcome" style={{ color: outcome.color }}><Icon size={22} /><span>{outcome.label}</span></div>
      <p className="eyebrow">{formatDate(incident)}</p>
      <h2>{formatLocation(incident)}</h2>
      <div className="infographic-badges">
        <span className={`provocation ${incident.provocation}`}>{formatProvocation(incident.provocation)}</span>
        <span>{coordinateLabel(incident)}</span>
      </div>
      <dl className="incident-facts">
        <div><dt>Activity</dt><dd>{incident.activity || "Not recorded"}</dd></div>
        <div><dt>Species</dt><dd>{incident.species_common || "Not confirmed / not recorded"}</dd></div>
        <div><dt>Incident type</dt><dd>{incident.incident_type_raw || "Not recorded"}</dd></div>
        <div className="wide"><dt>Injury</dt><dd>{incident.injury_summary || "Not recorded"}</dd></div>
      </dl>
      <section className="infographic-section">
        <h3>Sources <span>{incident.source_count}</span></h3>
        <ul className="source-list">
          {incident.sources.map((source, index) => (
            <li key={`${source.source_name}-${source.source_record_id}-${index}`}>
              <div><strong>{source.source_label}</strong><span>{source.match_status.replaceAll("_", " ")}</span></div>
              {source.url ? <a href={source.url} target="_blank" rel="noreferrer" title={`Open ${source.url_scope ?? "source"} link`}><ExternalLink size={16} /></a> : null}
            </li>
          ))}
        </ul>
      </section>
      <section className="infographic-section">
        <h3>Media</h3>
        {incident.media.length ? (
          <div className="incident-media">
            {incident.media.map((media) => <a key={media.url} href={media.url} target="_blank" rel="noreferrer"><img src={media.thumbnail_url || media.url} alt={media.alt} /></a>)}
          </div>
        ) : <p className="media-empty"><ImageOff size={17} /> No rights-cleared image is linked in the source record.</p>}
      </section>
      <footer>Source-derived historical record. Provocation, species, injury, and outcome labels preserve database uncertainty.</footer>
    </aside>
  );
}

function UnmappedIncidentDrawer({
  records,
  onClose,
  onSelect,
}: {
  records: GlobeIncident[];
  onClose: () => void;
  onSelect: (incident: GlobeIncident) => void;
}) {
  const [query, setQuery] = useState("");
  const [country, setCountry] = useState("all");
  const [region, setRegion] = useState("all");
  const countryCounts = useMemo(() => {
    const counts = new Map<string, number>();
    records.forEach((record) => {
      const label = record.country?.trim() || "Country not recorded";
      counts.set(label, (counts.get(label) ?? 0) + 1);
    });
    return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  }, [records]);
  const regionCounts = useMemo(() => {
    const counts = new Map<string, number>();
    records.forEach((record) => {
      const recordCountry = record.country?.trim() || "Country not recorded";
      if (country !== "all" && recordCountry !== country) return;
      const label = record.region?.trim() || "Region not recorded";
      counts.set(label, (counts.get(label) ?? 0) + 1);
    });
    return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  }, [country, records]);
  const visibleRecords = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase();
    return records.filter((record) => {
      const recordCountry = record.country?.trim() || "Country not recorded";
      if (country !== "all" && recordCountry !== country) return false;
      const recordRegion = record.region?.trim() || "Region not recorded";
      if (region !== "all" && recordRegion !== region) return false;
      if (!normalizedQuery) return true;
      return [
        record.location,
        record.region,
        record.country,
        record.activity,
        record.species_common,
        record.injury_summary,
        formatDate(record),
      ].some((value) => String(value ?? "").toLocaleLowerCase().includes(normalizedQuery));
    });
  }, [country, query, records, region]);
  const precisionCounts = useMemo(
    () => records.reduce<Record<LocationResolution, number>>(
      (counts, record) => {
        counts[locationResolution(record)] += 1;
        return counts;
      },
      { locality: 0, region: 0, country: 0, unknown: 0 },
    ),
    [records],
  );

  return (
    <aside className="unmapped-drawer" aria-label="Unmapped incident records">
      <header>
        <div>
          <p className="eyebrow">Visible without a guessed pin</p>
          <h2>Unmapped incidents</h2>
          <p>{records.length.toLocaleString()} source-derived records match the active globe filters.</p>
        </div>
        <button className="infographic-close" type="button" onClick={onClose} aria-label="Close unmapped incidents"><X size={20} /></button>
      </header>

      <div className="unmapped-resolution-summary" aria-label="Location resolution summary">
        <div><strong>{precisionCounts.locality.toLocaleString()}</strong><span>Named locality</span></div>
        <div><strong>{precisionCounts.region.toLocaleString()}</strong><span>Region only</span></div>
        <div><strong>{precisionCounts.country.toLocaleString()}</strong><span>Country only</span></div>
        <div><strong>{precisionCounts.unknown.toLocaleString()}</strong><span>No location</span></div>
      </div>

      <div className="unmapped-controls">
        <label className="unmapped-search">
          <Search size={16} aria-hidden="true" />
          <input aria-label="Search unmapped incidents" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search location, activity, date, injury…" />
        </label>
        <label>
          <span>Country</span>
          <select value={country} onChange={(event) => { setCountry(event.target.value); setRegion("all"); }}>
            <option value="all">All countries</option>
            {countryCounts.map(([label, count]) => <option key={label} value={label}>{label} ({count.toLocaleString()})</option>)}
          </select>
        </label>
        <label>
          <span>Region</span>
          <select value={region} onChange={(event) => setRegion(event.target.value)}>
            <option value="all">All regions</option>
            {regionCounts.map(([label, count]) => <option key={label} value={label}>{label} ({count.toLocaleString()})</option>)}
          </select>
        </label>
      </div>

      <div className="unmapped-results-heading">
        <span>{visibleRecords.length.toLocaleString()} records</span>
        <small>Open any record for its full source infographic.</small>
      </div>
      <div className="unmapped-list">
        {visibleRecords.map((incident) => {
          const outcome = outcomeConfig[incident.outcome_category];
          const Icon = outcome.icon;
          return (
            <button key={incident.globe_id} type="button" onClick={() => onSelect(incident)}>
              <span className="unmapped-outcome" style={{ color: outcome.color }}><Icon size={17} /></span>
              <span className="unmapped-record-copy">
                <strong>{formatLocation(incident)}</strong>
                <span>{formatDate(incident)} · {incident.activity || "Activity not recorded"}</span>
              </span>
              <span className={`resolution-badge ${locationResolution(incident)}`}><MapPinOff size={13} />{resolutionLabel(incident)}</span>
            </button>
          );
        })}
        {!visibleRecords.length ? <p className="unmapped-empty">No unresolved records match this search.</p> : null}
      </div>
      <footer>These incidents remain part of the database and all filtered totals. Broad or missing locations are listed here instead of being assigned misleading coordinates.</footer>
    </aside>
  );
}

type LocationResolution = "locality" | "region" | "country" | "unknown";

function locationResolution(incident: GlobeIncident): LocationResolution {
  if (incident.location?.trim()) return "locality";
  if (incident.region?.trim()) return "region";
  if (incident.country?.trim()) return "country";
  return "unknown";
}

function resolutionLabel(incident: GlobeIncident): string {
  const resolution = locationResolution(incident);
  if (resolution === "locality") return "Locality review";
  if (resolution === "region") return "Region only";
  if (resolution === "country") return "Country only";
  return "No location";
}

function coordinateLabel(incident: GlobeIncident): string {
  if (!incident.mapped || !incident.coordinates) return `Unmapped · ${resolutionLabel(incident)}`;
  if (incident.coordinate_confidence === "approximate") return "Approximate map point";
  if (incident.coordinate_source === "source_coordinate") return "Source coordinate";
  return "Reviewed contextual coordinate";
}

function GlobeError({ message }: { message: string }) {
  return <div className="globe-error"><strong>Incident globe unavailable</strong><span>{message}</span></div>;
}

function formatDate(incident: GlobeIncident): string {
  return incident.date_text || [incident.year, incident.month, incident.day].filter(Boolean).join("-") || String(incident.year);
}

function formatLocation(incident: GlobeIncident): string {
  return [incident.location, incident.region, incident.country].filter(Boolean).join(", ") || "Location not recorded";
}

function formatProvocation(value: GlobeProvocation): string {
  if (value === "conflicted") return "Provocation conflicted";
  if (value === "unknown") return "Provocation unknown";
  return value[0].toUpperCase() + value.slice(1);
}
