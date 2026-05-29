# Local Visual QA

Use this checklist for the AI1SAD local demo polish pass.

## Local URLs

- Frontend: <http://localhost:5174>
- FastAPI docs: <http://localhost:8000/docs>
- MkDocs: <http://localhost:8001>

FretTrack may already occupy port `5173`, so run the AI1SAD frontend on `5174` for local visual checks.

## Local Startup Script

Windows users can start the local demo with:

```powershell
.\start_ai1sad_demo.ps1 -Docs
```

The `start_ai1sad_demo.bat` wrapper calls the PowerShell script for double-click or Command Prompt usage. The script starts FastAPI on `127.0.0.1:8000`, Vite on `127.0.0.1:5174`, and MkDocs on `127.0.0.1:8001` when `-Docs` is passed. It prefers `F:\Python310\python.exe` when present and falls back to `python`; pass `-Python <path>` to override the interpreter.

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
