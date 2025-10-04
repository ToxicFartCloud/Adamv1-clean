# Server Bootstrap (Adamv1)
Goal: run AnythingLLM + Ollama on a dedicated box, 24/7. Desktop just connects via browser.

Services:
- Ollama (models + embeddings)
- AnythingLLM (GUI + agents)
- (Optional) TEI for embeddinggemma if centralizing embeddings

Ports:
- Ollama: 11434
- AnythingLLM: 3001 (example)
- TEI: 8080 (if used)

Data dirs (server):
- /srv/adam/models        # OLLAMA_MODELS
- /srv/adam/anythingllm   # AnythingLLM data/config
- /srv/adam/logs          # logs

Cutover steps (high level):
1) Install Docker/Podman or native packages.
2) Start Ollama as a service with OLLAMA_MODELS=/srv/adam/models.
3) Pull chat model (e.g., llama3.1:8b-instruct) + embeddinggemma.
4) Start AnythingLLM; set provider = Ollama @ http://SERVER_IP:11434.
5) Point your desktop browser to http://SERVER_IP:3001 and test.
