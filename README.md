# 🤖 Adam v1 — Modular, Local-First, Self-Updating LLM Assistant

Adam is a locally-runnable, plugin-based AI assistant that adapts to your hardware and tasks. Fully offline-first, modular, and built for extensibility.

- **Plugins:** write code, manage memory, audit hardware, run tools — all hot-swappable.
- **Model routing:** light condenser → heavy executor selected by hardware.
- **Observable:** structured logs, self-test, config-driven behavior.
- **Resilient:** degrades gracefully when a plugin/back-end isn’t available.

---

## 🚀 Quick Start

```bash
# 1) create env (or use system Python)
python3 -m venv .venv && source .venv/bin/activate

# 2) install
pip install -r requirements.txt

# 3) (optional) get the light model
# Download light-condenser.gguf from Releases and place it here:
#   models/light-condenser.gguf

# 4) run a quick ask
python3 run_adam.py --ask "What time is it?"
If you build the single binary with PyInstaller, the light model may be bundled. For source installs, place it under models/ as shown above.

📦 Layout
bash
Copy code
src/adam/            # core engine
plugins/             # drop .py to extend Adam (router, local_llm, tools, etc.)
tools/               # heavier on-demand scripts
sidecars/            # external services (optional)
docs/                # specs, runbooks, ADRs
config/              # YAML/JSON config
🧩 Plugins
Adam discovers plugins from plugins/.

Examples:

bash
Copy code
# run a plugin directly
python3 run_adam.py --plugin memory_write --args '{"content":"Remember this."}'

# health report (no execution)
python3 run_adam.py --plugin-health
🧠 Models
Light (condenser): models/light-condenser.gguf (download from Releases).

Heavy (executor): auto-selected by hardware audit; downloaded on demand if not present (configurable).

You can override choices in config/ or via CLI flags.

🧪 Self-Test
bash
Copy code
python3 run_adam.py --self-test
🔐 Offline-First
No external APIs by default. Networked features are opt-in and isolated.

🛠 Build (optional)
Single binary:

bash
Copy code
pyinstaller --clean -y packaging/adam.spec
Docker:
Use the provided Dockerfile (CPU baseline).

📜 License
MIT. See LICENSE.
