# Hybrid GraphRAG Chatbot (Combining Three Retrievals)

An advanced Retrieval-Augmented Generation (RAG) system that combines **Semantic Vector Search**, **BM25 Keyword Search**, and **Knowledge Graph Retrieval** to deliver better context to llm, so it can generate better response.

---

## Project Overview

Standard RAG systems rely purely on semantic search, which can miss exact keyword matches or fail to capture complex relations between distinct concepts. This project implements a **Hybrid GraphRAG** pipeline:

1. **Semantic Search (Dense Retrieval):** Queries document chunks stored in **Qdrant** using dense embeddings (`sentence-transformers/all-mpnet-base-v2`).
2. **BM25 Search (Sparse Retrieval):** Performs keyword matching against tokenized document chunks.
3. **Graph Retrieval (Relational Retrieval):** Extracts entities from queries and retrieves relationships from a **Neo4j** Knowledge Graph.
4. **Hybrid Combination & Reranking:** Merges dense and sparse retrieval results, combines them with graph data, and reranks the results using a Cross-Encoder model (`BAAI/bge-reranker-base`) for optimal relevance.
5. **Response Generation:** Formulates a prompt using the best-matching contexts and queries a local LLM (`Qwen2.5-7B-q4`) to generate the final response with full source citations.
6. so, in simple words, we are combining all the three retrievals, if you are learning rag systems, I recommend you to start with the semantic rag implementation of mine, which is available in my git account, later comes the hybrid rag and then this graph rag, so this way you can understand how different retrievals show real changes.

---

## File Structure

Below is the complete file structure of the repository:

```text
graph_rag/
├── backend/                  # FastAPI Application Core
│   ├── core/                 # Configurations, logging, and middleware
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── middleware.py
│   ├── database/             # Database client initializations
│   │   ├── neo4j.py          # Neo4j Graph Database client
│   │   └── qdrant.py         # Qdrant Vector Database client
│   ├── evaluations/          # Evaluation scripts and stored results
│   │   ├── deepeval_evaluation.py
│   │   ├── deepeval_results.csv
│   │   ├── evaluation_dataset.py
│   │   ├── graph_rag_deepeval_results.csv
│   │   ├── graph_rag_ragas_results.csv
│   │   └── ragas_evaluation.py
│   ├── pipelines/            # Main RAG Pipeline coordination
│   │   └── rag_pipeline.py
│   ├── retrievals/           # Retrieval strategies
│   │   ├── bm25_retrieval.py
│   │   ├── graph_retrieval.py
│   │   ├── hybrid_retrieval.py
│   │   ├── reranker.py
│   │   └── semantic_retrieval.py
│   ├── embedding_model.py    # Embedding model configuration
│   ├── entity_extractor.py   # LLM entity extraction for graph queries
│   ├── graph_builder.py      # Knowledge graph construction script
│   ├── injest_documents.py   # Semantic chunking and vector database ingestion
│   ├── main.py               # FastAPI App entry point
│   ├── test_models.py        # API connectivity test helper
│   └── text_chunker.py       # Semantic text splitter setup
├── data/                     # Plain-text source documents for ingestion
├── docker/                   # Docker environment configurations
│   └── docker-compose.yml    # Runs Neo4j instance
├── frontend/                 # Streamlit UI Client
│   └── app.py                # Streamlit chatbot interface
├── requirements.txt          # Python project dependencies
└── README.md                 # Project documentation
```

---

## Prerequisites & Installation

Ensure you have Python 3.10+ and Docker installed on your system.

### 1. Set Up the Virtual Environment
Clone this repository, navigate to the folder, and run:
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows (Command Prompt):
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory and populate it with your API keys and credentials:
```env
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_URL=bolt://localhost:7687

# Required for Entity Extraction & Graph Building
GROQ_API_KEY=your_groq_api_key

# Optional (for evaluations and testing)
GEMINI_API_KEY=your_gemini_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=your_langsmith_project_name
```
- There is no specific rule to go with groq llm provider, you can also go with openrouter or nvidia or any other providers, but if you go with other providers you also need to make changes in the codes, starting from graph building and its retrievals to evaluations. at those places I used this specific model from that provider, so that I can get a good knowledged model with a descent RPM rate and TPm rate. I'll explain the reason more briefly in a dedicated file related to graph database. go check it out.
---

## Execution Process (Step-by-Step)

Follow these steps in order to launch the containers, ingest data, build the graph, and start the application.

### Step 1: Spin Up Containers & local LLM
You need Neo4j, Qdrant, and your local LLM running.

1. **Start Neo4j (via Docker Compose):**
   ```bash
   docker compose -f docker/docker-compose.yml up -d
   ```
2. **Start Qdrant (via Docker):**
   ```bash
   docker run -d -p 6333:6333 -p 6334:6334 -v qdrant_storage:/qdrant/storage qdrant/qdrant
   ```
   - there is no need to run this complex commands if you know how to start the docker containers, let me tell you one thing, if you have the qdrant and neo4j directly in one yml file, then running the command: 
   ```bash
   docker compose up -d 
   ```
      - be aware of where you are running the command, as in my case, I got different way to work with this containers but, one basic thing to notice is, the yml script is inside the folder naming docker, so 

3. **Start Local LLM:**
   Make sure you have an OpenAI-compatible API server (e.g., Llamafile, Ollama, LM Studio, llama.cpp or vLLM) running on port `8080` serving the target model (`raaedk/Qwen2.5-7B-Instruct-Q4_K_M-GGUF`). 
   - Here is some information you need to know about the local llm procedure, its not like you are directly starting the local model here, i've used llama.cpp to run local models, if you don't have idea about that, there will be a dedicated file which explains the procedure, so that you can also run local models efficiently even on low end systems.

---
### Step 2: Ingest Source Documents
Run the ingestion script to semantically chunk all `.txt` documents inside the `/data` directory and upload their vector embeddings to Qdrant:
```bash
python -m backend.injest_documents
```
- Run this command and wait for some time, don't do anything as it takes time to get the ingestion done.
---

### Step 3: Build the Knowledge Graph
Extract entity-relationship triplets from your ingested chunks using Groq (`llama-3.1-8b-instant`) and populate your Neo4j database:
```bash
python -m backend.graph_builder
```
> **Note:** The script has a built-in rate-limiting delay of 15 seconds per chunk to prevent hitting Groq rate limits. 
- same here too, run the command and wait for a while
---

### Step 4: Run the Backend API
Start the FastAPI backend server using Uvicorn:
```bash
uvicorn backend.main:app --reload
```
The API documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

### Step 5: Run the Streamlit Frontend Client
In a new terminal window (with the virtual environment activated), start the Streamlit web application:
```bash
streamlit run frontend/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser to chat with your Hybrid GraphRAG Chatbot.