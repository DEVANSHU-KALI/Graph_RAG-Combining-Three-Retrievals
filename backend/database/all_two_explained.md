# Database Management Scripts (`backend/database/`)

This directory contains the database client initializations, connectivity drivers, and schema creation logic for the two databases powering our Hybrid GraphRAG pipeline:

- **Qdrant** (Vector Database)
- **Neo4j** (Graph Database)

## 1. Qdrant Database Script (`qdrant.py`)

### What Does This Script Do?

The `qdrant.py` script serves as the centralized interface for our **Vector Database**.

Its primary responsibilities are:

1. Instantiating an asynchronous client to communicate with the local Qdrant engine on port `6333`.
2. Defining the global collection name (`hybrid_graphrag`) used across the entire application.
3. Automatically checking for and creating the vector collection with the correct vector dimensions (**768D**) and distance metric (**Cosine Similarity**) on startup.

### Block-by-Block Technical Breakdown

#### A. Imports & Async Client Initialization

```python
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams
from backend.core.logging import logger

# Create async Qdrant client
qdrant_client = AsyncQdrantClient(host="localhost", port=6333)
COLLECTION_NAME = "hybrid_graphrag"
```

- **`AsyncQdrantClient`**: An asynchronous Python client for Qdrant. Using an `async` client prevents network calls from blocking FastAPI's main event loop during high-concurrency requests.
- **`host="localhost", port=6333`**: Connects to the local Qdrant instance (typically running in a Docker container exposing port `6333`).
- **`COLLECTION_NAME`**: Standardizes the target vector collection name across ingestion and retrieval scripts.

---

#### B. Collection Initialization (`initialize_qdrant`)

```python
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
```

- **`await qdrant_client.get_collections()`**: Asynchronously fetches all existing vector collections currently hosted in Qdrant.
- **Idempotency Check (`if COLLECTION_NAME not in collection_names`)**: Prevents trying to recreate a collection that already exists, which would throw an error.
- **`VectorParams(size=768, distance=Distance.COSINE)`**:
  - **`size=768`**: Configures vector slots to match the exact **768-dimensional** output of our embedding model (`sentence-transformers/all-mpnet-base-v2`).
  - **`distance=Distance.COSINE`**: Sets **Cosine Similarity** as the mathematical formula used by Qdrant to score similarity between query vectors and document vectors.

---

## 2. Neo4j Graph Database Script (`neo4j.py`)

### What Does This Script Do?

The `neo4j.py` script serves as the interface for our **Knowledge Graph Database**.

Its primary responsibilities are:

1. Initializing the Neo4j Bolt driver with authentication credentials from `config.py`.
2. Providing a connectivity verification utility (`verify_connection`).
3. Creating individual entity nodes (`create_entity`).
4. Sanitizing relationship strings and linking entities together into Graph Triplets (`create_relationship`).

---

### Block-by-Block Technical Breakdown

#### A. Driver Setup & Connection Verification

```python
import re
from neo4j import GraphDatabase
from backend.core.config import NEO4J_PASSWORD, NEO4J_USERNAME
from backend.core.logging import logger

driver = GraphDatabase.driver(
    "bolt://localhost:7687", auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
)

def verify_connection() -> None:
    try:
        driver.verify_connectivity()
        logger.info("Successfully connected to Neo4j")
    except Exception as error:
        logger.error(f"Neo4j Connection Failed: {error}")
```