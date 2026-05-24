# Replay Validation and Calibration Engine

Phase 6 adds a replay validation and calibration engine for testing warning, surveillance, and risk models against known scenarios.

The replay engine is standalone. It does not require a MongoDB connection. Scenarios are replayed through the deterministic rule engines to validate outputs, compare against quiet-day baselines, analyze signal decay, decompose confidence, and generate heatmaps.

## Architecture

```
app/replay/
  __init__.py         - Public API exports
  scenarios.py        - ReplayScenario dataclass, built-in scenarios
  runner.py           - ReplayRunner orchestrates scenario execution
  decay.py            - SignalDecayModel, type-specific decay parameters
  confidence.py       - ConfidenceDecomposition with source-weight breakdown
  quiet_day.py        - QuietDayBaseline for comparison
  heatmap.py          - HeatmapGenerator for coordinate-grid score maps
```

## Components

### Replay Scenarios

Each scenario captures a known location, timestamp, and environmental conditions. The runner feeds these through the existing `calculate_warning`, `score_surveillance_zones`, and risk engines.

Six built-in scenarios:

| Scenario | Region | Context |
|---|---|---|
| florida_summer_heavy_rain | Florida | Heavy summer rainfall, swimming |
| hawaii_sharktober_quiet | Hawaii | October quiet conditions, surfing |
| wa_spearfishing_reef_white | Western Australia | Spearfishing on reef, white shark suitability |
| south_africa_white_shark_surf_seal_colony | South Africa | White shark / seal colony / surf context |
| red_sea_oceanic_whitetip_feeding | Red Sea | Whale carcass feeding event |

Scenario packs are region-organized under `app/replay/datasets/`.

### Signal Decay

`SignalDecayModel` applies exponential half-life decay to signal values:

- `weather_rainfall`: 6h half-life, 24h expiry
- `sighting` / `shark_sighting`: 12h half-life, 36h expiry
- `carcass` / `whale_carcass`: 72h half-life, 144h expiry
- `ocean_sst`: 24h half-life, 72h expiry
- `biological_event`: 72h half-life, 144h expiry
- `sst_anomaly`: 48h half-life, 120h expiry
- `vessel_activity`: 12h half-life, 36h expiry

Decay weight = 2^(-age_hours / half_life_hours). Signals beyond `half_life * expiry_multiplier` hours receive weight 0.

### Confidence Decomposition

Confidence is decomposed into three weighted components:

- **coverage_confidence** (40%): what fraction of expected sources are present
- **freshness_confidence** (30%): penalty for stale sources
- **completeness_confidence** (30%): penalty for missing sources

Source weights are defined per data source (weather_observations, ocean_observations, vessel_activity, biological_events, etc.).

### Quiet-Day Comparison

The `QuietDayBaseline` defines a standard quiet-day input set (no rainfall, far from river mouth, moderate SST, minimal vessel/biological signal) and compares current replay output against it. The comparison reports delta, percent change, band change, and a text interpretation.

### Heatmap Generation

`HeatmapGenerator` produces coordinate grids centered on a location. Each grid cell is scored by the warning or risk engine, producing:

- `cells`: list of {lat, lon, score, band}
- `statistics`: min, max, avg, median score
- `config`: center, radius, cell count

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/v1/replay/scenarios` | List built-in replay scenarios |
| `GET /api/v1/replay/run` | Run a built-in scenario by `scenario_id` query parameter |
| `GET /api/v1/replay/compare` | Compare a scenario to quiet-day baseline by `scenario_id` query parameter |
| `POST /api/v1/replay/run` | Run a custom scenario |
| `GET /api/v1/replay/run-all` | Run all built-in scenarios |
| `GET /api/v1/replay/decay-analysis/{scenario_id}` | Signal decay analysis for a scenario |
| `GET /api/v1/replay/heatmap` | Generate surveillance-priority heatmap |
| `GET /api/v1/replay/run/{scenario_id}` | Compatibility helper for built-in scenario replay |
| `GET /api/v1/replay/compare-quiet-day/{scenario_id}` | Compare scenario to quiet-day baseline |

## CLI Usage

Replay scenarios can also be run directly without the API:

```python
from app.replay.scenarios import REPLAY_SCENARIOS
from app.replay.runner import ReplayRunner

runner = ReplayRunner()
result = runner.run_scenario(REPLAY_SCENARIOS["florida_summer_heavy_rain"])
print(result.warning["warning_score"], result.warning["warning_band"])
```

## Testing

Run replay-specific tests:

```
python -m pytest tests/test_replay_engine.py -v
```

## Limitations

- Scenarios are deterministic and do not include real-time provider data
- Heatmap generation recalculates scores per cell; large grids may be slow
- Quiet-day baseline uses fixed moderate inputs, not historical averages
- Signal decay is exponential; does not account for intermittent refresh patterns
