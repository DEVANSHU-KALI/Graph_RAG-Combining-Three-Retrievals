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

#### 3. Reranking and Context Compiling
```python
    # Reranking
    reranked_chunks = await rerank_results(query, retrieved_chunks)

    # Build Context
    context = "\n\n".join(chunk["text"] for chunk in reranked_chunks)

    # Citations
    citations = list(set(chunk["source"] for chunk in reranked_chunks))
```
- **`rerank_results`:** Sends the candidate pool to the Cross-Encoder model. It returns only the top 3 highest-relevance chunks.
- **`context`:** Joins the text payloads of these top 3 chunks using double newlines to form the reference context for the LLM.
- **`citations`:** Extracts unique source filenames (e.g., `biology.txt`, `physics.txt`) from the metadata of the winning chunks, providing trace citations.

---

#### 4. The Constrained Prompt
```python
    prompt = f"""
You are a helpful AI assistant.

Answer ONLY from the provided context.

If the answer is not present
in the context, say:

"I could not find the answer
in the provided documents."

Context:
{context}

Question:
{query}
"""
```
* **`Answer ONLY...`:** Instructs the LLM to strictly base its answer on the retrieved contexts. This is a standard guard against hallucination.
* **`I could not find the answer...`:** Instructs the model to output a standard fallback sentence if the context does not contain the answer, rather than trying to guess from its base training knowledge.

---

#### 5. Local LLM Generation
```python
    response = await client.chat.completions.create(
        model="raaedk/Qwen2.5-7B-Instruct-Q4_K_M-GGUF",
        messages=[{"role": "user", "content": prompt}],
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "citations": citations,
        "contexts": [chunk["text"] for chunk in reranked_chunks],
    }
```
- **`client.chat.completions.create`:** Calls our local `llama.cpp` server asynchronously, sending our prompt to the Qwen model.
- **Return Dictionary:** Packages the LLM's answer text, the citations list, and the raw source contexts to return to the caller (FastAPI or evaluation scripts).

---

## Tracing and Observability (LangSmith)

### What is Tracing & Why Do We Use It?
RAG pipelines involve multiple asynchronous operations (vector searches, keyword searches, entity extraction prompts, Cypher calls, and local LLM calls). If a query fails, returns bad context, or is extremely slow, it is very difficult to debug where the bottleneck occurred just by looking at a terminal log.

**LangSmith** provides visual debugging, tracing, and monitoring. By wrapping our core execution loop in a trace decorator, every input, output, latency measurement, and intermediate variable is automatically sent to the LangSmith web console.

### The `@traceable` Decorator
In `rag_pipeline.py`, we import `traceable` and apply it as a decorator to our main function:
```python
from langsmith import traceable

@traceable
async def generate_answer(query: str, bm25_index, documents):
```
* **How it works:** When Python runs the `@traceable` wrapper:
  1. It intercepts the call to `generate_answer()`, logging the starting timestamp and input parameters.
  2. It tracks the execution of all nested helper functions (such as Qdrant queries and Neo4j Cypher calls).
  3. If the pipeline succeeds, it logs the final generated response dictionary.
  4. If the pipeline crashes, it captures the complete traceback and exception details, allowing you to debug exactly which node failed.
* **Environment Configuration:** For this tracing to activate, the backend reads specific variables from the `.env` file:
  * `LANGCHAIN_TRACING_V2=true` (Enables the tracing agent).
  * `LANGCHAIN_API_KEY=your_key` (Authenticates with your LangSmith account).
  * `LANGCHAIN_PROJECT=your_project_name` (Groups logs under a specific dashboard project).

---

### Pipeline Flow:
**FastAPI forwards query** $\rightarrow$ **Execute Semantic & BM25 search** $\rightarrow$ **Apply Min-Max normalization & merge results (Hybrid)** $\rightarrow$ **Query Neo4j Graph for query entities** $\rightarrow$ **Combine Hybrid chunks & Graph statements** $\rightarrow$ **Rerank candidate pool using Cross-Encoder** $\rightarrow$ **Select top 3 chunks** $\rightarrow$ **Construct context-bounded prompt** $\rightarrow$ **Query local Qwen model** $\rightarrow$ **Return JSON payload containing generated response, citations, and contexts**.
