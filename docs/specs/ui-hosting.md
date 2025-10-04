# UI Hosting — Adam Core (FastAPI)
## Goal
Serve your Stitch UI (in `./ui`) from Adam Core on the same origin as the API:
- `GET /` → `ui/index.html`
- `GET /static/*` → files under `ui/`
- Controlled via `config/adam.yaml` → `ui.enabled`, `ui.dir`, `ui.index`, `ui.static_route`
## Config (already present in your YAML)
ui:
  enabled: true
  dir: ./ui
  index: index.html
  static_route: /static
## Behavior
- If `ui.enabled: false`: return **404** for `/` and any path under `ui.static_route`.
- If `ui.enabled: true`:
  - `GET /` → serve `File(ui.dir/ui.index)` with `Content-Type: text/html; charset=utf-8`, `Cache-Control: no-store`.
  - `GET {ui.static_route}/{path}` → serve `File(ui.dir/{path})` if and only if `{path}` resolves within `ui.dir` (reject `..` traversal).
    - Cache headers: `public, max-age=3600` for `.js,.css,.png,.svg,.jpg,.woff2`.
    - No directory listing; 404 if not found.
- Same-origin only; no CORS for UI→API calls.
- Log each request: `ui_request {path, status, bytes}`.
## Acceptance
1) With `ui.enabled: true`
   - `curl -I http://127.0.0.1:8000/` → 200 + `text/html`
   - `curl -I http://127.0.0.1:8000/static/app.js` → 200 + `application/javascript`
2) With `ui.enabled: false`
   - Both paths return 404
3) Security
   - `curl -I "http://127.0.0.1:8000/static/../config/adam.yaml"` → 404
## Implementation notes
- Mount static via Starlette static files at `ui.static_route`.
- Serve `/` with explicit file response from `ui.dir/ui.index`.
- Add safe join to prevent traversal.
- Respect YAML at runtime; fallback to `DEFAULT_CONFIG`.
- HTML `no-store`, static = cacheable.
