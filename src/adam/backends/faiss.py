"""FAISS backend for memory search — fast approximate nearest neighbors."""

import logging
import json
from pathlib import Path
from typing import List, Dict
import numpy as np

from .base import MemorySearchBackend, register_backend
from ..utils.embedder import EmbeddingModel

logger = logging.getLogger("adam.backends.faiss")

# ➤ Try to import FAISS — skip registration if not available
try:
    import faiss

    _available = True
except ImportError:
    _available = False
    logger.debug("FAISS not installed — backend will not be registered.")


if _available:

    class FAISSMemoryBackend(MemorySearchBackend):
        def __init__(
            self,
            index_path: str,
            mapping_path: str,
            model_name: str = "all-MiniLM-L6-v2",
        ):
            """
            Initialize FAISS backend.

            Args:
                index_path (str): Path to .index file (e.g., "data/memory.index")
                mapping_path (str): Path to JSON mapping id → text (e.g., "data/id_to_text.json")
                model_name (str): Embedding model name for query encoding
            """
            self.index_path = Path(index_path)
            self.mapping_path = Path(mapping_path)
            self.model_name = model_name

            # ➤ Load FAISS index
            if not self.index_path.exists():
                raise FileNotFoundError(f"FAISS index not found: {self.index_path}")
            self.index = faiss.read_index(str(self.index_path))

            # ➤ Load id-to-text mapping
            if not self.mapping_path.exists():
                raise FileNotFoundError(f"Mapping file not found: {self.mapping_path}")
            with open(self.mapping_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure keys are ints
                self.id_to_text: Dict[int, str] = {int(k): v for k, v in data.items()}

            # ➤ Initialize embedder
            self.embedder = EmbeddingModel(model_name)

            logger.info(
                "FAISS backend initialized: index=%s, mapping=%s, model=%s",
                self.index_path,
                self.mapping_path,
                model_name,
            )

        def search(self, query: str, top_k: int) -> List[str]:
            """Sync search using FAISS index."""
            try:
                # Encode query
                embedding = self.embedder.encode([query])  # Shape: (1, D)

                # Search
                distances, ids = self.index.search(embedding.astype(np.float32), top_k)

                # Map ids to text
                results = []
                for i in range(len(ids[0])):
                    doc_id = int(ids[0][i])
                    text = self.id_to_text.get(doc_id, f"[MISSING ID: {doc_id}]")
                    results.append(text)

                return results

            except Exception as e:
                logger.exception("FAISS search failed")
                raise RuntimeError(f"Search error: {e}") from e

        async def asearch(self, query: str, top_k: int) -> List[str]:
            """Async search — delegates to sync version."""
            import asyncio

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.search, query, top_k)

    # ➤ Auto-register if available
    register_backend("faiss", FAISSMemoryBackend)
    logger.debug("FAISS backend registered.")
