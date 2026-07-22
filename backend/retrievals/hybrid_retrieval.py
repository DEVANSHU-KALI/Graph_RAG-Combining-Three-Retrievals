# -----------------------------
# Normalize Scores
# -----------------------------
def normalize_scores(results: list[dict]) -> list[dict]:

    if not results:
        return []

    scores = [result["score"] for result in results]

    max_score = max(scores)
    min_score = min(scores)

    if max_score == min_score:
        for result in results:
            result["score"] = 1.0

        return results

    for result in results:
        result["score"] = (result["score"] - min_score) / (max_score - min_score)

    return results


# -----------------------------
# Hybrid Retrieval
# -----------------------------
async def hybrid_retrieval(
    semantic_results: list[dict], bm25_results: list[dict]
) -> list[dict]:

    semantic_results = normalize_scores(semantic_results)

    bm25_results = normalize_scores(bm25_results)

    combined_results = {}

    # -----------------------------
    # Add Semantic Results
    # -----------------------------
    for result in semantic_results:
        chunk_id = result["chunk_id"]

        combined_results[chunk_id] = {
            "text": result["text"],
            "source": result["source"],
            "chunk_id": chunk_id,
            "semantic_score": result["score"],
            "bm25_score": 0.0,
            "final_score": result["score"],
        }

    # -----------------------------
    # Add BM25 Results
    # -----------------------------
    for result in bm25_results:
        chunk_id = result["chunk_id"]

        if chunk_id in combined_results:
            combined_results[chunk_id]["bm25_score"] = result["score"]

            combined_results[chunk_id]["final_score"] += result["score"]

        else:
            combined_results[chunk_id] = {
                "text": result["text"],
                "source": result["source"],
                "chunk_id": chunk_id,
                "semantic_score": 0.0,
                "bm25_score": result["score"],
                "final_score": result["score"],
            }

    # -----------------------------
    # Sort Results
    # -----------------------------
    hybrid_results = sorted(
        combined_results.values(), key=lambda x: x["final_score"], reverse=True
    )

    return hybrid_results[:5]
