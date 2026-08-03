This file contains the explanation of rag_pipeline.py

## rag_pipeline.py

### What Does This Script Do & Why is it Used?
In simple terms, this script is the **brain of our chat pipeline**. It orchestrates the entire runtime query process: it runs the search queries across our databases, combines and ranks the results, structures a strict prompt, and calls our local LLM to write the final, citation-backed answer.
