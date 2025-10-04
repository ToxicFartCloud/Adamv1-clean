import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Generator
import urllib.request
import urllib.error
import urllib.parse

METADATA = {
    "label": "Ollama LLM",
    "description": "Generates responses using local Ollama server.",
    "ui_action": False,
    "executable": True,
}

logger = logging.getLogger("adam")
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "ollama_llm.log"


def _call_ollama(prompt: str, model: str, stream: bool = False) -> Any:
    """Call Ollama API. Returns dict (non-stream) or generator (stream)."""
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
        },
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            if stream:
                return _stream_response(response)
            else:
                raw = response.read().decode("utf-8")
                lines = [json.loads(line) for line in raw.splitlines() if line.strip()]
                final_response = "".join(line.get("response", "") for line in lines)
                return final_response
    except Exception as e:
        raise RuntimeError(f"Ollama API call failed: {e}") from e


def _stream_response(response) -> Generator[str, None, None]:
    """Yield tokens from streaming Ollama response."""
    for line in response:
        if not line.strip():
            continue
        try:
            chunk = json.loads(line)
            token = chunk.get("response", "")
            if token:
                yield token
        except json.JSONDecodeError:
            continue


def _log_call(
    prompt: str, model: str, stream: bool, response_preview: str, latency_ms: int
):
    """Log structured entry to ollama_llm.log."""
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model": model,
        "stream": stream,
        "prompt_length": len(prompt),
        "response_preview": response_preview[:100] + "..."
        if len(response_preview) > 100
        else response_preview,
        "latency_ms": latency_ms,
    }

    LOG_DIR.mkdir(exist_ok=True)

    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("Failed to write ollama_llm log: %s", exc)


def run(**kwargs) -> Dict[str, Any]:
    """
    Generate response using Ollama.

    Expected kwargs:
        - prompt: str
        - model: str
        - stream: bool (default: False)

    Returns:
        Non-stream: { "ok": bool, "data": str, "error": str or None }
        Stream:     { "ok": bool, "stream": True, "generator": Generator, "error": str or None }
    """
    prompt = kwargs.get("prompt", "")
    model = kwargs.get("model", "unknown")
    stream = kwargs.get("stream", False)

    if not isinstance(prompt, str):
        return {"ok": False, "data": None, "error": "'prompt' must be a string."}

    if not isinstance(model, str):
        return {"ok": False, "data": None, "error": "'model' must be a string."}

    start_time = time.time()

    try:
        # ➤ Try real Ollama first
        result = _call_ollama(prompt, model, stream)

        latency_ms = int((time.time() - start_time) * 1000)

        if stream:
            # Wrap generator to log on completion
            def logged_generator():
                full_response = ""
                for token in result:
                    full_response += token
                    yield token
                _log_call(prompt, model, stream, full_response, latency_ms)

            logger.info(
                "[STREAM] Ollama LLM: model=%s, prompt='%s...'", model, prompt[:50]
            )
            return {
                "ok": True,
                "stream": True,
                "generator": logged_generator(),
                "error": None,
            }
        else:
            _log_call(prompt, model, stream, result, latency_ms)
            logger.info(
                "[OLLAMA] model=%s → %d chars in %dms", model, len(result), latency_ms
            )
            return {
                "ok": True,
                "data": result,
                "error": None,
            }

    except Exception as e:
        # ➤ Fallback to mock
        error_msg = f"Ollama call failed, using mock: {e}"
        logger.warning(error_msg)

        fake_response = f"Answer to '{prompt[:30]}...' using model '{model}'. This is a simulated response."

        if stream:

            def mock_generator():
                for word in fake_response.split():
                    yield word + " "

            return {
                "ok": True,
                "stream": True,
                "generator": mock_generator(),
                "error": None,
            }
        else:
            return {
                "ok": True,
                "data": fake_response,
                "error": None,
            }
