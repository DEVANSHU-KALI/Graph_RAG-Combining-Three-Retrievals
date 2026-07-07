# Key concepts used in this project explained briefly.

## 1) Chunking:
Now let's come to the very first basics of a RAG system—specifically when we're dealing with semantic retrieval. Why do we even split documents?
If you try to feed an entire 50-page document or database dump directly to a model, or try to search it all at once, you'll hit a couple of walls. First, LLMs have limits on how much text they can read at once (the context window). Second, if you convert a massive document into a single vector embedding, the semantic meaning gets "diluted." The specific details get lost in the noise. Chunking is just the process of breaking that raw text down into smaller, self-contained pieces so that retrieval actually works.

Once we split the text, we convert each piece (or chunk) into a vector embedding and store it in Qdrant database along with its metadata (like the source filename and chunk ID).

### Alternative Chunking Strategies

Depending on the nature of your documents and how much quality you want, you can use different chunking strategies. No single method works best for all types of data.
### A. Character Splitting (Fixed-Size Chunking)
This is the most basic approach. You just split the text every N characters (like 500 characters) and add an overlap (say, 50 characters) so you don't lose context at the split boundary.
* **How it works:** It’s a simple sliding window that counts characters and cuts the text.
* **The Catch:** It's super fast, but it's completely blind to structure. It will split right in the middle of a word or sentence, which breaks the semantic meaning.
* **When to use it:** Best for highly uniform data, raw logs, or structured strings where formatting and sentence structures are not important, or when you need a super-fast, low-compute baseline.
