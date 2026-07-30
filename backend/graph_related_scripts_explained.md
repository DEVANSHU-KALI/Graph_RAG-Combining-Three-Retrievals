This file explains: `entity_extractor.py` and `graph_builder.py` scripts.

## entity_extractor.py
This script uses `llama` from `groq` llm provider to extract entities from the query, which is then used to search the graph database for relevant information.
We wrap the model with openai wrapper and use that, and let the llm respond in json format for better extraction.

### code breakdown
```python
import json
from openai import OpenAI
from backend.core.config import GROQ_API_KEY
client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)
```
- to get response in json format, we import json.
- we take the groq api key from the config file and initialize the client.

```python
def extract_entities(query: str) -> list[str]:
    prompt = f"""
    Extract only the important entities from the user query.
    Return ONLY valid JSON.
    ...
    {{
        "entities": [
            "FastAPI",
            "Qdrant",
            "Sarcoplasmic Reticulum"
        ]
    }}
    Query:{query}
    """
```
- the function takes query and returns list of strings as mentioned.
- the prompt is given in such way that, it make the llm to response in that specific format mentioned.
```python
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)

    return result.get("entities", [])
```
- Here one thing to notice is `client.chat.completions.create`, this is the **chat endpoint** of **openai wrapper**, so we pass our information to that llm in this way.
- We also mentioned to generate response as json object.
- Another thing to notice here is the thing which `result` variable holding,
that is how we are going to extract the response from that llm.
- finally we return the entities if they are available.

---

## graph_builder.py

### What Does This Script Do & Why is it Used?
In simple terms, this script is our offline **Knowledge Graph builder**. It extracts structured entities and relationships from our unstructured text data and stores them in our **Neo4j** graph database.

#### Reason for its Existence
When users ask questions, the chatbot needs to find connections between different concepts (e.g., *"How does FastAPI connect with Qdrant?"*). 
We cannot perform LLM-based entity-relationship extraction on hundreds of documents in real-time during a chat because it would take minutes and exceed API rate limits. Instead, this script runs **offline** (once, beforehand) as an ETL pipeline to parse our text chunks, build the graph nodes and edges, and store them permanently in Neo4j so they can be queried in milliseconds during runtime.

### Code Breakdown

#### 1. Imports and Client Initialization
```python
import asyncio
import json
import time

from openai import OpenAI

from backend.core.config import GROQ_API_KEY
from backend.core.logging import logger
from backend.database.neo4j import create_entity, create_relationship
from backend.database.qdrant import COLLECTION_NAME, qdrant_client

client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)
```
- **`create_entity` and `create_relationship`:** Imported from our Neo4j database helper script to insert nodes and relationships.
- **`qdrant_client` and `COLLECTION_NAME`:** Used to read the text chunks that are already stored in our Qdrant vector database.
- **`client = OpenAI(...)`:** Initializes the OpenAI wrapper client pointing to the Groq API endpoint to leverage their high-speed Llama-3.1 model.

#### 2. LLM Graph Extraction (`extract_graph_from_chunk`)
```python
def extract_graph_from_chunk(chunk: str) -> dict:

    prompt = f"""
    You are an advanced system designed to extract entity-relationship graphs from text.
        Return ONLY a valid JSON object matching the schema below. No explanations, no markdown block wrappers.
        Ensure all JSON keys and string values are strictly enclosed in double-quotes.

        Schema:
        {{
            "entities": ["ENTITY_NAME_1", "ENTITY_NAME_2"],
            "relationships": [
                {{
                    "source": "ENTITY_NAME_1",
                    "target": "ENTITY_NAME_2",
                    "relation": "RELATIONSHIP_TYPE"
                }}
            ]
        }}
        Guidelines:
        1. Normalize entities (convert to Title Case, e.g., "Sarcoplasmic Reticulum", "Cosine Similarity").
        2. Write relationships in UPPERCASE with underscores (e.g., "PART_OF", "STORES", "INFLUENCES").

Text to extract from:
{chunk}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)
```
- **`prompt`:** Instructs the LLM to analyze a text chunk and return a JSON containing two main keys: `entities` (list of concepts) and `relationships` (objects specifying a source node, target node, and the relationship connection type).
- **`response_format={"type": "json_object"}`:** Configures the API call to force the LLM to output a valid JSON format, preventing parsing crashes in our python script.
- **`json.loads(...)`:** Converts the raw JSON string returned by the LLM into a standard Python dictionary.

#### 3. Loading Chunks from Qdrant (`load_chunks`)
```python
async def load_chunks():

    points, _ = await qdrant_client.scroll(
        collection_name=COLLECTION_NAME,
        limit=10000,
        with_payload=True,
        with_vectors=False,
    )

    chunks = [point.payload["text"] for point in points]

    logger.info(f"Loaded {len(chunks)} chunks from Qdrant")

    return chunks
```