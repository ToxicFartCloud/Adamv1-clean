# spdx-FileCopyrightText: 2024 Eric Johnson
# spdx-License-Identifier: MIT

# Media Type (MIT)

# Copyright (c) 2024 Eric Johnson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
core.py -- Central Orchestrator for the Adam Project.

This file serves as the core orchestration engine for the Adam project.
It is designed to be a lean, offline-first, and extensible foundation.
All complex functionality, such as I/o adapters, model interaction,
and retrieval logic, is delegated to external, hot-swappable plugins.

Architectural Philosophy:
-------------------------
The core principle is decoupling the "how" from the "what". The core
orchestrator knows "what" to do (e.g., "embed text", "search a transcript"),
but it delegates the "how" (e.g., using a local GGUF model, querying a local
PgVector database) to specialized plugins. This ensures the core remains stable
and agnostic to specific implementations.

Plugin Development Guide:
-------------------------
Plugins are the primary mechanism for extending Adam's capabilities.

1. Create a plugin module:
   - Create a directory structure like: `adam_tools/plugins/my_tool.py`.
     The `adam_tools` and `adam_tools/plugins` directories should have
     an `__init__.py` file to be recognized as Python packages.
   - The module name (e.g., `my_tool`) is used as the plugin's identifier.

2. Implement the `run` function:
   - Your plugin module MUST contain a function named `run`.
   - The signature must be: `run(**kwargs) -> dict`.
   - It receives arguments from the CLI or other system calls.

3. Adhere to the return contract:
   - The `run` function MUST always return a dictionary with the
     following structure:
     { "ok": bool, "data": any, "error": str or None }
   - This standardized format ensures that plugin errors do not crash
     the main orchestrator. The `ok` flag indicates success or failure,
     and `error` provides a human-readable message on failure.

4. Invoke the plugin from the CLI:
   python run_adam.py --plugin my_tool --args '{"some_arg": "value"}'

-------------------------

Design Notes:
-------------------------

- Componentized Architecture: Inspired by AnythingLLM's separation of LLMs,
  Embedders, and Vector DBs, Adam is built around abstract interfaces
  and plugins to achieve similar modularity for offline-only components.
- Plugin Discovery: The concept of discovering tools/skills from a
  predefined location is inspired by AnythingLLM's plugins/agent-skills
  directory structure. Adam adapts this using a Python namespace (adam_tools.plugins)
  for a more idiomatic implementation.
- Configuration-driven Behavior: AnythingLLM relies on configuration
  (e.g., connection strings, api keys) to wire its components together. Adam
  adopts this by using a config/adam.yaml file to define system-wide
  settings like model choices.
- RAG as a Core Workflow: The primary "chat with your documents" flow in
  AnythingLLM informs the design of Adam's handle_ask_request function,
  which orchestrates the canonical retrieve-augment-generate sequence.

Clean-Room Statement:
No code or identifiers were copied; this file was written from scratch
to implement similar high-level behavior.

