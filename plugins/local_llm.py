from typing import Any, Dict
import logging
import os
from pathlib import Path

METADATA = {
    "label": "Local LLM",
    "description": "Runs GGUF models locally using llama-cpp-python.",
    "ui_action": False,
    "executable": True,
}

logger = logging.getLogger("adam")

# Lazy import — only load if needed
try:
    from llama_cpp import Llama

    _llama_available = True
except ImportError:
    _llama_available = False
    logger.warning(
        "llama-cpp-python not installed. Install with: pip install llama-cpp-python"
    )


class LocalLLM:
    def __init__(self, model_path: str, n_ctx: int = 2048, n_threads: int = 4):
        if not _llama_available:
            raise RuntimeError("llama-cpp-python not available")
        self.llm = Llama(
            model_path=model_path, n_ctx=n_ctx, n_threads=n_threads, verbose=False
        )

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stream: bool = False,
    ):
        if stream:
            return self._generate_stream(prompt, max_tokens, temperature)
        else:
            output = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["\n\n"],
                echo=False,
            )
            return output["choices"][0]["text"]

    def _generate_stream(self, prompt: str, max_tokens: int, temperature: float):
        for token in self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["\n\n"],
            echo=False,
            stream=True,
        ):
            yield token["choices"][0]["text"]


# Simple in-process cache so light + heavy stay hot.
_MODEL_CACHE: Dict[str, LocalLLM] = {}


def _default_model_path() -> str:
    try:
        from src.adam.core import load_configuration

        config = load_configuration()
        return config.get("default_model_path", "models/light-condenser.gguf")
    except Exception:
        return "models/light-condenser.gguf"


def _get_llm(model_path: str) -> LocalLLM:
    llm = _MODEL_CACHE.get(model_path)
    if llm is None:
        llm = LocalLLM(model_path)
        _MODEL_CACHE[model_path] = llm
    return llm


def run(**kwargs) -> Dict[str, Any]:
    """
    Generate response using local GGUF model.

    Expected kwargs:
        - prompt: str
        - model_path: str (path to .gguf file)
        - max_tokens: int (default: 512)
        - temperature: float (default: 0.7)
        - stream: bool (default: False)

    Returns:
        Non-stream: { "ok": bool, "data": str, "error": str or None }
        Stream:     { "ok": bool, "stream": True, "generator": Generator, "error": str or None }
    """
    try:
        prompt = kwargs.get("prompt", "")
        model_path = kwargs.get("model_path")
        if not model_path:
            model_path = _default_model_path()
            print(f"DEBUG: Using default model path: {model_path}")
        print(f"DEBUG: Checking if file exists: {os.path.exists(model_path)}")

        max_tokens = kwargs.get("max_tokens", 512)
        temperature = kwargs.get("temperature", 0.7)
        stream = kwargs.get("stream", False)

        if not isinstance(prompt, str):
            return {"ok": False, "data": None, "error": "'prompt' must be a string."}

        if not Path(model_path).exists():
            return {
                "ok": False,
                "data": None,
                "error": f"Model not found: {model_path}",
            }

        llm = _get_llm(model_path)

        if stream:

            def generator():
                for token in llm.generate(prompt, max_tokens, temperature, stream=True):
                    yield token

            return {
                "ok": True,
                "stream": True,
                "generator": generator(),
                "error": None,
            }
        else:
            result = llm.generate(prompt, max_tokens, temperature, stream=False)
            return {
                "ok": True,
                "data": result,
                "error": None,
            }

    except Exception as e:
        error_msg = f"Local LLM failed: {str(e)}"
        logger.exception(error_msg)
        return {
            "ok": False,
            "data": None,
            "error": error_msg,
        }
