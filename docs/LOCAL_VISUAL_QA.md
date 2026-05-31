# Local Visual QA

Use this checklist for the AI1SAD local demo polish pass.

## Local URLs

- Frontend: <http://localhost:5174>
- FastAPI docs: <http://localhost:8000/docs>
- MkDocs: <http://localhost:8001>

FretTrack may already occupy port `5173`, so run the AI1SAD frontend on `5174` for local visual checks.

## One-Click Local Launcher

Windows users can start the full local demo by double-clicking:

```text
start_ai1sad_demo.bat
```

The launcher starts:

- Backend: <http://localhost:8000>
- FastAPI docs: <http://localhost:8000/docs>
- Frontend: <http://localhost:5174>
- MkDocs: <http://localhost:8001>

It also opens browser tabs for the frontend, FastAPI docs, and MkDocs portal.

The batch wrapper calls the PowerShell launcher:

```powershell
.\start_ai1sad_demo.ps1
```

The launcher warns if ports `8000`, `5174`, or `8001` are already in use. It does not silently replace existing processes.

## Stop Script

Stop the local demo by double-clicking:

```text
stop_ai1sad_demo.bat
```

Or run:

```powershell
.\stop_ai1sad_demo.ps1
```

The stop script terminates processes bound to ports `8000`, `5174`, and `8001`.

## Manual Fallback Commands

Backend:

```powershell
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Windows Python fallback:

```powershell
F:\Python310\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
cd frontend
npm run dev -- --host 0.0.0.0 --port 5174
```

MkDocs:

```powershell
mkdocs serve --dev-addr 0.0.0.0:8001
```

## Demo Notes

- The frontend demo banner must be visible when demo mode is enabled.
- `warning_score` is the general public-facing warning signal for the selected location.
- `activity_hazard_score` captures activity, habitat, season, species, and exposure context from backend outputs.
- `surveillance_priority_score` is the operational priority for where patrol or drone coverage should look next.
- Low warning with high surveillance priority is valid when public messaging can remain calm while operators still have location-specific reasons to observe a zone.

## Screenshots Checklist

- [ ] Landing/dashboard
- [ ] Operational map
- [ ] Why This Zone panel
- [ ] Replay view
- [ ] Provider health
- [ ] Docs portal

## Validation Checklist

- [ ] Frontend tests
- [ ] Frontend build
- [ ] Backend tests
- [ ] MkDocs build
- [ ] Secret scan
