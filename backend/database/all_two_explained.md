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

- **`bolt://localhost:7687`**: Uses Neo4j's binary protocol (**Bolt**) for high-performance database communication.
- **`driver.verify_connectivity()`**: Sends a lightweight health check to confirm Neo4j is online and credentials are valid before performing graph operations.

---

#### B. Entity Node Creation (`create_entity`)

```python
def create_entity(entity_name: str) -> None:
    query = """
    MERGE (e:Entity {
        name: $entity_name
    })
    """
    with driver.session() as session:
        session.run(query, entity_name=entity_name)
```

- **`MERGE` Clause**: In Cypher, `MERGE` acts like a **"Get or Create"** operation. If an `:Entity` node with `name: $entity_name` already exists, it leaves it intact; if not, it creates a new node.
- **`with driver.session() as session`**: Manages the database session lifecycle, automatically opening connections and closing them when the operation completes.

---

#### C. Relationship Creation & String Sanitization (`create_relationship`)

```python
def create_relationship(source: str, relationship: str, target: str) -> None:
    # 1. Replace spaces, commas, periods, hyphens, brackets, slashes with underscores
    clean_relation = re.sub(r"[\s,\.\[\]\-\/]+", "_", relationship)
    # 2. Keep only alphanumeric characters and underscores
    clean_relation = re.sub(r"[^\w]", "", clean_relation)
    # 3. Convert to uppercase and strip leading/trailing underscores
    clean_relation = clean_relation.strip("_").upper()

    # 4. Fallback defaults if empty or invalid start character
    if not clean_relation:
        clean_relation = "RELATED_TO"
    elif clean_relation[0].isdigit():
        clean_relation = f"REL_{clean_relation}"

    query = f"""
    MERGE (source:Entity {{
        name: $source
    }})
    MERGE (target:Entity {{
        name: $target
    }})
    MERGE (source)-[:{clean_relation}]->(target)
    """

    with driver.session() as session:
        session.run(query, source=source, target=target)
```

- **Sanitization Steps**: Cypher relationship types (the label on the arrow `-[:RELATION]->`) do not support parameterization like `$relation` and must be embedded directly into the query string. Therefore, regex (`re.sub`) is used to sanitize raw LLM output:
  1. Replaces special characters (`-`, `/`, spaces, commas) with `_`.
  2. Strips out invalid non-alphanumeric characters.
  3. Converts to uppercase (standard Cypher convention, e.g., `USED_WITH`).
  4. Fixes leading digits (Cypher relationships cannot start with numbers, e.g., `1ST` becomes `REL_1ST`).
- **Cypher Execution**: Merges the `source` entity node, merges the `target` entity node, and connects them with a directed edge `-[:CLEAN_RELATION]->`.