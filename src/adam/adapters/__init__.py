# src/adam/adapters.py

import collections.abc
import logging
import os
from pathlib import Path

# Define PROJECT_ROOT for ChromaDB path
PROJECT_ROOT = Path(__file__).parent.parent.parent

logger = logging.getLogger("adam")

# ==============================================================================
# SECTION 1: Abstract Base Classes (The Blueprints)
# ==============================================================================


class EmbeddingAdapter:
    """Abstract interface for an embedding model component."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embeds a list of text documents."""
        raise NotImplementedError("Subclasses must implement this method.")


class VectorStoreAdapter:
    """Abstract interface for a vector storage component."""

    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadata: list[dict],
    ) -> None:
        """Upserts documents (with vectors and metadata) into the store."""
        raise NotImplementedError("Subclasses must implement this method.")

    def search(self, query_vector: list[float], top_k: int) -> list[dict]:
        """Searches for the most similar documents to a query vector."""
        raise NotImplementedError("Subclasses must implement this method.")


# ==============================================================================
# SECTION 2: Concrete Implementations (The Real Tools)
# ==============================================================================


class SentenceTransformerEmbedder(EmbeddingAdapter):
    """A concrete implementation using the sentence-transformers library."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(model_name)
            logger.info(
                f"SentenceTransformerEmbedder loaded with model '{model_name}'."
            )
        except ImportError:
            logger.error(
                "sentence-transformers is not installed. Please run: pip install sentence-transformers"
            )
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model: {e}")
            self.model = None

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not self.model:
            return [[0.0] * 384 for _ in texts]  # Return dummy data on failure

        embeddings = self.model.encode(texts, convert_to_numpy=False)
        return [e.tolist() for e in embeddings]


class ChromaVectorStore(VectorStoreAdapter):
    """A concrete implementation using a local ChromaDB database."""

    def __init__(
        self,
        collection_name: str = "adam_memory",
        path: str = str(PROJECT_ROOT / "vector_store"),
    ):
        try:
            import chromadb

            os.makedirs(path, exist_ok=True)  # Ensure directory exists
            self.client = chromadb.PersistentClient(path=path)
            self.collection = self.client.get_or_create_collection(name=collection_name)
            logger.info(
                f"ChromaVectorStore connected to collection '{collection_name}'."
            )
        except ImportError:
            logger.error("chromadb is not installed. Please run: pip install chromadb")
            self.client = None
            self.collection = None
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.client = None
            self.collection = None

    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadata: list[dict],
    ):
        if not self.collection:
            return
        self.collection.upsert(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadata
        )

    def search(self, query_vector: list[float], top_k: int) -> list[dict]:
        if not self.collection:
            return []
        results = self.collection.query(
            query_embeddings=[query_vector], n_results=top_k
        )

        formatted_results = []
        if results and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                formatted_results.append(
                    {
                        "id": doc_id,
                        "score": results["distances"][0][i]
                        if results["distances"]
                        else 0,
                        "meta": results["metadatas"][0][i]
                        if results["metadatas"]
                        else {},
                        "document": results["documents"][0][i]
                        if results["documents"]
                        else "",
                    }
                )
        return formatted_results  # ← REMOVED TRAILING DOT
