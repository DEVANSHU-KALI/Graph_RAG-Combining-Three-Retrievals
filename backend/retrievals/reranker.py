from sentence_transformers import CrossEncoder

# -----------------------------
# Load Reranker Model
# -----------------------------
reranker = CrossEncoder(
    "BAAI/bge-reranker-base"
)


# -----------------------------
# Rerank Results
# -----------------------------
async def rerank_results(
    query: str,
    retrieved_chunks: list[dict]
) -> list[dict]:

    pairs = [
        (
            query,
            chunk["text"]
        )
        for chunk in retrieved_chunks
    ]

    scores = reranker.predict(
        pairs
    )

    reranked_results = []

    for chunk, score in zip(
        retrieved_chunks,
        scores
    ):

        reranked_results.append(
            {
                **chunk,
                "rerank_score": float(score)
            }
        )

    reranked_results = sorted(
        reranked_results,
        key=lambda x: x["rerank_score"],
        reverse=True
    )

    return reranked_results[:3]