---FILE_START path: docs/specs/rag-pipeline.md
# RAG Pipeline — Spec (EmbeddingGemma + LanceDB)

## Ingestion

1.  **Input**: The `/v1/ingest` endpoint accepts raw documents (`documents: [{text, ...}]`) or a list of URLs (`urls: [...]`).
2.  **Fetching**: If URLs are provided, the system will fetch the content of each URL. It will respect `robots.txt` and timeout after 10 seconds.
3.  **Text Normalization**: All fetched/provided text is normalized: basic HTML stripping, convert to plain text, remove excessive whitespace.
4.  **Chunking**:
    -   **Strategy**: Recursive Character Text Splitting.
    -   **Chunk Size**: `1000` characters. This refers to the number of characters in each chunk.
    -   **Chunk Overlap**: `150` characters.
5.  **Metadata Generation**: For each chunk, the following metadata is generated and stored:
    -   `source` (string): The origin of the document (e.g., URL, file path).
    -   `title` (string, optional): The document title, if available.
    -   `doc_id` (string): A unique identifier for the source document (e.g., hash of the URL).
    -   `chunk_id` (integer): The sequential number of the chunk within the document (e.g., 0, 1, 2...).
    -   `language` (string, optional): Detected language code (e.g., "en").
6.  **Deduplication (Optional)**: Before embedding, generate a SHA256 hash of the normalized chunk text. If a chunk with the same hash already exists in the index, skip it to prevent duplicate entries.

## Embeddings

-   **Model**: `EmbeddingGemma` (or model specified in `config.models.embedding`).
-   **Provider**: Ollama, via the `/api/embed` endpoint.
-   **Dimensions**:
    -   Default: `768`.
    -   Optional MRL (Matryoshka Representation Learning): `512`, `256`. The vector will be truncated to the specified dimension post-generation.
-   **Normalization**: Vectors are expected to be normalized by the embedding model. Set to `true` by default.
-   **Prompt Templating**: No prompt templating is required for `EmbeddingGemma`. The text is sent directly. We differentiate "query" vs "document" embeddings by convention in our code, but the model API call is the same.

## Storage (LanceDB)

-   **Database Path**: `./data/lancedb` (configurable in `adam.yaml`).
-   **Table Schema**:
    -   `id` (string): Primary key, formatted as `{doc_id}_{chunk_id}`.
    -   `text` (string): The actual text content of the chunk.
    -   `vector` (FixedSizeList(float, 768)): The 768-dimension embedding.
    -   `metadata` (struct): A struct containing `source`, `title`, `doc_id`, etc.
-   **Indexing**:
    -   **Type**: IVF_PQ (Inverted File Index with Product Quantization). This provides a good balance of speed and accuracy for large datasets.
    -   **Parameters**: `num_partitions=256`, `num_sub_vectors=96`. These are starting parameters and should be tuned based on dataset size.
-   **Upsert Logic**: The ingestion process will use an `upsert` operation based on the `id` field. This makes ingestion idempotent: re-ingesting the same document will overwrite existing chunks but not create duplicates.

## Search

1.  **Input**: The `/v1/search` endpoint receives a `query` string.
2.  **Embedding**: The query string is embedded using the same `EmbeddingGemma` model to create a 768-dimension query vector.
3.  **Similarity Search**:
    -   **Metric**: Cosine similarity.
    -   **`top_k`**: Defaults to `8`. The number of chunks to retrieve.
4.  **Output**: The endpoint returns a list of matching chunks, including their text, score, and metadata, which serves as the basis for citations.
    -   `chunks`: The retrieved text content.
    -   `scores`: The similarity scores.
    -   `citations`: The `metadata` objects for each chunk.

## Evaluation (Mini Plan)

For a quick quality check on our RAG pipeline using a 10-Q (quarterly financial report) as a sample document:
1.  **Prepare Questions**: Write 10-15 questions whose answers are definitively in the 10-Q (e.g., "What was the total revenue?", "List the key risk factors mentioned.").
2.  **Ingest**: Ingest the 10-Q document.
3.  **Run Search**: For each question, run a search against the index (`/v1/search`).
4.  **Metrics**:
    -   **Hit Rate @ K (hit@k)**: For each question, is at least one of the top K=3 retrieved chunks relevant to answering the question? Calculate the percentage of questions with at least one hit.
    -   **Mean Reciprocal Rank (MRR)**: For each question, find the rank of the *first* relevant document. MRR is the average of the reciprocal of these ranks (1/rank). A higher MRR means relevant results appear higher.
5.  **Manual Spot-Check**: Manually review the top 3 results for each query. Do they make sense? Are they from the correct section of the document? This provides qualitative feedback.

## Examples

### Ingest Request
```json
{
  "urls": ["https://www.sec.gov/ix?doc=/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm"],
  "metadata": { "document_type": "10-Q" }
}
```
### Ingest Response
```json
{
  "inserted": 152,
  "vector_dim": 768,
  "index_name": "aapl_10q_2023",
  "sample_ids": ["d41d8cd9_0", "d41d8cd9_1"]
}
```

### Search Request
```json
{
  "query": "What are the risks related to international operations?",
  "top_k": 3
}
```
### Search Response
```json
{
  "matches": [
    {
      "id": "d41d8cd9_45",
      "score": 0.91,
      "text": "The Company’s international operations subject it to a variety of risks, including...",
      "metadata": {"source": "https://...", "title": "Apple Inc. 10-Q"}
    }
  ],
  "query_embedding_dim": 768
}
```
---FILE_END