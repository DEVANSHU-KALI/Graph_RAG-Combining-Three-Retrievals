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

#### B. Recursive Character Chunking
This is a much smarter step up (like LangChain's `RecursiveCharacterTextSplitter`). Instead of splitting blindly, it looks at a list of separators in order—usually double newlines (`\n\n`), single newlines (`\n`), spaces (` `), and finally characters.
* **How it works:** It tries to split paragraphs first. If a paragraph is still too big, it tries to split on sentences, then words, and so on. 
* **When to use it:** This is the default go-to for general, unstructured text (like articles, blog posts, or standard reports) where you want to keep paragraphs and sentences intact without needing heavy computation.

#### C. Structure-Aware Chunking (Markdown/HTML/Code)
If you're dealing with markdown or code files, you can split based on the document's native structure. For example, you can split markdown files at H1, H2, or H3 headings, or split code files at class/function boundaries.
* **Why it's good:** It ensures that a code block or markdown section stays together as a single logical unit.
* **When to use it:** Essential when building a codebase assistant or indexing documentation that relies heavily on hierarchy, code blocks, or HTML layout structures.

#### D. Semantic Chunking
This is the method we are using in this project. Instead of counting characters or looking at static separators, it looks at the *meaning* of the text.
* **How it works:** It splits the document into sentences first, generates embeddings for each, calculates the similarity between consecutive sentences, and splits when the similarity drops below a threshold (like the 75th percentile).
* **When to use it:** Best when your documents contain complex narrative flows, transitions between different topics, or varying paragraph lengths, and you need highly cohesive context chunks where every line relates to the same core topic.
#### E. Agentic Chunking
This is the most advanced (and expensive) method. You pass the text to an LLM and literally ask it: "Read this text and tell me where the logical breaks are." 
* **The Catch:** It gives amazing quality, but it's very slow and costs a lot in API usage because you're calling an LLM just to chunk the data.
* **When to use it:** Best for high-value, complex documents (like legal contracts or financial statements) where missing a topic boundary could lead to severe reasoning errors, and cost/latency are not major concerns.

--- 

## 2) Embeddings and qdrant database.
Once we have our chunks, how does the system actually "understand" and search through them? This is where embeddings and vector databases come into play.

Let's demystify what an embedding actually is. Human language is full of nuance, double meanings, and context, which computers are terrible at processing. An embedding is basically a translator: it converts raw text into a long list of numbers (a high-dimensional vector) that represents its semantic meaning. 

If you think of a 2D graph, you can map points using `(x, y)` coordinates. In a vector space, we do the same thing, but instead of 2 dimensions, we use hundreds or thousands. For example, in this project, we use a 768-dimensional model. That means every single text chunk is converted into a list of 768 floating-point numbers. In this massive space, sentences with similar meanings (like "FastAPI is running on port 8000" and "The web API is active on port 8000") are placed very close to each other, while unrelated topics are placed far away.

### Types of Embedding Models
Not all embedding models work the same way. Depending on your search requirements, you generally choose between three main types:

#### A. Dense Embedding Models (Bi-Encoders)
This is the most common type and the one we are using in this project (specifically `sentence-transformers/all-mpnet-base-v2`).
* **How it works:** It processes a text chunk as a single unit and outputs a single dense vector representing the overall meaning of that text.
* **When to use it:** Perfect for general semantic search, finding conceptually similar topics, and building standard RAG pipelines.

#### B. Sparse Embedding Models (like SPLADE or BM25-based vectors)
Instead of compressing text into a dense array of abstract numbers, sparse models output vectors that are mostly zeros, with non-zero values representing specific vocabulary words and their relative importance.
* **How it works:** It maps text directly to a huge vocabulary dictionary, scoring the importance of individual words in the text.
* **When to use it:** Best when you need exact matches for product serial numbers, legal codes, specific naming conventions, or highly technical jargon where semantic search might get confused by similar-sounding words.

#### C. Late Interaction / Multi-Vector Models (like ColBERT)
Instead of squashing an entire document chunk into one single vector, late interaction models generate a separate embedding vector for *every single token* (word) in the text.
* **How it works:** During search, the query's individual word vectors are compared directly against all the individual word vectors of the documents, aligning them dynamically.
* **When to use it:** Best for high-precision search where word order, fine-grained details, and token-level relationships are extremely critical, though it requires significantly more memory and storage space.

### The Qdrant Vector Database
Why can't we just store these lists of 768 numbers in a standard SQL or NoSQL database? 
If you have thousands of chunks, finding the closest match using a standard database would require running a heavy math operation (like Cosine Similarity) against every single row, one by one. This is called a flat scan, and it completely grinds to a halt as your data grows.


Vector databases like **Qdrant** are built specifically to solve this problem:
* **HNSW Indexing (Hierarchical Navigable Small World):** Qdrant builds a multi-layered graph of the vectors (similar to a skip-list or a social network map). When a query comes in, it navigates this graph to quickly find the **Approximate Nearest Neighbors (ANN)** without scanning every single record. It's incredibly fast.
* **Payload Storage:** Along with the vector, Qdrant allows you to store a "payload"—which is just metadata like the raw text, the chunk ID, and the source file. This allows the backend to retrieve the actual text to feed to the LLM immediately after a vector match is found.

--- 

## 3) BM25 Index and Keyword Retrieval:
While semantic search is great at understanding conceptual meaning (like mapping "dog" to "puppy"), it has a major blind spot. It can completely miss exact keywords, serial numbers, variable names, or specific jargon, and start hallucinating. To prevent this, RAG systems run a parallel track called **Keyword Retrieval** (or Lexical Search). 

In this project, we use the industry standard algorithm for keyword search: **BM25 (Best Match 25)**. 
To understand BM25, think of it as a highly optimized version of TF-IDF. When you search for terms, BM25 scores each document chunk based on three main factors:
1. **Term Frequency (TF):** How many times a query word appears in a chunk. The more it appears, the higher the score. However, BM25 uses "term frequency saturation"—once a word appears 3 or 4 times, repeating it 100 more times won't keep inflating the score indefinitely.
2. **Inverse Document Frequency (IDF):** How common is this word across all your documents? Common filler words like "the" or "is" are ignored, while rare words like "FastAPI" or "Neo4j" are given massive priority.
3. **Document Length Normalization:** Long documents naturally contain more words. BM25 penalizes longer chunks so that short, highly-concentrated chunks matching the query are ranked higher.

In our project, we fetch the texts of all document chunks from Qdrant on startup, tokenize them (`text.lower().split()`), and build a `BM25Okapi` index that runs directly in RAM.

### Alternative Keyword Search Methods
Depending on your project's scale and search requirements, there are different ways to set up keyword search:
#### A. TF-IDF (Term Frequency-Inverse Document Frequency)
This is the mathematical predecessor to BM25.
* **How it works:** It simply multiplies how often a word appears in a document by how rare it is in the corpus.
* **The Catch:** It doesn't normalize for document length, meaning long documents are heavily favored. It also lacks term frequency saturation, meaning a document that repeats a keyword 50 times gets an unnaturally high score.
* **When to use it:** Mostly legacy projects, simple text classification tasks, or quick scripts where you need a super lightweight search without configuring extra libraries.

#### C. Full-Text Search Engines (like Elasticsearch, OpenSearch, or Meilisearch)
These are standalone, external databases designed purely for search.
* **How it works:** They build an inverted index (mapping every word to the documents it appears in) and store it on disk. They use BM25 under the hood but add extra search features.

* **Why they are powerful:** They support fuzzy matching (finding "FastAPI" even if you type "FatsAPI"), language stemming (treating "running" and "run" as the same word), and advanced filtering.
* **When to use it:** When your data scales to millions of documents, you need typo tolerance, or you want to update documents in real-time without recalculating the entire index in Python RAM.

--- 

## 4) Quantization:
When you want to run a Large Language Model (LLM) locally, the first obstacle you run into is memory (VRAM or RAM). A standard 7-billion parameter model (like Qwen2.5-7B) running at standard 16-bit floating-point precision (FP16) requires about **14 GB of memory** just to load. If you try to run it on a normal laptop, it will either crash or run at a painful speed of 1 token per second.

This is where **Quantization** comes to the rescue. It is a compression technique that shrinks model weights, allowing massive LLMs to run on consumer-grade hardware.

To understand quantization, imagine trying to measure a room. Instead of measuring down to the millimeter (which requires a lot of decimals and data), you round it to the nearest centimeter.  In deep learning, model weights are originally stored as highly precise decimal numbers (like `FP32` or `FP16`). Quantization maps these continuous high-precision decimals to a discrete,  lower-precision range—most commonly **8-bit (INT8)** or **4-bit (INT4)** integers.


For this project, we use a **4-bit quantized version** of the Qwen model (`Q4_K_M-GGUF`). This reduces the model's memory footprint from **14 GB down to roughly 4.7 GB**, allowing it to load easily and run quickly on standard CPU/GPU setups.

### Types of Quantization
There are different ways to quantize a model depending on when you compress it and the level of accuracy you need:

#### A. Post-Training Quantization (PTQ)
This is the standard approach used for local LLM deployment (and the one used for our GGUF model).

* **How it works:** The model is fully trained at high precision (FP16). Once training is complete, the weights are mapped and compressed to lower precision (like 4-bit or 8-bit) as a one-time conversion step.
* **The Catch:** Because the conversion happens after training, there is a minor loss in the model's reasoning accuracy (called quantization loss).