#!/usr/bin/env bash
set -u
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ok=0; fail=0
check(){ local name="$1" ; shift
  if "$@"; then echo "[OK]  $name"; ((ok++)); else echo "[FAIL] $name"; ((fail++)); fi
}

# 1) Adam self-test
check "Adam self-test" bash -lc "cd \"$BASE\" && python3 Adam.py --self-test >/dev/null 2>&1"

# 2) Config present
check "config/adam.yaml exists" test -f "$BASE/config/adam.yaml"

# 3) Plugin stubs importable
check "plugin: memory_write import"  python3 - <<PY
import importlib, sys
sys.exit(0 if importlib.util.find_spec('adam_tools.plugins.memory_write') else 1)
PY
check "plugin: memory_search import" python3 - <<PY
import importlib, sys
sys.exit(0 if importlib.util.find_spec('adam_tools.plugins.memory_search') else 1)
PY
check "plugin: memory_summarize import" python3 - <<PY
import importlib, sys
sys.exit(0 if importlib.util.find_spec('adam_tools.plugins.memory_summarize') else 1)
PY

# 4) Ollama reachable
check "Ollama API reachable" bash -lc "curl -sS http://127.0.0.1:11434/api/tags >/dev/null"

# 5) EmbeddingGemma responds
check "EmbeddingGemma embed" bash -lc "curl -sS http://127.0.0.1:11434/api/embed -H 'content-type: application/json' -d '{\"model\":\"embeddinggemma\",\"input\":\"hello\"}' | grep -q 'embedding'"

echo
echo "Doctor summary: $ok ok, $fail fail"
exit $fail
