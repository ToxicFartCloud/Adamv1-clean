# UI Hosting — Smoke Test
## Preconditions
- Adam Core running on http://127.0.0.1:8000
- `config/adam.yaml` contains the `ui:` block
## Tests
# 1) Root serves HTML
curl -I http://127.0.0.1:8000/ | sed -n '1,5p'
# 2) Static serves app.js
curl -I http://127.0.0.1:8000/static/app.js | sed -n '1,5p'
# 3) Toggle off and confirm 404s (set ui.enabled: false, restart app)
curl -I http://127.0.0.1:8000/ | head -1
curl -I http://127.0.0.1:8000/static/app.js | head -1
# 4) Traversal is blocked
curl -I "http://127.0.0.1:8000/static/../config/adam.yaml" | head -1
