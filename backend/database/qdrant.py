# backend/database/qdrant.py

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams

from backend.core.logging import logger

# Create async Qdrant client
qdrant_client = AsyncQdrantClient(host="localhost", port=6333)


# Collection name
COLLECTION_NAME = "hybrid_graphrag"


async def initialize_qdrant() -> None:

    try:
        # Get all existing collections
        collections = await qdrant_client.get_collections()

        collection_names = [collection.name for collection in collections.collections]

        # Create collection if it does not exist
        if COLLECTION_NAME not in collection_names:
            await qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )

            logger.info(f"Created Qdrant collection: {COLLECTION_NAME}")

        else:
            logger.info(f"Qdrant collection already exists: {COLLECTION_NAME}")

    except Exception as error:
        logger.error(f"Failed to initialize Qdrant: {error}")

        raise
