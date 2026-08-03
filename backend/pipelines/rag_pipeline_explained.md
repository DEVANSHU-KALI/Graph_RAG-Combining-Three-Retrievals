This file contains the explanation of rag_pipeline.py

## rag_pipeline.py

### What Does This Script Do & Why is it Used?
In simple terms, this script is the **brain of our chat pipeline**. It orchestrates the entire runtime query process: it runs the search queries across our databases, combines and ranks the results, structures a strict prompt, and calls our local LLM to write the final, citation-backed answer.

#### Reason for its Existence
A RAG system is a chain of multiple moving parts. By keeping the pipeline logic in a separate script (`rag_pipeline.py`) instead of directly inside the FastAPI server (`main.py`):
1. **Separation of Concerns:** The API server focuses purely on network handling and request validation, while this script focuses purely on the retrieval and generation algorithms.
2. **Evaluations Integration:** Testing frameworks like **Ragas** and **DeepEval** can import `generate_answer` directly to run batch evaluations on your prompts and retrieval outputs without needing to start the FastAPI server.
3. **Modularity:** It allows us to easily tweak the prompt structure, change the number of retrieved chunks, or switch model endpoints in one centralized file.

---

### Code Breakdown

#### 1. Setup and Client Initialization
```python
from openai import AsyncOpenAI

from backend.retrievals.bm25_retrieval import bm25_retrieval
from backend.retrievals.graph_retrieval import graph_retrieval
from backend.retrievals.hybrid_retrieval import hybrid_retrieval
from backend.retrievals.reranker import rerank_results
from backend.retrievals.semantic_retrieval import semantic_retrieval

client = AsyncOpenAI(base_url="http://localhost:8080/v1", api_key="dummy")
```
- **Retrievals & Reranker Imports:** Imports all individual search functions (Semantic, BM25, Hybrid, Graph) and the reranking module.
- **`client = AsyncOpenAI(...)`:** Creates an asynchronous OpenAI-compatible client. It points to `http://localhost:8080/v1` which is the local API port exposed by our `llama.cpp` server running the quantized Qwen model.

---
