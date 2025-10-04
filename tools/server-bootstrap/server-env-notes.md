# Server Env Notes
# When the server is ready, set:

# 1) Ollama model storage (persistent)
# /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment=OLLAMA_MODELS=/srv/adam/models
# then:
# sudo systemctl daemon-reload && sudo systemctl restart ollama

# 2) (Optional) keep-alive behavior for models
# Environment=OLLAMA_KEEP_ALIVE=5m   # unload after 5 min idle (default-ish)
# or Environment=OLLAMA_KEEP_ALIVE=-1 # keep resident (not recommended for 24/7 unless you have RAM)

# 3) AnythingLLM data dir (container bind mount):
# -v /srv/adam/anythingllm:/app/data

# 4) Network
# Give the server a static IP or DHCP reservation, e.g., 192.168.1.50
# GUI: http://192.168.1.50:3001
# Ollama API: http://192.168.1.50:11434
