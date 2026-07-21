# backend/database/neo4j.py
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


def create_entity(entity_name: str) -> None:

    query = """
    MERGE (e:Entity {
        name: $entity_name
    })
    """

    with driver.session() as session:
        session.run(query, entity_name=entity_name)


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


if __name__ == "__main__":
    verify_connection()
