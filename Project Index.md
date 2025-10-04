# Project Index

## Core Runtime
- run_adam.py → Entry point.
- src/adam/core.py → Core assistant logic.
- src/adam/server/main.py → Server runtime.
- src/adam/ui/app.py → User interface.

## Plugins & Extensions
- backup_snapshot → System state management.
- git_ops → Repository & code operations.
- guard_approval → Safety checks & approval flow.
- hardware_audit → System environment awareness.
- memory_* → Long-term memory functions.
- model_router, model_update → Model selection & upgrade.
- ollama_llm → Ollama LLM integration.
- proc_app, proc_ps → Process management utilities.
- Web Search, wmgr → External search & task workflow.
- sled_client → System integration bridge.

## Sidecars
- director → Planning, task routing, orchestration.
- github_publisher → Automated GitHub publishing.
- sled → Edge/compute integration.

## Docs
- context → Guidelines, living docs, ADRs.
- specs → Design specs (pipelines, orchestrators, server checklists).
- runbooks → Operational docs & smoke tests.
- prompts → Prompt design library.

## Eval & Tests
- eval → JSONL test sets & evaluation tasks.
- tests → Plugin, adapter, and runtime tests.
- scripts → Automation, CI helpers, diagnostics.

## Data & Logs
- logs → Debug & audit trails.
- snapshots → Saved states.
- ui_data → Saved chats & user artifacts.
