# Ingestion Scripts Explanation

This document explains the scripts in charge of preprocessing, chunking, embedding, and uploading document data to our Qdrant vector database. These processes are run **offline** before the chat server starts to prepare the dataset.

The ingestion pipeline consists of three scripts:
1. `embedding_model.py` - Sets up the text embedder.
2. `text_chunker.py` - Standardizes semantic paragraph splitting.
3. `injest_documents.py` - Orchestrates file reading, chunking, vector generation, and Qdrant ingestion.

---

## 1. `embedding_model.py`

### What Does This Script Do?
This script initializes our text embedding model using the `langchain_huggingface` library. It loads the `sentence-transformers/all-mpnet-base-v2` model from HuggingFace. This object is imported by other scripts whenever text (either document chunks or incoming search queries) needs to be converted into mathematical vectors.

### Code Breakdown
```python
from langchain_huggingface import HuggingFaceEmbeddings

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"
)
```
- **`HuggingFaceEmbeddings`:** A wrapper class that download and executes HuggingFace models locally using PyTorch.
- **`model_name="sentence-transformers/all-mpnet-base-v2"`:** Specifies the model checkpoint. This is a top-performing sentence transformer model that outputs **768-dimensional vectors**. It maps semantic concepts into coordinates in a high-dimensional space.

---

## 2. `text_chunker.py`

### What Does This Script Do?
This script configures a **Semantic Chunker** that splits raw text documents into smaller chunks. Unlike naive chunkers that split text at arbitrary character lengths, this chunker splits document text on semantic boundaries when the topic changes.

### Code Breakdown
```python
from langchain_experimental.text_splitter import SemanticChunker
from backend.embedding_model import embedding_model

text_splitter = SemanticChunker(
    embedding_model,
    breakpoint_threshold_type="percentile",
    breakpoint_threshold_amount=75,
)
```
- **`SemanticChunker`:** Imports LangChain's experimental splitter.
- **`embedding_model`:** Passed as the first argument because the splitter must convert sentences into vectors to evaluate how closely related they are.
- **`breakpoint_threshold_type="percentile"` & `breakpoint_threshold_amount=75`:** 
  1. The splitter divides the document into individual sentences.
  2. It calculates the semantic distance (cosine difference) between consecutive sentences.
  3. It analyzes these differences across the document and calculates the 75th percentile of topic shifts.
  4. Any boundary where the topic shift exceeds this 75th percentile threshold triggers a chunk split. This groups sentences belonging to the same topic together.

---

## 3. `injest_documents.py`

### What Does This Script Do?
This is the master orchestrator script. It scans the `/data` directory for `.txt` files, reads them, splits them semantically into chunks, calls the embedding model to generate coordinate vectors for each chunk, packages them into Qdrant database points, and uploads them in bulk.

### Code Breakdown

#### A. Client Initialization
```python
import os
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from backend.core.logging import logger
from backend.embedding_model import embedding_model
from backend.text_chunker import text_splitter

client = QdrantClient(host="localhost", port=6333)
COLLECTION_NAME = "hybrid_graphrag"
```
- **`QdrantClient`:** Initializes a synchronous connection to the local Qdrant database running on port `6333`.
- **`PointStruct`:** The data model schema used to format records for Qdrant database insertion.

---

#### B. Reading and Chunking Files
```python
def ingest_documents(folder_path: str) -> None:
    documents = []
    chunk_id = 0

    for filename in os.listdir(folder_path):
        if not filename.endswith(".txt"):
            continue

        file_path = os.path.join(folder_path, filename)
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()

        chunks = text_splitter.create_documents([text])

        for chunk in chunks:
            documents.append(
                {"chunk_id": chunk_id, "text": chunk.page_content, "source": filename}
            )
            chunk_id += 1
```
- **`os.listdir(folder_path)`:** Loops through the target folder and skips any files that are not `.txt`.
- **`text_splitter.create_documents`:** Invokes our semantic chunker on the raw text, returning a list of document objects containing segmented paragraph texts.
- **`documents.append`:** Loop flattens chunks into simple dictionaries, assigning an incrementing integer `chunk_id` and recording the `source` filename (critical for source citations in the chat interface).

---

#### C. Vector Generation & Payload Formatting
```python
    logger.info(f"Generated {len(documents)} chunks")

    chunk_texts = [document["text"] for document in documents]
    embeddings = embedding_model.embed_documents(chunk_texts)
    logger.info(f"Generated {len(embeddings)} embeddings")

    points = []
    for document, embedding in zip(documents, embeddings):
        points.append(
            PointStruct(
                id=document["chunk_id"],
                vector=embedding,
                payload={
                    "chunk_id": document["chunk_id"],
                    "text": document["text"],
                    "source": document["source"],
                },
            )
        )
```
- **`embed_documents(chunk_texts)`:** Calls our local sentence-transformers model to compute vectors for all extracted text chunks in a single batch operation.
- **`zip(documents, embeddings)`:** Matches each document dictionary with its corresponding 768-dimensional float vector.
- **`PointStruct`:** Packages each record. Qdrant requires points to have:
  * `id`: A unique integer.
  * `vector`: The 768 float array.
  * `payload`: A metadata dictionary containing key-value data (the raw text and file source) to retrieve later.

---

#### D. Batch Uploading
```python
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    logger.info(f"Uploaded {len(points)} chunks to Qdrant")

if __name__ == "__main__":
    ingest_documents("data")
```
- **`client.upsert`:** Uploads the entire list of formatted `PointStruct` objects to Qdrant. If a point with the same ID already exists, it is overwritten.
- **`__main__`:** Triggers the pipeline, passing the folder `"data"` as the input directory.

---

### Ingestion Flow:
**Scan data folder for `.txt` files** $\rightarrow$ **Read text files** $\rightarrow$ **Split text semantically based on sentence distance thresholds** $\rightarrow$ **Batch embed text chunks using sentence-transformers** $\rightarrow$ **Construct Qdrant PointStruct objects containing vector coordinates and text metadata payloads** $\rightarrow$ **Upsert points to Qdrant**.
