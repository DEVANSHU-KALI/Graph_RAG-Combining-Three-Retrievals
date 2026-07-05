# Things to Know: Pre-Ingestion, Processing, and Core Technologies

This document explains the offline and background processes that prepare the system's databases before you can query them. It outlines document chunking, ingestion, knowledge graph construction, local model quantization, and key configuration parameters.

For the step-by-step query runtime execution flow, refer to [project_explaination.md]

---

## 1. Document Chunking & Vector Ingestion (The Vector DB Stage)

* **Script:** [injest_documents.py](file:graph_rag/backend/injest_documents.py)
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
- Semantic chunking works based on embedding mode you choose. Better embedding model, better split as it understand the data well.
- If you observer the code, you can see that we import the embedding model from the embedding model script into this chunking script to use that here instead of again initializing the embedding model in the chunking script.
- Info related to the chunking will be explained more deeply in the [key_concepts.md]
### Embeddings & Vector Storage
* **Embedding Model:** `sentence-transformers/all-mpnet-base-v2`
* **Dimensions:** 768 dimensions (meaning every chunk is mapped to a vector containing 768 floating-point values representing its semantic features).
* **Storage in Qdrant:** The chunks are uploaded to Qdrant as points containing:
  * An ID.
  * The 768-dimensional float vector.
  * A payload dictionary containing the source filename, chunk ID, and raw chunk text, as these are the only things we needed to make the system work, and you can also add other things to metadata.
- All the info related to the embeddings will be explained more deeply in the [key_concepts.md]
---

## 2. Knowledge Graph Construction (The Graph DB Stage)

* **Script:** [graph_builder.py](file:graph_rag/backend/graph_builder.py)
* **Target Database:** Neo4j (runs in a Docker container on port `7687`)

The Knowledge Graph (KG) captures structured, relational context which dense vectors might miss. Building it involves parsing text chunks into nodes and edges.

``` m
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

## 3. Local LLM Setup & Quantization

The final generation stage uses a locally hosted LLM to guarantee privacy, security, and eliminate API call costs during conversation.

* **Model Used:** `raaedk/Qwen2.5-7B-Instruct-Q4_K_M-GGUF`
* **Local Hosting Framework:** `llama.cpp` (specifically `llama-server.exe`)

### Model Quantization
Running a 7-billion parameter model in full 16-bit floating-point precision (FP16) requires roughly **14 GB of VRAM** just to load the model weights, which is out of range for average consumer hardware.
**Quantization** is a deep-learning optimization technique that shrinks model weights.
* **How it works:** It maps high-precision floating-point numbers to lower-precision representations (e.g., 4-bit integers). 
* **The Result:** The model size is reduced from 14 GB down to **~4.7 GB** with negligible loss in reasoning ability. This allows the model to run comfortably on standard consumer GPUs or system RAM.

### Running the Local Llama Server
We launch `llama.cpp` in server mode, exposing an OpenAI-compatible endpoint:
```bash
.\llama-server.exe -hf raaedk/Qwen2.5-7B-Instruct-Q4_K_M-GGUF -ngl 25
```
* **`-hf` Parameter:** Downloads the specified repository directly from Hugging Face if it is not cached locally.
* **`-ngl 25` (Number of GPU Layers to Offload):** Offloads 25 of the model's layers directly to your graphics card (CUDA/Metal) while running the remaining layers on your CPU. Adjusting this value higher or lower helps tune performance based on your system's VRAM capacity.

---

## 4. API LLM (Groq) vs. Local LLM (Qwen)

You might wonder why we use a cloud-based API model for building the graph but a local model for answering questions:

| Feature / Task | Graph Building (Groq Llama 3.1 8B) | RAG Question Answering (Local Qwen 2.5 7B) |
| :--- | :--- | :--- |
| **Task Complexity** | **High:** Requires structured entity extraction, strict JSON compliance, and high semantic parsing logic. | **Moderate:** Needs to synthesize an answer from a provided context under strict constraints. |
| **Execution Frequency** | **Low:** Done only once offline during the initial setup/ingestion phase. | **High:** Executed every time a user types a message in the chat. |
| **LLM Requirement** | **API Cloud Model:** A large, highly capable model is necessary to avoid extraction errors and JSON schema breaks. | **Local Model:** Cost-free, private, and highly context-loyal. Local models are easily constrained to only answer from provided text. |