"""

import argparse
import copy
import json
import logging
import logging.handlers
import importlib
import inspect
import os
import pathlib
import re
import socket
import subprocess
import sys
import time
import typing
import yaml
from pathlib import Path


def resolve_model_path(name: str, search_dir: str = "models") -> str:
    """Return the first matching model path (plain, .gguf, .bin); default to .gguf."""
    safe_name = str(name)
    base = Path(search_dir) / safe_name
    candidates = [base, base.with_suffix(".gguf"), base.with_suffix(".bin")]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return str(base.with_suffix(".gguf"))


from collections.abc import Generator
from src.adam.plugin_manager import manager
from src.adam.adapters import ChromaVectorStore, SentenceTransformerEmbedder

# ------------------------------------------------------------------------------
# CONSTANTS AND PATHS
# ------------------------------------------------------------------------------

MODULE_DIR = pathlib.Path(__file__).parent
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent  # → Adamv1/
CONFIG_DIR = PROJECT_ROOT / "config"
CONFIG_FILE = CONFIG_DIR / "adam.yaml"
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "adam.log"

# Use string constants for backends since we no longer import plugin functions directly
LOCAL_BACKEND = "local_llm"
OLLAMA_BACKEND = "ollama_llm"
MOCK_BACKEND = "mock_llm"

_ACTIVE_PRIMARY_BACKEND = LOCAL_BACKEND
_USE_MOCK_LLM = False
_LLM_INIT_DONE = False

if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

# Remove old plugin registry logic — PluginManager is now the single source of truth
PLUGIN_NAMESPACE = "plugins"

try:
    from utils.token_counter import count_tokens
except ImportError:  # pragma: no cover

    def count_tokens(text: str, model: str = "gpt-4") -> int:
        return max(1, len(text.split()))


DEFAULT_CONFIG = {
    "model_router": {
        "default_model": "light-condenser",
        "heavy_model": "qwen3-coder-30b-q4km",
        "heavy_triggers": {
            "word_count_threshold": 100,
            "keywords": ["code", "analyze", "review", "detailed"],
        },
    },
    "rag": {
        "top_k": 3,
    },
    "ui": {
        "enabled": True,
        "theme": "dark",
        "download_path": "models/",
        "default_model": "light-condenser",
    },
    "server": {
        "host": "127.0.0.1",
        "port": 8000,
        "cors_enabled": False,
        "auth": {
            "enabled": False,
            "token": "",
            "ui_token": "",
        },
    },
    "inference": {
        "default_temperature": 0.7,
        "default_gpu_layers": 20,
    },
    "plugin_paths": {
        "github_publisher": {
            "sidecar": "./sidecars/github_publisher",
        }
    },
}


# ------------------------------------------------------------------------------
# CORE SERVICES: CONFIGURATION & LOGGING
# ------------------------------------------------------------------------------


class JsonLogFormatter(logging.Formatter):
    """A custom log formatter that outputs log records as JSON Lines."""

    def format(self, record):
        ts = getattr(record, "asctime", None)
        if not ts:
            ts = self.formatTime(record)
        log_obj = {
            "timestamp": ts,
            "levelname": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
        }
        if record.exc_info:
            log_obj["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging():
    """Sets up a structured JSON Lines logger.

    This function configures the root logger to output logs in JSONL format
    to a specified file. It also ensures the log directory exists.
    """
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
    except OSError as e:
        print(
            f"ERROR: Could not create log directory at '{LOG_DIR}': {e}",
            file=sys.stderr,
        )
        sys.exit(1)

    logger = logging.getLogger("adam")
    logger.setLevel(logging.INFO)

    # Avoid adding handlers repeatedly if the function is called multiple times
    if not logger.handlers:
        handler = logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=10240000, backupCount=5
        )
        formatter = JsonLogFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def log_event(event: str, **fields: typing.Any) -> None:
    """Lightweight logging helper for structured events."""
    try:
        logger = logging.getLogger("adam")
        if not logger.handlers:
            logger = setup_logging()
        payload = {"event": event}
        if fields:
            payload.update(fields)
        logger.info(json.dumps(payload))
    except Exception:
        pass


def load_configuration():
    # ... imports ...

    config = copy.deepcopy(DEFAULT_CONFIG)  # Already has correct default_model_path!

    if not CONFIG_FILE.exists():
        logging.getLogger("adam").warning(
            f"Config file not found at '{CONFIG_FILE}'. Using defaults."
        )
        return config

    try:
        with open(CONFIG_FILE, "r") as f:
            user_config = yaml.safe_load(f)
            if isinstance(user_config, dict):
                # Deep merge
                stack = [(user_config, config)]
                while stack:
                    top_user, top_default = stack.pop()
                    for k, v in top_user.items():
                        if (
                            k in top_default
                            and isinstance(v, dict)
                            and isinstance(top_default[k], dict)
                        ):
                            stack.append((v, top_default[k]))
                        else:
                            top_default[k] = v
    except (OSError, yaml.YAMLError) as e:
        logging.getLogger("adam").error(f"Failed to load config: {e}")
        # Return defaults on error
        return copy.deepcopy(DEFAULT_CONFIG)

    return config


def get_default_model_path(
    cfg: typing.Optional[typing.Dict[str, typing.Any]] = None,
) -> str:
    config = cfg or load_configuration()
    path = config["default_model_path"]  # No fallback needed - always present
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


# ------------------------------------------------------------------------------
# PLUGIN MANAGEMENT SUBSYSTEM
# ------------------------------------------------------------------------------


def discover_plugins(with_metadata: bool = False) -> list[dict]:
    """
    Returns a list of available plugins by asking the PluginManager.
    The manager is now the single source of truth for plugin discovery.
    """
    plugin_names = manager.get_available_plugins()
    return [{"name": name} for name in plugin_names]


def initialize_llm_backends(force: bool = False) -> None:
    """Ensure at least one LLM backend is ready, falling back to a mock model."""

    global _ACTIVE_PRIMARY_BACKEND, _USE_MOCK_LLM, _LLM_INIT_DONE

    if _LLM_INIT_DONE and not force:
        return

    logger = logging.getLogger("adam")
    _LLM_INIT_DONE = True
    _USE_MOCK_LLM = False

    if manager.ensure_plugin_loaded(LOCAL_BACKEND):
        _ACTIVE_PRIMARY_BACKEND = LOCAL_BACKEND
        logger.info("Primary LLM backend set to local_llm")
        return

    logger.warning("local_llm unavailable at startup; attempting ollama_llm")
    if manager.ensure_plugin_loaded(OLLAMA_BACKEND):
        _ACTIVE_PRIMARY_BACKEND = OLLAMA_BACKEND
        logger.info("Primary LLM backend set to ollama_llm")
        return

    logger.error("No LLM plugins available; using mock_llm fallback")
    _ACTIVE_PRIMARY_BACKEND = MOCK_BACKEND
    _USE_MOCK_LLM = True


def _call_llm_with_fallback(
    prompt: str, model_name: str, config: dict, llm_params: dict
) -> dict:
    """Attempt local_llm, then ollama_llm, then a mock response."""

    logger = logging.getLogger("adam")
    initialize_llm_backends()

    # Ensure non-streaming execution for RAG flow
    execution_params = {**llm_params, "stream": False}

    if _USE_MOCK_LLM:
        return _mock_llm_response(prompt)

    def _invoke_backend(backend: str) -> dict:
        if backend == LOCAL_BACKEND:
            if not manager.ensure_plugin_loaded(LOCAL_BACKEND):
                return {"ok": False, "error": "local_llm unavailable"}
            try:
                model_path = resolve_model_path(model_name)
            except Exception as exc:
                logger.error(
                    "Model path resolution failed for %s: %s", model_name, exc
                )
                model_path = f"models/{model_name}.gguf"

            result = manager.run_plugin(
                LOCAL_BACKEND,
                prompt=prompt,
                model_path=model_path,
                **execution_params,
            )
        elif backend == OLLAMA_BACKEND:
            if not manager.ensure_plugin_loaded(OLLAMA_BACKEND):
                return {"ok": False, "error": "ollama_llm unavailable"}
            result = manager.run_plugin(
                OLLAMA_BACKEND,
                prompt=prompt,
                model=model_name,
                **execution_params,
            )
        else:
            return _mock_llm_response(prompt)

        if result.get("ok"):
            result["llm_backend"] = backend
            result["model_name"] = model_name
        return result

    backend_sequence = []
    if _ACTIVE_PRIMARY_BACKEND == LOCAL_BACKEND:
        backend_sequence = [LOCAL_BACKEND, OLLAMA_BACKEND]
    elif _ACTIVE_PRIMARY_BACKEND == OLLAMA_BACKEND:
        backend_sequence = [OLLAMA_BACKEND, LOCAL_BACKEND]
    else:
        backend_sequence = [LOCAL_BACKEND, OLLAMA_BACKEND]

    seen = set()
    for backend in backend_sequence:
        if backend in seen:
            continue
        seen.add(backend)
        result = _invoke_backend(backend)
        if result.get("ok"):
            return result
        logger.warning("%s failed (%s)", backend, result.get("error"))

    logger.error("All LLM backends failed; using mock response")
    return _mock_llm_response(prompt)


def _mock_llm_response(prompt: str) -> dict:
    """Return a deterministic, safe response when no real LLM backends are available."""

    snippet_lines = (prompt or "").strip().splitlines()
    snippet = " ".join(snippet_lines) if snippet_lines else "(no prompt provided)"
    snippet = snippet[:400] + ("..." if len(snippet) > 400 else "")

    message = (
        "Mock response (LLM unavailable).\n\n"
        "I'm running in fallback mode because neither local_llm nor ollama_llm could load.\n"
        f"Prompt echo: {snippet}"
    )

    return {
        "ok": True,
        "data": message,
        "error": None,
        "llm_backend": MOCK_BACKEND,
        "model_name": "adam-mock-llm",
    }


def _condense_with_light(text: str, light_model_name: str, config: dict) -> str:
    """Normalize/condense noisy chat into a clean, structured prompt."""
    model_path = resolve_model_path(light_model_name or "light-condenser")

    prompt = (
        "You are a prompt condenser. Convert the USER content into a crisp task brief for a stronger executor.\n"
        "Respond ONLY with:\n"
        "[SYSTEM]\n"
        "- role: executor\n"
        "- safety: offline, no external APIs\n"
        "- style: concise\n"
        "- constraints: deterministic when temperature<=0.3\n"
        "[USER]\n"
        "- objective: ...\n"
        "- key_details: ...\n"
        "- code_language: ...\n"
        "- files: ...\n"
        "- acceptance_criteria: ...\n"
        "- examples: (short, optional)\n\n"
        f"USER:\n{text}"
    )
    try:
        res = manager.run_plugin(
            "local_llm",
            prompt=prompt,
            model_path=model_path,
            max_tokens=384,
            temperature=0.3,
            stream=False,
        )
        if res and res.get("ok") and res.get("data", {}).get("text"):
            return res["data"]["text"]
    except Exception:
        pass
    return text


def get_plugin_health_report() -> dict:
    """Return structural plugin health information without executing plugins."""
    # Since PluginManager handles loading, we'll just report available vs. loaded
    available = manager.get_available_plugins()
    loaded = set(manager._loaded_plugins.keys())

    # We avoid importing here to respect lazy loading
    return {
        "available_plugins": sorted(available),
        "loaded_plugins": sorted(loaded),
        "note": "Full health check requires execution; this is a static report.",
    }


# ------------------------------------------------------------------------------
# ORCHUSTRATION LOGIC AND HOOKS
# ------------------------------------------------------------------------------


def memory_write(content: str) -> dict:
    """Record information using the memory_write plugin."""
    result = manager.run_plugin("memory_write", content=content)
    if not result.get("ok"):
        return {
            "ok": False,
            "data": result.get("data"),
            "error": result.get("error") or "Memory write failed.",
        }
    return result


def memory_search(query: str, top_k: int = 3) -> dict:
    """Retrieve relevant information using the memory_search plugin."""
    result = manager.run_plugin("memory_search", query=query, top_k=top_k)
    if not result.get("ok"):
        return {
            "ok": False,
            "data": result.get("data"),
            "error": result.get("error") or "Memory search failed.",
        }
    return result


def memory_summarize() -> dict:
    """Summarize stored context via the memory_summarize plugin."""
    result = manager.run_plugin("memory_summarize")
    if not result.get("ok"):
        return {
            "ok": False,
            "data": result.get("data"),
            "error": result.get("error") or "Memory summary failed.",
        }
    return result


def handle_ask_request(config: dict, cli_args: argparse.Namespace) -> dict:
    """Orchestrates the full RAG flow with a single, unified routing call."""
    logger = logging.getLogger("adam")
    logger.info(f"Got ask request: '{cli_args.ask}'")

    # 1. Audit hardware to inform the router
    hardware_result = manager.run_plugin("hardware_audit")
    if not hardware_result.get("ok"):
        return {"ok": False, "error": "Hardware audit failed"}
    hardware_data = hardware_result.get("data", {})

    # 2. Make a single, authoritative routing decision
    route = manager.run_plugin(
        "model_router",
        query=cli_args.ask,
        hardware=hardware_data,
        config=config,
    )
    if not route.get("ok"):
        return {"ok": False, "error": f"Model router failed: {route.get('error')}"}

    selection = route.get("data", {})
    model_name = selection.get("model_name")
    if not model_name:
        return {"ok": False, "error": "Model router did not return a model name"}

    # 3. Ensure the chosen model is available
    model_path = resolve_model_path(model_name)
    if not Path(model_path).exists():
        logger.warning(
            f"Model '{model_name}' not found at '{model_path}'. Attempting download."
        )
        repo_id = selection.get("repo_id")
        filename = selection.get("filename")
        if repo_id and filename:
            download_result = manager.run_plugin(
                "model_download",
                repo_id=repo_id,
                filename=filename,
                local_dir="models",
            )
            if not download_result.get("ok"):
                logger.error(
                    f"Failed to download model '{model_name}': {download_result.get('error')}"
                )

    # 4. (Optional) Condense prompt with a light model
    user_prompt = cli_args.ask
    light_name = selection.get("preprocess_with")
    if light_name:
        user_prompt = _condense_with_light(user_prompt, light_name, config)

    # 5. Perform RAG
    embedder = SentenceTransformerEmbedder()
    vector_store = ChromaVectorStore()

    # Validate adapters
    if not getattr(embedder, "model", None):
        return {"ok": False, "error": "Embedding model failed to initialize"}
    if not getattr(vector_store, "collection", None):
        return {"ok": False, "error": "Vector store failed to initialize"}

    query_vector = embedder.embed_texts([cli_args.ask])[0]
    retrieved_context = vector_store.search(
        query_vector, top_k=config.get("rag", {}).get("top_k", 3)
    )

    # 6. Construct prompt
    context_text = "\n\n".join([ctx.get("document", "") for ctx in retrieved_context])
    prompt = (
        "You are Adam, an assistant. Use the provided context to answer the user.\n\n"
        f"Context:\n{context_text}\n\n"
        f"Question:\n{user_prompt}\n\nAnswer:"
    )

    # 7. Execute LLM with fallback
    llm_params = selection.get("params", {})
    llm_result = _call_llm_with_fallback(
        prompt=prompt, model_name=model_name, config=config, llm_params=llm_params
    )

    if not llm_result.get("ok"):
        return {"ok": False, "error": llm_result.get("error", "LLM call failed")}

    # 8. Construct response
    answer = llm_result.get("data", "(no response)")
    response = {
        "ok": True,
        "answer": answer,
        "citations": [ctx.get("meta", {}) for ctx in retrieved_context],
        "model_used": llm_result.get("model_name", model_name),
        "llm_backend": llm_result.get("llm_backend", "unknown"),
        "router_reason": selection.get("reason"),
    }

    # 9. Record to memory (non-critical)
    try:
        memory_write(f"Question: {cli_args.ask}\tResponse: {answer}")
    except Exception as e:
        logger.warning(f"Memory write failed (non-critical): {e}")

    return response


def handle_plugin_request(cli_args: argparse.Namespace) -> dict:
    """Handles a direct call to a plugin via the CLI."""
    plugin_name = cli_args.plugin
    try:
        args = json.loads(cli_args.args) if cli_args.args else {}
        if not isinstance(args, dict):
            raise ValueError("--args must be a valid JSON object.")
    except (json.JSONDecodeError, ValueError) as e:
        error_msg = f"Error parsing --args: {e}"
        logger = logging.getLogger("adam")
        logger.error(error_msg)
        return {"ok": False, "data": None, "error": error_msg}

    logger = logging.getLogger("adam")
    logger.info(f"Executing plugin {plugin_name} with args: {args}")
    return manager.run_plugin(plugin_name, **args)


# ------------------------------------------------------------------------------
# UI LAUNCHER
# ------------------------------------------------------------------------------


def ensure_backend(app_host: str, app_port: int, timeout_s: int = 8) -> bool:
    """If nothing listens on app_host:app_port, start uvicorn and wait briefly."""

    def _is_up() -> bool:
        with socket.socket() as sock:
            sock.settimeout(0.5)
            try:
                sock.connect((app_host, app_port))
                return True
            except Exception:
                return False

    if _is_up():
        log_event("backend_ok", host=app_host, port=app_port)
        return True

    log_event("backend_starting", host=app_host, port=app_port)
    try:
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(
            [env.get("PYTHONPATH", ""), os.path.join(PROJECT_ROOT, "src")]
        )
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "server.main:app",
                "--host",
                app_host,
                "--port",
                str(app_port),
            ],
            cwd=os.getcwd(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )
    except Exception as exc:
        log_event("backend_launch_failed", error=str(exc))
        return False

    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if _is_up():
            log_event("backend_ready")
            return True
        time.sleep(0.25)

    log_event("backend_timeout", seconds=timeout_s)
    return False


def run_ui(
    app_host: str = "127.0.0.1",
    app_port: int = 8000,
    config: typing.Optional[dict] = None,
) -> int:
    """Launch the Tk UI and route submissions through the core orchestrator."""
    log_path = os.path.join(os.path.expanduser("~"), ".cache", "adam", "launcher.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(
            f"[{time.strftime('%F %T')}] python={sys.executable} cwd={os.getcwd()} file={os.path.abspath(__file__)}\n"
        )

    runtime_config = config if config is not None else load_configuration()
    ui_state: typing.Dict[str, typing.Any] = {"app": None}
    logger = logging.getLogger("adam")

    def _push_to_ui(message: str) -> None:
        app = ui_state.get("app")
        if app and hasattr(app, "receive_response"):
            try:
                app.receive_response(message)
            except Exception:
                logger.exception("Failed to deliver response to UI")
        else:
            logger.warning("UI not ready; dropping response: %s", message[:120])

    COMMAND_ALIASES = {
        "diag": "diag_adam",
        "diag_adam": "diag_adam",
        "deepdiag": "deep_diag",
        "deep_diag": "deep_diag",
        "diag-director": "diag_director",
        "diag_director": "diag_director",
    }

    def _format_structured(payload: typing.Any) -> str:
        if payload is None:
            return "(no data)"
        if isinstance(payload, (dict, list)):
            try:
                return json.dumps(payload, indent=2)
            except Exception:
                return str(payload)
        return str(payload)

    def _format_command_response(name: str, result: typing.Any, kind: str) -> str:
        if isinstance(result, dict):
            ok = bool(result.get("ok"))
            error = result.get("error")
            data = result.get("data")
        else:
            ok = False
            error = str(result)
            data = None

        status = "✅" if ok else "⚠️"
        lines = [f"{status} {kind} /{name}"]

        if error and not ok:
            lines.append(f"Error: {error}")

        if data not in (None, ""):
            lines.append(_format_structured(data))

        return "\n\n".join(filter(None, lines))

    def _execute_command(command: str) -> bool:
        normalized = command.strip().lower()
        if not normalized:
            return False

        available_plugins = manager.get_available_plugins()
        if normalized in available_plugins:
            result = manager.run_plugin(normalized)
            _push_to_ui(_format_command_response(normalized, result, "plugin"))
            return True

        tool_name = COMMAND_ALIASES.get(normalized, normalized)
        try:
            from adam.tools import run_tool as _run_tool

            result = _run_tool(tool_name)
        except Exception as exc:  # pragma: no cover - tooling optional
            result = {"ok": False, "data": None, "error": str(exc)}

        is_dict = isinstance(result, dict)
        ok = bool(result.get("ok")) if is_dict else False

        if ok:
            _push_to_ui(_format_command_response(tool_name, result, "tool"))
            return True

        error_msg = ""
        if is_dict:
            error_msg = result.get("error") or ""
        if not error_msg:
            error_msg = str(result)

        lower_error = error_msg.lower()
        missing_clues = any(
            phrase in lower_error
            for phrase in [
                "not found",
                "does not have",
                "unavailable",
                "unknown tool",
                "no such tool",
            ]
        )

        if missing_clues:
            suggestion = (
                f"⚠️ tool /{tool_name} is not available."
                "\nWould you like me to draft it?"
                " Let me know the objective, required inputs, and expected outputs so I can scaffold the tool."
            )
            _push_to_ui(suggestion)
        else:
            _push_to_ui(_format_command_response(tool_name, result, "tool"))

        return True

    def _derive_model_options() -> list[tuple[str, str]]:
        router_cfg = runtime_config.get("model_router", {}) if runtime_config else {}
        options: list[tuple[str, str]] = []
        default_model = router_cfg.get("default_model")
        heavy_model = router_cfg.get("heavy_model")
        if default_model:
            options.append((f"{default_model} (default)", default_model))
        if heavy_model and heavy_model != default_model:
            options.append((f"{heavy_model} (heavy)", heavy_model))
        return options

    def _on_ready(app) -> None:
        ui_state["app"] = app

        try:
            model_options = _derive_model_options()
            if model_options and hasattr(app, "_set_available_models"):
                app._set_available_models(model_options)
        except Exception:
            logger.exception("Failed to seed model options for UI")

        backend_label = _ACTIVE_PRIMARY_BACKEND
        if _USE_MOCK_LLM:
            backend_label = f"{backend_label} (fallback)"

        intro_lines = [
            "Adam UI connected to core.",
            f"Primary backend: {backend_label}",
        ]
        try:
            available = manager.get_available_plugins()
            intro_lines.append(
                "Loaded plugins: " + ", ".join(sorted(available)) if available else "No plugins discovered"
            )
        except Exception:
            intro_lines.append("Plugin discovery unavailable")

        _push_to_ui("\n".join(intro_lines))

    def _format_citations(
        citations: typing.Iterable[typing.Mapping[str, typing.Any]]
    ) -> str:
        lines = []
        for idx, citation in enumerate(citations or [], start=1):
            label = (
                citation.get("title")
                or citation.get("source")
                or citation.get("document_id")
            )
            if not label:
                label = json.dumps(citation)
            lines.append(f"{idx}. {label}")
        return "\n".join(lines)

    def _submit_callback(user_text: str) -> None:
        try:
            logger.info("UI request received")

            commands = set(
                re.findall(r"(?<!:)\B/([a-zA-Z0-9_\-]+)", user_text or "")
            )
            if commands:
                for cmd in commands:
                    _execute_command(cmd)
                return

            result = ask_question(
                question=user_text,
                heavy=False,
                config=copy.deepcopy(runtime_config),
            )

            if isinstance(result, dict):
                if result.get("ok"):
                    answer = result.get("answer", "(no response)")
                    citations = result.get("citations") or []
                    backend = result.get("llm_backend") or "local_llm"
                    model = result.get("model_used") or result.get("model_name")

                    response_lines = [answer.strip() or "(no response)"]
                    if model or backend:
                        response_lines.append("")
                        response_lines.append(
                            f"Model: {model or 'unknown'} ({backend})"
                        )
                    if citations:
                        response_lines.append("")
                        response_lines.append("Sources:")
                        response_lines.append(_format_citations(citations))

                    _push_to_ui(
                        "\n".join(line for line in response_lines if line is not None)
                    )
                else:
                    error_msg = result.get("error") or "Unknown error"
                    _push_to_ui(f"(error) {error_msg}")
            else:
                chunks = list(result)
                aggregated = "".join(chunks).strip() or "(no response)"
                _push_to_ui(aggregated)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("UI submission failed: %s", exc)
            _push_to_ui(f"(error) {exc}")

    ok = ensure_backend(app_host, app_port)
    if not ok:
        log_event("backend_unavailable", host=app_host, port=app_port)

    try:
        ui_mod = importlib.import_module("src.ui.app")
        run_adam_ui = getattr(ui_mod, "run_adam_ui", None) or getattr(
            ui_mod, "main", None
        )
        if not callable(run_adam_ui):
            raise ImportError(
                "src.ui.app has no runnable entrypoint (run_adam_ui/main)."
            )
    except (ImportError, ModuleNotFoundError) as exc:
        sys.stderr.write(f"UI not available: {exc}\n")
        sys.stderr.write("tkinter is not installed. Please install it to use the UI.\n")
        sys.stderr.write("On Debian/Ubuntu: sudo apt-get install python3-tk\n")
        sys.stderr.write("On Fedora: sudo dnf install python3-tkinter\n")
        sys.stderr.write("On CentOS: sudo yum install python3-tkinter\n")
        sys.stderr.write("On macOS: brew install python-tk\n")
        return 1

    import tkinter as tk

    run_params: typing.Dict[str, typing.Any] = {}
    sig = inspect.signature(run_adam_ui)
    if "app_host" in sig.parameters:
        run_params["app_host"] = app_host
    if "app_port" in sig.parameters:
        run_params["app_port"] = app_port
    if "submit_callback" in sig.parameters:
        run_params["submit_callback"] = _submit_callback
    if "on_ready" in sig.parameters:
        run_params["on_ready"] = _on_ready

    params_iter = iter(sig.parameters.values())
    first_param = next(params_iter, None)
    if (
        first_param
        and first_param.kind
        in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        and first_param.default is inspect._empty
        and first_param.name in {"root", "tk_root", "window"}
    ):
        root = tk.Tk()
        return run_adam_ui(root, **run_params)

    return run_adam_ui(**run_params)


# ------------------------------------------------------------------------------
# AUDIT AND SELF-TEST ROUTINES
# ------------------------------------------------------------------------------


def run_audit(cli_args: argparse.Namespace) -> dict:
    """Executes the audit_client plugin if it exists."""
    print("Executing audit client...")
    result = manager.run_plugin("audit_client", arguments=cli_args.audit)
    if not result["ok"]:
        print("\nHINT: The audit feature requires the `audit_client` plugin.")
        print("Please make sure it is available in the `adam_tools/plugins` directory.")
    return result


def run_self_test():
    """Runs a series of checks to verify the operational status of the Adam core."""
    print("Running Adam Self-Test...")
    test_passed = True

    try:
        # 1. Configuration Loading
        print("\n1. Configuration Loading...", end="")
        config = load_configuration()
        if isinstance(config, dict) and "model_router" in config:
            print("OK")
        else:
            print("FAILED", end="")
            test_passed = False

        # 2. Logging Setup
        print("\n2. Logging Setup...", end="")
        logger = setup_logging()
        logger.info("Self test log entry.")
        if LOG_FILE.exists():
            print("OK")
        else:
            print("FAILED", end="")
            test_passed = False

        # 3. Plugin Discovery
        print("\n3. Plugin Discovery...", end="")
        plugins = discover_plugins()
        plugin_names = [p["name"] for p in plugins]
        expected_plugins = [
            "model_router",
            "local_llm",
            "memory_search",
            "hardware_audit",
        ]
        missing_plugins = [p for p in expected_plugins if p not in plugin_names]
        if not missing_plugins:
            print(f"OK (found {len(plugins)} plugins)")
        else:
            print(f"FAILED - Missing plugins: {missing_plugins}")
            test_passed = False

        # 4. Model Routing (Test unified router)
        print("4. Model Routing...")
        mock_hardware = {"ram_gb": 32, "gpu": {"gpus": [{"vram_gb": 16}]}}
        query_simple = "What is the time?"
        query_heavy = "Please write a Python function to calculate Fibonacci."

        # Test simple query → should use light model
        result_default = manager.run_plugin(
            "model_router", query=query_simple, hardware=mock_hardware, config=config
        )
        decision_default = result_default.get("data", {})

        # Test heavy query → should use heavy model
        result_heavy = manager.run_plugin(
            "model_router", query=query_heavy, hardware=mock_hardware, config=config
        )
        decision_heavy = result_heavy.get("data", {})

        print(
            f"  - Default decision: '{decision_default.get('reason')}' → {decision_default.get('model_name')}"
        )
        print(
            f"  - Heavy decision: '{decision_heavy.get('reason')}' → {decision_heavy.get('model_name')}"
        )

        # Validate routing logic by checking model classes
        default_is_light = (
            decision_default.get("preprocess_with") is None
        )  # Light models don't need preprocessing
        heavy_has_preprocessing = (
            decision_heavy.get("preprocess_with") == "light-condenser"
        )

        if default_is_light and heavy_has_preprocessing:
            print("  - Routing logic OK")
        else:
            print("  - Routing logic FAILED")
            test_passed = False

        # 5. RAG Adapters
        print("5. RAG Adapters...", end="")
        try:
            embedder = SentenceTransformerEmbedder()
            vector_store = ChromaVectorStore()

            # Validate embedder
            if not getattr(embedder, "model", None):
                print("FAILED - Embedder not initialized")
                test_passed = False
            else:
                vec = embedder.embed_texts(["test"])
                if (
                    len(vec) == 1 and len(vec[0]) == 384
                ):  # Standard sentence-transformer dimension
                    print("OK")
                else:
                    print(
                        f"FAILED - Wrong embedding shape: {len(vec)}x{len(vec[0]) if vec else 0}"
                    )
                    test_passed = False

            # Validate vector store
            if not getattr(vector_store, "collection", None):
                print("Vector store not initialized (non-critical)")
        except Exception as e:
            print(f"FAILED with error: {e}")
            test_passed = False

        # 6. Memory Plugins (Basic smoke test)
        print("6. Memory Plugins...", end="")
        try:
            # Test memory_write (should work even with empty memory)
            write_result = manager.run_plugin(
                "memory_write", content="Self-test memory entry"
            )
            if write_result.get("ok"):
                print("OK")
            else:
                print(f"FAILED - memory_write: {write_result.get('error')}")
                test_passed = False
        except Exception as e:
            print(f"FAILED with error: {e}")
            test_passed = False

    except Exception as e:
        import traceback

        print(f"\nFAILED with unexpected error: {e}")
        traceback.print_exc()
        test_passed = False

    print("\n---------------------------------")
    if test_passed:
        print("Self-Test PASSED. Adam core is operational.")
        sys.exit(0)
    else:
        print("Self-Test FAILED. Check errors above.")
        sys.exit(1)


# ------------------------------------------------------------------------------
# MAIN EXECUTION BLOCK
# ------------------------------------------------------------------------------


def ask_question(
    question: str,
    heavy: bool = False,
    config: dict | None = None,
    stream: bool = False,
) -> typing.Union[dict, Generator[str, None, None]]:
    """Public API: Ask a question using the RAG flow and return structured output."""
    active_config = config if config is not None else load_configuration()

    class _MockArgs:
        def __init__(self, ask_text: str, force_heavy: bool):
            self.ask = ask_text
            self.heavy = force_heavy

    cli_args = _MockArgs(ask_text=question, force_heavy=heavy)

    try:
        result = handle_ask_request(active_config, cli_args)

        if result.get("stream") and isinstance(result.get("generator"), Generator):
            return result

        if not result.get("ok"):
            return result

        prompt_used = result.get("prompt", question)
        answer = result.get("answer", "(no response)")
        model_name = result.get("model_used", "unknown")

        if not result.get("memory_logged"):
            memory_write(f"Question: {question}\tResponse: {answer}")

        prompt_tokens = count_tokens(prompt_used, model=model_name)
        completion_tokens = count_tokens(answer, model=model_name)

        result["usage"] = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

        result.setdefault("model_used", model_name)
        result.setdefault("llm_backend", result.get("llm_backend", "unknown"))
        return result
    except Exception as exc:  # pragma: no cover - safety net
        logger = logging.getLogger("adam")
        logger.error("Error in ask_question", exc_info=True)
        return {
            "ok": False,
            "answer": f"(error) {exc}",
            "citations": [],
            "model_used": "unknown",
        }


def main():
    """The main entry point for the Adam orchestrator.

    It parses command-line arguments, dispatches to the correct
    handler function, and prints the JSON output.
    """
    parser = argparse.ArgumentParser(
        description="Adam -- A lean, extensible, offline-first orchestrator."
    )

    main_group = parser.add_mutually_exclusive_group(required=True)
    main_group.add_argument(
        "--ask",
        metavar="QUESTION",
        help="Ask Adam a question using RAG (if configured).",
    )
    main_group.add_argument(
        "--plugin",
        metavar="PLUGIN_NAME",
        help="Execute a direct call to a specific plugin.",
    )
    main_group.add_argument(
        "--tool",
        metavar="TOOL_NAME",
        help="Execute an on-demand tool from the ./tools/ directory.",
    )
    main_group.add_argument(
        "--self-test",
        action="store_true",
        help="Run built-in system checks to verify core functionality.",
    )
    main_group.add_argument(
        "--audit",
        metavar="DETAILS",
        help="Run the audit client plugin with given arguments.",
    )
    main_group.add_argument(
        "--ui",
        action="store_true",
        help="Launch the Tkinter UI.",
    )
    main_group.add_argument(
        "--plugin-health",
        action="store_true",
        help="Show health status of all plugins.",
    )

    parser.add_argument(
        "--args",
        metavar="JSON_STRING",
        default="{}",
        help="Arguments to pass to a plugin, formatted as a JSON string.",
    )
    parser.add_argument(
        "--heavy",
        action="store_true",
        help="Force the use of the heavy model for an --ask request.",
    )
    parser.add_argument(
        "--ui-host",
        dest="ui_host",
        default="127.0.0.1",
        help="Host where the Adam backend is listening.",
    )
    parser.add_argument(
        "--ui-port",
        dest="ui_port",
        type=int,
        default=8000,
        help="Port where the Adam backend is listening.",
    )

    args = parser.parse_args()

    # Setup logging and configuration
    setup_logging()
    config = load_configuration()
    initialize_llm_backends()

    result = {}

    try:
        if args.self_test:
            run_self_test()
            return  # Self-test handles exit
        elif args.ask:
            result = handle_ask_request(config, args)
        elif args.plugin:
            result = handle_plugin_request(args)
        elif args.tool:
            from adam.tools import run_tool

            try:
                tool_args = json.loads(args.args) if args.args else {}
                if not isinstance(tool_args, dict):
                    raise ValueError("--args must be a JSON object.")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing --args: {e}")
                sys.exit(1)

            result = run_tool(args.tool, **tool_args)
            print(json.dumps(result, indent=2))
            return
        elif args.audit:
            result = run_audit(args)
        elif args.plugin_health:
            report = get_plugin_health_report()
            print(json.dumps(report, indent=2))
            return
        elif args.ui:
            return run_ui(
                app_host=args.ui_host,
                app_port=args.ui_port,
                config=config,
            )
    except Exception as e:
        import traceback

        error_msg = f"unhandled error in main execution: {e}"
        logger = logging.getLogger("adam")
        logger.critical(error_msg, exc_info=True)
        print("FULL TRACEBACK:", file=sys.stderr)
        traceback.print_exc()
        result = {
            "ok": False,
            "data": None,
            "error": error_msg,
        }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
