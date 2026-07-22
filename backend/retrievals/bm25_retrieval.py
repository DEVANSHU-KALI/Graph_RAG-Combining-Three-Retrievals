from rank_bm25 import BM25Okapi

from backend.database.qdrant import COLLECTION_NAME, qdrant_client


# -----------------------------
# Build BM25 Once
# -----------------------------
async def initialize_bm25():

    points, _ = await qdrant_client.scroll(
        collection_name=COLLECTION_NAME,
        limit=10000,
        with_payload=True,
        with_vectors=False,
    )

    documents = []

    for point in points:
        documents.append(
            {
                "text": point.payload["text"],
                "source": point.payload["source"],
                "chunk_id": point.payload["chunk_id"],
            }
        )

    tokenized_docs = [doc["text"].lower().split() for doc in documents]

    bm25_index = BM25Okapi(tokenized_docs)

    return bm25_index, documents


# -----------------------------
# BM25 Retrieval
# -----------------------------
async def bm25_retrieval(query: str, bm25_index, documents) -> list[dict]:

    tokenized_query = query.lower().split()

    scores = bm25_index.get_scores(tokenized_query)

    results = []

    for i in range(len(documents)):
        results.append(
            {
                "text": documents[i]["text"],
                "source": documents[i]["source"],
                "chunk_id": documents[i]["chunk_id"],
                "score": float(scores[i]),
            }
        )

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    return results[:10]
