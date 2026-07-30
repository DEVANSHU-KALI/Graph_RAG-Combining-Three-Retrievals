# backend/ingest_documents.py

import os

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from backend.core.logging import logger
from backend.embedding_model import embedding_model
from backend.text_chunker import text_splitter

client = QdrantClient(host="localhost", port=6333)

COLLECTION_NAME = "hybrid_graphrag"


def ingest_documents(folder_path: str) -> None:

    documents = []

    chunk_id = 0

    # -----------------------------
    # Read TXT Files
    # -----------------------------
    for filename in os.listdir(folder_path):
        if not filename.endswith(".txt"):
            continue

        file_path = os.path.join(folder_path, filename)

        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()

        # -----------------------------
        # Semantic Chunking
        # -----------------------------
        chunks = text_splitter.create_documents([text])

        # -----------------------------
        # Store Chunks
        # -----------------------------
        for chunk in chunks:
            documents.append(
                {"chunk_id": chunk_id, "text": chunk.page_content, "source": filename}
            )

            chunk_id += 1

    logger.info(f"Generated {len(documents)} chunks")

    # -----------------------------
    # Generate Embeddings
    # -----------------------------
    chunk_texts = [document["text"] for document in documents]

    embeddings = embedding_model.embed_documents(chunk_texts)

    logger.info(f"Generated {len(embeddings)} embeddings")

    # -----------------------------
    # Create Qdrant Points
    # -----------------------------
    points = []

    for document, embedding in zip(documents, embeddings):
        points.append(
            PointStruct(
                id=document["chunk_id"],
                vector=embedding,
                payload={
                    "chunk_id": document["chunk_id"],
                    "text": document["text"],
                    "source": document["source"],
                },
            )
        )

    # -----------------------------
    # Upload To Qdrant
    # -----------------------------
    client.upsert(collection_name=COLLECTION_NAME, points=points)

    logger.info(f"Uploaded {len(points)} chunks to Qdrant")


if __name__ == "__main__":
    ingest_documents("data")
