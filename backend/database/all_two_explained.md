# Database Management Scripts (`backend/database/`)

This directory contains the database client initializations, connectivity drivers, and schema creation logic for the two databases powering our Hybrid GraphRAG pipeline:

- **Qdrant** (Vector Database)
- **Neo4j** (Graph Database)

---

## 1. Qdrant Database Script (`qdrant.py`)

### What Does This Script Do?

The `qdrant.py` script serves as the centralized interface for our **Vector Database**.

Its primary responsibilities are:
