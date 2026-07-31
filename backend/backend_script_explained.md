# Backend Script Explanation

This document explains the main execution server of the application: `main.py`. This script serves as the API gateway for our Hybrid GraphRAG system, exposing web endpoints for the frontend application.

---

## 1. `main.py`

### What Does This Script Do?
The `main.py` script initializes and exposes a **FastAPI** web application. Its primary responsibilities are:
1. **Server Lifecycle Management (Lifespan):** Runs startup events, such as loading document data and pre-calculating the BM25 keyword index in-memory (RAM) to keep query responses fast.
2. **Middleware Registration:** Attaches our request-logging middleware globally to measure endpoint latency.
3. **Request Schema Validation:** Enforces structural constraints on incoming payloads using Pydantic.
4. **API Endpoint Routing:** Exposes a health check route (`/health`) and the primary chat pipeline gateway (`/chat`).

---

### Code Breakdown

#### A. Lifespan Context Manager
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel, Field
from backend.core.middleware import LoggingMiddleware
from backend.pipelines.rag_pipeline import generate_answer
from backend.retrievals.bm25_retrieval import initialize_bm25

bm25_index = None
documents = None

@asynccontextmanager
async def lifespan(app: FastAPI):

    global bm25_index
    global documents

    bm25_index, documents = await initialize_bm25()

    yield
```