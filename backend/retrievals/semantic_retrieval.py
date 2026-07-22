from qdrant_client.models import SearchRequest

from backend.database.qdrant import COLLECTION_NAME, qdrant_client
from backend.embedding_model import embedding_model


async def semantic_retrieval(query: str) -> list[dict]:

    query_embedding = embedding_model.embed_query(query)

    results = await qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=10,
    )

    retrieved_chunks = []

    for point in results.points:
        retrieved_chunks.append(
            {
                "text": point.payload["text"],
                "source": point.payload["source"],
                "chunk_id": point.payload["chunk_id"],
                "score": point.score,
            }
        )

    return retrieved_chunks
