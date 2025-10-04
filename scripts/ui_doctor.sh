#!/usr/bin/env bash
set -u
host="http://127.0.0.1:8000"
ollama="http://127.0.0.1:11434"
ok=0; fail=0
check(){ local name="$1"; shift
  if "$@"; then echo "[OK]  $name"; ((ok++)); else echo "[FAIL] $name"; ((fail++)); fi
}

# 1) Root served and has our input IDs
check "GET / (200)" bash -lc "curl -s -o /dev/null -w '%{http_code}' $host/ | grep -q '^200$'"
check "HTML has id=prompt" bash -lc "curl -s $host/ | grep -q 'id=\"prompt\"'"
check "HTML has id=messages" bash -lc "curl -s $host/ | grep -q 'id=\"messages\"'"

# 2) JS served from /static
check "GET /static/app.js (200)" bash -lc "curl -s -o /dev/null -w '%{http_code}' $host/static/app.js | grep -q '^200$'"

# 3) Backend chat endpoint
check "POST /v1/chat returns JSON" bash -lc "curl -s $host/v1/chat -H 'content-type: application/json' -d '{\"model\":\"qwen2.5:14b-instruct\",\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}]}' | grep -Eq '\"choices\"|\"error\"'"

# 4) Ollama
check "Ollama API reachable" bash -lc "curl -s -o /dev/null -w '%{http_code}' $ollama/api/tags | grep -q '^200$'"

echo
echo "UI Doctor summary: $ok ok, $fail fail"
exit $fail
