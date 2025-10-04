"""
Shared embedding utility for memory search backends.

Auto-selects best available model:
    1. sentence-transformers (if installed) → best
    2. transformers w/ mean pooling (fallback) → good
    3. Mock embeddings (last resort) → always works
"""

import threading
import logging
import hashlib
from typing import List
import numpy as np

logger = logging.getLogger("adam.embedder")

# ➤ Lazy imports
_ST_AVAILABLE = False
_TF_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer

    _ST_AVAILABLE = True
except ImportError:
    pass

if not _ST_AVAILABLE:
    try:
        from transformers import AutoTokenizer, AutoModel
        import torch

        _TF_AVAILABLE = True
    except ImportError:
        pass


class EmbeddingModel:
    _instances = {}
    _lock = threading.Lock()

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        with self._lock:
            if model_name not in self._instances:
                self._instances[model_name] = self._load_model(model_name)
            self.model = self._instances[model_name]

    def _load_model(self, model_name: str):
        if _ST_AVAILABLE:
            try:
                model = SentenceTransformer(model_name)
                logger.info("Loaded SentenceTransformer: %s", model_name)
                return {"type": "sentence_transformers", "model": model}
            except Exception as e:
                logger.warning("Failed to load SentenceTransformer: %s", e)

        if _TF_AVAILABLE:
            try:
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModel.from_pretrained(model_name)
                logger.info("Loaded transformers model: %s", model_name)
                return {"type": "transformers", "tokenizer": tokenizer, "model": model}
            except Exception as e:
                logger.warning("Failed to load transformers model: %s", e)

        logger.warning("No embedding model available. Using mock embeddings.")
        return {"type": "mock"}

    def encode(self, texts: List[str]) -> np.ndarray:
        model_data = self.model

        if model_data["type"] == "sentence_transformers":
            embeddings = model_data["model"].encode(texts, convert_to_numpy=True)
            return embeddings.astype(np.float32)

        elif model_data["type"] == "transformers":
            tokenizer = model_data["tokenizer"]
            model = model_data["model"]

            inputs = tokenizer(
                texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            )
            with torch.no_grad():
                outputs = model(**inputs)
                # Mean pooling
                attention_mask = inputs["attention_mask"]
                token_embeddings = outputs.last_hidden_state
                input_mask_expanded = (
                    attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
                )
                sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
                sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
                mean_pooled = sum_embeddings / sum_mask
                return mean_pooled.numpy().astype(np.float32)

        else:  # mock
            embeddings = []
            for text in texts:
                h = hashlib.md5(text.encode()).hexdigest()
                vec = [
                    int(h[i : i + 2], 16) / 255.0 for i in range(0, min(len(h), 64), 2)
                ]
                # Pad or truncate to 384 dims (standard for MiniLM)
                vec = (vec * (384 // len(vec) + 1))[:384]
                embeddings.append(vec)
            return np.array(embeddings, dtype=np.float32)
