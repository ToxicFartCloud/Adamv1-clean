# Adam — Project Guidelines & Living Docs
_Last updated: 2025-09-22_

## Current Goals & Roadmap
- **Stabilize core run path**: Adam.py (launcher) → adam_base.py (orchestrator) → UI → backend.
- **Keep offline-first**: no cloud keys or paid APIs in artifacts; local models via `models/`.
- **Operator UX**: UI Start/Stop backend toggle; on-demand autostart in orchestrator.
- **Diagnostics-first**: quick and deep repo checks to prevent drift.
- **Next**: plugin hygiene (silence missing ones or implement), minimal RAG backend, nightly eval hook.

## Architecture Notes
- **Launcher (`Adam.py`)**: Thin wrapper; cds to repo root, seeds `sys.path`, delegates to `adam_base.main`, defaults to `--ui` if no args.
- **Orchestrator (`adam_base.py`)**: CLI, config load/merge, JSON logging (guarded `asctime`), `run_ui` with **`ensure_backend`** (starts `uvicorn server.app:app` on 127.0.0.1:8000 if down), plugin discovery.
- **Backend (`server/app.py`)**: FastAPI on **127.0.0.1:8000**; exposes `/admin/health` and `/admin/shutdown` for UI control.
- **UI (`ui/UI.py`)**: Tk app; **Server** menu (Start ▶ / Stop ■) calling backend start/shutdown.
- **Sidecars**: SLED runner at `sidecars/sled/app.py` (separate port, optional). Future: embeddings/RAG sidecar.
- **Config**: `config/adam.yaml` includes `default_model_path`; repo maintains `models/` dir.
- **Diagnostics**: `scripts/diagnostics/diag_adam.py` (smoke), `scripts/diagnostics/deep_diag.py` (wiring).

## Policies
- **Offline-only ops** for Adam; artifacts avoid cloud creds/APIs.
- **No edits to `Adam.py`** unless explicitly approved; prefer orchestrator + plugins/sidecars.
- **Edit protocol**: ≤2 steps per file, show line numbers & context, def before/after, imports **outside** code blocks.
- **Living doc visibility**: share **Updated/Added** snippets by default; show entire doc only on request.
- **Eval gates & rollback**: keep self-test green; use snapshots to revert when a regression is detected.

## Operations
### Runbook (Quick Start)
- `python3 Adam.py --self-test` → should print only “missing plugin” notices.
- `python3 Adam.py --ui` → opens UI; orchestrator auto-starts backend if down.
- Backend manual: `python3 -m uvicorn server.app:app --host 127.0.0.1 --port 8000`.
- Health: `curl -s http://127.0.0.1:8000/admin/health` or root `/`.

### UI Server Toggle
- **Start ▶**: spawns `uvicorn server.app:app` if port is closed.
- **Stop ■**: POST `/admin/shutdown` (graceful self-exit).

### Diagnostics
- **Quick**: `python3 scripts/diagnostics/diag_adam.py` → checks launcher, `run_ui`, backend reachability.
- **Deep**: `python3 scripts/diagnostics/deep_diag.py` → validates split/UI/backend/sidecar hooks, default model path, plugins list.
- Current status: **deep diag ok=true** with `models/` present.

### Snapshots Policy
- Latest known-good: `snapshots/post_diags_2025-09-22_0450.tgz`.
- Keep last **3** archives; prune older: `ls -1t snapshots/*.tgz | tail -n +4 | xargs -r rm -f`.

## Config
- `config/adam.yaml` must include:
  ```yaml
  default_model_path: models/adam_offline.gguf
  ```
- Repo hygiene (`.gitignore` suggested): `models/`, `logs/`, `snapshots/*.tgz`, `__pycache__/`.

## Decisions Log (dated one-liners)
- **2025-09-20**: Reset to base; rebuild via orchestrator + plugins/sidecars; keep UI separate from backend.
- **2025-09-20**: Autostart-on-demand chosen over always-on service (workstation-friendly).
- **2025-09-21**: Restored launcher/orchestrator split; fixed plugin discovery & logger; added `ensure_backend`.
- **2025-09-21**: Added UI Start/Stop and backend admin endpoints.
- **2025-09-22**: Added diagnostics suite; set `default_model_path`; deep diag green; snapshot captured.

## Changelog (docs-only)
- **2025-09-22**: Diagnostics docs; default model path; snapshots policy.
- **2025-09-21**: UI Server menu; admin health/shutdown; logging fix; plugin discovery init.
- **2025-09-20**: Split restoration; autostart helper; runbook drafted.

---

_Contact notes_: SLED remains optional (separate port). Missing plugins (e.g., `memory_client`) can be commented out until implemented.
