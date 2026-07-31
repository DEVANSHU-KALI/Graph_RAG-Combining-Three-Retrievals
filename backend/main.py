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


app = FastAPI(title="GraphRAG API", lifespan=lifespan)


# Middleware
app.add_middleware(LoggingMiddleware)


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)


@app.get("/health")
async def health_check():

    return {"status": "healthy"}


@app.post("/chat")
async def chat_endpoint(request: QueryRequest):

    result = await generate_answer(request.query, bm25_index, documents)

    return result
