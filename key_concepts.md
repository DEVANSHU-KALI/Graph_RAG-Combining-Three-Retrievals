## Key concepts used in this project explained briefly.

### 1) Chunking:
Now let's come to the very first basics of a RAG system—specifically when we're dealing with semantic retrieval. Why do we even split documents?
If you try to feed an entire 50-page document or database dump directly to a model, or try to search it all at once, you'll hit a couple of walls. First, LLMs have limits on how much text they can read at once (the context window). Second, if you convert a massive document into a single vector embedding, the semantic meaning gets "diluted." The specific details get lost in the noise. Chunking is just the process of breaking that raw text down into smaller, self-contained pieces so that retrieval actually works.