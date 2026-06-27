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