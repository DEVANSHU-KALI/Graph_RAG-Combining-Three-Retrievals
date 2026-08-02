from openai import AsyncOpenAI
from langsmith import traceable

from backend.retrievals.bm25_retrieval import bm25_retrieval
from backend.retrievals.graph_retrieval import graph_retrieval
from backend.retrievals.hybrid_retrieval import hybrid_retrieval
from backend.retrievals.reranker import rerank_results
from backend.retrievals.semantic_retrieval import semantic_retrieval

client = AsyncOpenAI(base_url="http://localhost:8080/v1", api_key="dummy")


# -----------------------------
# Main RAG Pipeline
# -----------------------------
@traceable
async def generate_answer(query: str, bm25_index, documents):

    # -----------------------------
    # Semantic Retrieval
    # -----------------------------
    semantic_results = await semantic_retrieval(query)

    # -----------------------------
    # BM25 Retrieval
    # -----------------------------
    bm25_results = await bm25_retrieval(query, bm25_index, documents)

    # -----------------------------
    # Hybrid Retrieval
    # -----------------------------
    hybrid_results = await hybrid_retrieval(semantic_results, bm25_results)

    # -----------------------------
    # Graph Retrieval
    # -----------------------------
    graph_results = await graph_retrieval(query)

    # -----------------------------
    # Combine Results
    # -----------------------------
    retrieved_chunks = hybrid_results + graph_results

    # -----------------------------
    # Reranking
    # -----------------------------
    reranked_chunks = await rerank_results(query, retrieved_chunks)

    # -----------------------------
    # Build Context
    # -----------------------------
    context = "\n\n".join(chunk["text"] for chunk in reranked_chunks)

    # -----------------------------
    # Citations
    # -----------------------------
    citations = list(set(chunk["source"] for chunk in reranked_chunks))

    # -----------------------------
    # Prompt
    # -----------------------------
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

    # -----------------------------
    # Generate Response
    # -----------------------------
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
