# backend/graph_builder.py
# backend/graph_builder.py

import asyncio
import json
import time

from openai import OpenAI

from backend.core.config import GROQ_API_KEY
from backend.core.logging import logger
from backend.database.neo4j import create_entity, create_relationship
from backend.database.qdrant import COLLECTION_NAME, qdrant_client

client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)


# -----------------------------
# Extract Graph From Chunk
# -----------------------------
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


# -----------------------------
# Build Graph
# -----------------------------
def build_graph(chunks: list[str]) -> None:

    for chunk in chunks:
        try:
            graph_data = extract_graph_from_chunk(chunk)

            entities = graph_data.get("entities", [])

            relationships = graph_data.get("relationships", [])

            # -------------------
            # Create Nodes
            # -------------------
            for entity in entities:
                create_entity(entity)

            # -------------------
            # Create Relationships
            # -------------------
            for relationship in relationships:
                create_relationship(
                    source=relationship["source"],
                    relationship=relationship["relation"],
                    target=relationship["target"],
                )

            logger.info("Chunk graph stored successfully")

            # -------------------
            # Rate Limiting
            # -------------------
            time.sleep(15)

        except Exception as error:
            logger.error(f"Graph Extraction Error: {error}")


# -----------------------------
# Load Chunks From Qdrant
# -----------------------------
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


# -----------------------------
# Main
# -----------------------------
async def main():

    chunks = await load_chunks()

    build_graph(chunks)


if __name__ == "__main__":
    asyncio.run(main())
