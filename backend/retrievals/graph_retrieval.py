from neo4j import GraphDatabase

from backend.core.config import NEO4J_PASSWORD, NEO4J_URL, NEO4J_USERNAME
from backend.entity_extractor import extract_entities

driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


# -----------------------------
# Graph Retrieval
# -----------------------------
async def graph_retrieval(query: str) -> list[dict]:

    entities = extract_entities(query)

    if not entities:
        return []

    with driver.session() as session:
        result = session.run(
            """
            MATCH (source)-[r]->(target)

            WHERE
                source.name IN $entities
                OR
                target.name IN $entities

            RETURN
                source.name AS source,
                type(r) AS relationship,
                target.name AS target
            """,
            entities=entities,
        )

        graph_results = []

        for record in result:
            graph_results.append(
                {
                    "text": (
                        f"{record['source']} "
                        f"{record['relationship']} "
                        f"{record['target']}"
                    ),
                    "source": "graph",
                    "chunk_id": None,
                    "score": 1.0,
                }
            )

    return graph_results[:5]
