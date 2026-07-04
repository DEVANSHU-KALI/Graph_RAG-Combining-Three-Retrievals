# Things to Know: Pre-Ingestion, Processing, and Core Technologies

This document explains the offline and background processes that prepare the system's databases before you can query them. It outlines document chunking, ingestion, knowledge graph construction, local model quantization, and key configuration parameters.

For the step-by-step query runtime execution flow, refer to [project_explaination.md](file:///d:/projects/graph_rag/project_explaination.md).

---

## 1. Document Chunking & Vector Ingestion (The Vector DB Stage)

* **Script:** [injest_documents.py](file:///d:/projects/graph_rag/backend/injest_documents.py)
* **Target Database:** Qdrant (runs locally on port `6333`)

Before text documents can be searched semantically, they must undergo preprocessing. This consists of **Semantic Chunking** and **Dense Vector Generation**.

### Semantic Chunking vs. Naive Chunking
Normally, text splitters break documents down by a hard character or token limit (e.g., split every 500 characters). This naive approach often breaks sentences in half, separating critical context. 
This project utilizes a **Semantic Chunker** (`langchain_experimental.text_splitter.SemanticChunker`):
1. It splits the document into individual sentences.
2. It calculates dense vector embeddings for each sentence using the embedding model.
3. It evaluates the semantic distance (similarity) between consecutive sentences.
4. If the distance between two consecutive sentences exceeds a set threshold (configured at the **75th percentile** of similarity differences), it inserts a boundary.
5. This ensures each chunk represents a semantically coherent topic or paragraph rather than an arbitrary segment.

### Embeddings & Vector Storage
* **Embedding Model:** `sentence-transformers/all-mpnet-base-v2`
* **Dimensions:** 768 dimensions (meaning every chunk is mapped to a vector containing 768 floating-point values representing its semantic features).
* **Storage in Qdrant:** The chunks are uploaded to Qdrant as points containing:
  * An ID.
  * The 768-dimensional float vector.
  * A payload dictionary containing the source filename, chunk ID, and raw chunk text.

---

## 2. Knowledge Graph Construction (The Graph DB Stage)

* **Script:** [graph_builder.py](file:///d:/projects/graph_rag/backend/graph_builder.py)
* **Target Database:** Neo4j (runs in a Docker container on port `7687`)

The Knowledge Graph (KG) captures structured, relational context which dense vectors might miss. Building it involves parsing text chunks into nodes and edges.

```mermaid
graph LR
    subgraph Neo4j Database
        E1[Entity Node: "FastAPI"]
        E2[Entity Node: "Qdrant"]
        E1 -- "USED_WITH" --> E2
    end
```

### The LLM Extraction Loop
1. The script fetches all ingested text chunks from the Qdrant database payload.
2. For each chunk, it builds a prompt instructing a powerful LLM (`llama-3.1-8b-instant` via the Groq API) to extract entity-relationship triplets.
3. To enforce strict format validation, the request uses JSON mode:
   ```json
   {
       "entities": ["FastAPI", "Qdrant"],
       "relationships": [
           {
               "source": "FastAPI",
               "target": "Qdrant",
               "relation": "USED_WITH"
           }
       ]
   }
   ```
   
4. **Neo4j Cypher Injection:**
   The script iterates over the returned JSON. It sanitizes relationship names into uppercase, snake-case strings and executes Cypher commands:
   * **Node Creation:** `MERGE (e:Entity {name: $entity_name})` (Ensures unique nodes).
   * **Relationship Creation:** `MERGE (source)-[:RELATIONSHIP]->(target)` (Connects nodes).

### Groq API Rate Limiting & The 15-Second Sleep
Building graphs via LLM extraction is highly token-intensive. Free-tier API providers like Groq impose strict **Requests Per Minute (RPM)** and **Tokens Per Minute (TPM)** limits.
To prevent script failures due to `429 Too Many Requests` status codes, `graph_builder.py` sleeps for **15 seconds** after processing each chunk:
```python
# Rate Limiting Guard
time.sleep(15)
```
This rate-limiting buffer is crucial for script stability during batch parsing.

---