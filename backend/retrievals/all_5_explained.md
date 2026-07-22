This file includes explanations of all the three retrieval codes, also including the reranker code with work flow.

## semantic_retrieval.py
apart from the imports lets get the logic directly.
```python
async def semantic_retrieval(query: str) -> list[dict]

    query_embedding = embedding_model.embed_query(query)

    results = await qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=10,
    )
```
- function takes `query as input`, then the query is converted into embeddings using the embeddings model.
- take that embeddings and compare it with the embeddings with all the points in the qdrant database.
- `qdrant_client.query_points()` is the function used to get that searching process, we pass needed attributes and as we want only top 10 relevant points(chunks) so we give that limit there. 

```python

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
```
- the variable `results` store all the things it got from qdrant database related to that embeddings.
- we use a list to store all the needed information  