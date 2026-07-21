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
