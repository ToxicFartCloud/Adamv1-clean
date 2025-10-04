from src.adam.adapters import SentenceTransformerEmbedder, ChromaVectorStore

# Test embedding
print("Testing embedder...")
embedder = SentenceTransformerEmbedder()
vectors = embedder.embed_texts(["Hello world"])
print(f"Embedding dimension: {len(vectors[0])}")

# Test vector store
print("\nTesting vector store...")
store = ChromaVectorStore()
store.upsert(
    ids=["1"],
    documents=["Hello world"],
    embeddings=[[0.1] * 384],
    metadata=[{"source": "test.txt"}],
)
results = store.search([0.1] * 384, top_k=1)
print("Search results:", results)
