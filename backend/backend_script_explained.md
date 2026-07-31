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
- **`bm25_index = None` & `documents = None`:** Initializes global variables in the module scope to store the BM25 data mapping.
- **`@asynccontextmanager`:** A Python decorator used to define setup and teardown logic for the application lifespan.
- **`lifespan(app: FastAPI)`:** 
  * Everything before the `yield` statement executes **once** when the FastAPI server starts up. Here, it calls `initialize_bm25()` which scrolls through Qdrant, tokenizes document texts, builds the BM25 lookup model, and caches it in memory.
  * The `yield` statement pauses execution, transferring control to the FastAPI application to serve client requests.
  * *Why we do it:* Pre-building the BM25 index on boot avoids re-calculating statistics for every chat query, reducing API response times.

---

#### B. App and Middleware Setup
```python
app = FastAPI(title="GraphRAG API", lifespan=lifespan)

# Middleware
app.add_middleware(LoggingMiddleware)
```
- **`app = FastAPI(...)`:** Instantiates the FastAPI application core, registering our custom `lifespan` handler.
- **`app.add_middleware(LoggingMiddleware)`:** Mounts our request logging middleware globally. Every HTTP request sent to the API will pass through `LoggingMiddleware` to start a timer, trace the path, and log execution latency.

---