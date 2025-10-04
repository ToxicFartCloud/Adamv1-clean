<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
🤖 Adam v1 — Modular, Self-Updating, Local LLM Assistant

Adam is a locally-runnable, plugin-based AI assistant designed to adapt to your hardware, tasks, and preferences.
Think LM Studio meets AutoGPT — but fully offline, modular, and built for extensibility.

🔧 Plugins: Write code, search web, manage memory, audit hardware — all via hot-swappable plugins.

🧠 Self-Aware: Chooses models based on task + hardware. Logs everything. Learns from feedback.

📦 Modular: Breaks if one piece fails? Nope. Adam degrades gracefully.

🚀 Ready for Dev: Clean structure, self-test, logging, config — all set up.

▶️ Quick Start
pip install -r requirements.txt
python3 run_adam.py --ask "What time is it?"

🧩 Plugins
Adam discovers plugins automatically from /plugins.

Example:

Bash

python3 run_adam.py --plugin memory_write --args '{"content": "Remember this."}'
📂 Structure
src/adam/ — Core engine
plugins/ — Drop .py files here to extend Adam
tools/ — On-demand heavy tools
sidecars/ — External services (director, sled, etc.)
docs/ — Specs, runbooks, ADRs, context notes
config/ — System-wide settings
🧪 Test It
Bash

python3 run_adam.py --self-test
python3 run_adam.py --plugin-health
Built with ❤️ for developers who want full control over their AI assistant.

text


—

## 💡 FUTURE UPGRADES (When You’re Bored)

- ➤ `scripts/build_faiss_index.py` — auto-generate FAISS index from text files
- ➤ UI with Tkinter or Web frontend
- ➤ Dockerfile for containerized deployment
- ➤ MCP server integration
- ➤ Plugin auto-repair system (you mentioned this earlier — we can build it!)

=======
# Adamv1
Local AI assistant
>>>>>>> 85c76a261a6ba84258a977872145fec99d505d9c
=======
# Adamv1
Local AI assistant
>>>>>>> 85c76a261a6ba84258a977872145fec99d505d9c
=======
# Adamv1
Local AI assistant
>>>>>>> 85c76a261a6ba84258a977872145fec99d505d9c
