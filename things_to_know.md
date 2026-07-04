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
