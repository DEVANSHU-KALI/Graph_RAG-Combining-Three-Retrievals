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

* **When to use it:** This is the go-to for running open-source models (Llama, Qwen, Mistral) locally using frameworks like `llama.cpp` or `Ollama`. It requires no retraining and is ready to use instantly.
#### B. Quantization-Aware Training (QAT)
Instead of compressing the model after training, the model is trained with quantization in mind.

* **How it works:** During the training process, the system simulates the effects of quantization. The model "learns" to adjust its weights to compensate for the lower precision limits.
* **Why it's good:** It retains almost 99% of the original model's accuracy, even at very low bitrates.

* **When to use it:** Used when you are developing custom models for low-power edge devices (like mobile phones, smart cameras, or microcontrollers) where every bit of accuracy and hardware efficiency counts.

#### C. Dynamic vs. Static Quantization
This refers to whether the activations (the intermediate math calculations inside the model during inference) are compressed along with the model weights.
* **Dynamic Quantization:** The model weights are quantized offline, but the activations are converted to lower precision dynamically during runtime. 

  * *When to use it:* Best for LLMs, where the main bottleneck is the time it takes to load massive weights from memory into the processor.
* **Static Quantization:** Both weights and activations are quantized offline beforehand by running a small sample dataset (calibration data) through the model to determine the active ranges.
  * *When to use it:* Best for Computer Vision models (like CNNs) where raw compute speed on the activations is the main bottleneck.

---

## 5) Graphs and Neo4j Database:
When we work with standard databases, we are used to storing data in grids (SQL tables) or document trees (NoSQL JSON). While these work great for isolated items, they struggle with connections. If you want to find out how various concepts are connected across several steps (multi-hop search), a relational database has to run highly resource-intensive `JOIN` operations that slow down quickly.
A **Graph Database** solves this by treating the relationships between data as first-class citizens, storing them directly alongside the data itself. 


### How Neo4j Works
Neo4j is the most popular Labeled Property Graph (LPG) database. It is structured around three core concepts:
1. **Nodes (Entities):** The actual objects or concepts in your graph (e.g., a node representing `FastAPI` or `Qdrant`).
2. **Relationships (Edges):** The directed connections between nodes (e.g., `FastAPI` -> `[USED_WITH]` -> `Qdrant`). In Neo4j, relationships always have a direction and a type.

3. **Properties:** Key-value pairs stored inside nodes or relationships (e.g., a node might have `{version: "0.110.0"}`, and a relationship might have `{difficulty: "easy"}`).

#### Index-Free Adjacency (The Core Engine)
In a traditional database, if you want to find a connection, the system has to scan a central index table. 
Neo4j uses **Index-Free Adjacency**. This means every node acts as a micro-index, holding direct memory pointers to its neighboring nodes. Traversing the graph is simply a matter of chasing memory pointers. Because of this, query performance depends only on the size of the subgraph you are searching, not the overall size of the entire database.
#### Cypher Query Language

To interact with Neo4j, we use **Cypher**, a declarative query language. Cypher is designed to be visual, using ASCII-art to represent graph patterns:
```cypher
// Matching a pattern: Source Node pointing to Target Node
MATCH (s:Entity)-[r:USED_WITH]->(t:Entity)
RETURN s.name, t.name
```
#### Alternative graph database

Depending on your project infrastructure and database requirements, there are different graph solutions available:

1) Labeled Property Graph (LPG) Databases (like Neo4j)
- How it works: Nodes and relationships can have properties, and queries are optimized for fast traversals and updates.
- When to use it: The gold standard for general GraphRAG, fraud detection, recommendation engines, and social network analysis where you need fast, intuitive, property-rich graphs.

2) RDF Triple Stores (like GraphDB, Amazon Neptune, or Apache Jena)
- How it works: Stores data as strict "triples" (Subject -> Predicate -> Object) using web URIs instead of plain strings. It uses SPARQL as its query language and supports logical reasoning engines.
- When to use it: Best for academic projects, semantic web integrations, public knowledge bases (like Wikidata), or metadata management where formal logic rules and globally standardized web ontologies are required.
3) Multi-Model Databases (like ArangoDB or OrientDB)
- How it works: Databases designed to store documents (JSON), key-value pairs, and graphs all inside a single database engine.
- When to use it: Ideal when your project already uses JSON documents heavily, and you want to query relations between those documents without the operational overhead of hosting both MongoDB and Neo4j.
4) Relational Databases with Graph Extensions (like PostgreSQL with Apache AGE)
- How it works: An extension that adds graph database functionality (including Cypher query support) directly on top of a standard PostgreSQL instance.
- When to use it: Best when you already have a mature PostgreSQL setup and want to experiment with graph features without introducing new database engines into your production stack.

--- 

## 6) Logging

When you first start coding, you are taught to use `print()` statements to debug your code and check if variables hold the right values. However, in production-grade systems, `print()` is practically useless. It prints directly to the standard output, gets mixed up with other terminal stdout, doesn't record timestamps, has no concept of severity (e.g., warning vs. critical crash), and won't write to log files automatically.

**Logging** is the structured practice of recording runtime events, system states, warnings, and errors during an application's execution. It acts as the "black box flight recorder" for your code.


### How Logging Works (The Core Concepts)
A standard logging system relies on three main components:
1. **Loggers:** The entry point. You call a logger in your code to submit a log record.
2. **Handlers:** Decide *where* the log record goes. It can send logs to the console (StreamHandler), write them to a local file (FileHandler), or ship them over the network to a central server.
3. **Formatters:** Define *what* the logs look like. They dynamically add context, like timestamps, log levels, file names, and line numbers.


#### The 5 Log Levels
Logs are classified by severity so that you can filter out noise during normal operations:
* `DEBUG` (10): Detailed diagnostic information, mostly useful for developers during local debugging.
* `INFO` (20): Confirmation that things are working as expected (e.g., "Server started on port 8000").
* `WARNING` (30): An indication that something unexpected happened, but the software is still running (e.g., "Low disk space").
* `ERROR` (40): A serious issue that prevented a specific function from executing (e.g., "Database connection timed out").
* `CRITICAL` (50): A fatal error indicating the entire program cannot continue running (e.g., "Out of memory, server shutting down").


### A Simple Python Example
Here is how you set up a basic logger:
```python
import logging
# 1. Get a logger instance
logger = logging.getLogger("TestLogger")
logger.setLevel(logging.WARNING) # Only log WARNING levels and higher

# 2. Set up handler and formatter
console_handler = logging.StreamHandler()
log_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# 3. Log messages
logger.info("This info log will NOT print (below WARNING level threshold)")
logger.warning("This is a warning message!")
```
**Output**
```bash
2026-07-13 23:29:54 | WARNING | This is a warning message!
```

### How Industry-Grade Systems Use Logging

In professional software development, logging isn't just about printing to a console. It is a critical layer of **Observability**.

#### Structured Logging (JSON format)

Rather than writing logs as plain-text sentences, production systems log events as JSON objects.

```json
{
  "timestamp": "2026-07-13T23:29:54Z",
  "level": "ERROR",
  "endpoint": "/chat",
  "latency_ms": 1250,
  "error_msg": "Neo4j timeout"
}
```

This allows automated log parsers to easily index, search, and filter logs by keys (like searching logs where `latency_ms > 1000`).

#### Centralized Log Management (The ELK Stack / Grafana Loki / Datadog)

In cloud architectures with dozens of servers, you cannot log into each machine to view text files. Servers stream their logs to a central database (like Elasticsearch or Loki) where engineers can query them in one dashboard.

#### Alerting Systems

Companies configure triggers based on logs.

For instance, if the system logs more than **10 `ERROR` events within 1 minute**, it immediately sends a notification to the engineering team via Slack or PagerDuty.

### How Logging is Used in Our Project

We have set up a custom logging system in our FastAPI backend to track requests and database operations.

#### 1. The Custom Logger (`logging.py`)

We initialize a custom logger named `HybridGraphRAG` and set the severity threshold to `INFO`.

We configure a console handler with the structured format:

```text
%(asctime)s | %(levelname)s | %(name)s | %(message)s
```

We also set:

```python
logger.propagate = False
```

to prevent logs from propagating up to the default root logger, preventing duplicate outputs in the terminal.

---

#### 2. FastAPI Request Logging Middleware (`middleware.py`)

We created a custom `LoggingMiddleware` class that intercepts every single incoming HTTP request.

- When a request arrives, it logs:

```text
INFO | INFO request received at /chat
```

- It starts a timer, executes the route, and calculates the difference:

```python
process_time = time.time() - start_time
```

- On completion, it logs:

```text
INFO | POST /chat completed with status code 200 in 0.8423 seconds
```

This is critical for tracking API latency and identifying slow query retrievals.

---

#### 3. Background Operations Logging

We import `logger` to track:

- Database health.

  Example:

```text
Successfully connected to Neo4j
```

- Text chunking progression.

  Example:

```text
Generated 144 chunks
```

- Qdrant database status.

---

### Alternative Logging Libraries in Python

While Python's standard `logging` library is solid, the industry often turns to modern alternatives.

#### A. Loguru

- **How it works**
  - A modern Python library designed to make logging fun.
  - It requires zero configuration boilerplate.

- **Why it's great**
  - Supports colorized terminal outputs by default.
  - Handles file rotation and compression out of the box.
  - Uses simplified syntax.

```python
from loguru import logger

logger.info("Just import and write, no setup needed!")
```

- **When to use it**
  - Highly recommended for scripts, fast prototypes, and mid-sized backend projects where you want rich console logging with zero setup.


#### B. Structlog

- **How it works**
  - A logging engine designed specifically for structured (key-value / JSON) logging.

- **Why it's great**
  - Optimized for speed.
  - Works by building nested contexts (e.g., binding a request ID to all downstream logs triggered by that request).

- **When to use it**
  - The default choice for production microservices deployed in Docker/Kubernetes environments where logs are forwarded to central systems like Datadog or ELK.

---

#### C. Application Performance Monitoring (APM) Agents (like Sentry or Datadog APM)

- **How it works**
  - Standalone agents integrated into your application code that automatically capture errors, print stack traces, and group repeating errors.

- **When to use it**
  - Used in production web apps alongside standard loggers to get detailed trace maps of user paths and automatic bug alerts.

--- 

## 7) Middleware

When a user submits a query from a frontend web app, the HTTP request doesn't just hit the database and return an answer immediately. Before the backend executes any route logic, several administrative tasks must occur:

- Is the user authenticated?
- Is the request payload safe?
- Should we compress the response?

Instead of writing this boilerplate logic inside **every single API endpoint**, we use **Middleware**.

Middleware is a software layer (or a chain of layers) that sits between the incoming request and your application's router. It intercepts the request **before** it reaches your endpoint, and intercepts the response **after** your endpoint finishes but **before** it is sent back to the client.

### How Middleware Works (The Dispatch Cycle)

Think of middleware as a security checkpoint at an airport. It can inspect, modify, or block requests entirely.

```text
Incoming Request
        │
        ▼
┌──────────────────────────────┐
│ Middleware                   │
│ • Start Timer                │
│ • Logging                    │
│ • Authentication             │
└──────────────┬───────────────┘
               │
               ▼
        FastAPI Router
               │
               ▼
      Processes Request
               │
               ▼
┌──────────────────────────────┐
│ Middleware                   │
│ • Stop Timer                 │
│ • Log Status                 │
│ • Modify Response            │
└──────────────┬───────────────┘
               │
               ▼
      Outgoing Response
```

1. **Request Interception**
   - The middleware receives the request first.
   - It can:
     - Add headers.
     - Check authentication tokens.
     - Start execution timers.

2. **The `call_next` Function**
   - If the request passes all checks, the middleware calls:

   ```python
   await call_next(request)
   ```

   - This passes the request down the chain to the actual FastAPI route handler (or the next middleware).

3. **Response Interception**
   - Once the endpoint finishes executing and returns a response, the middleware catches it on the way back out.
   - It can:
     - Inspect the response status code.
     - Calculate execution time.
     - Inject response headers.
     - Compress the response.


4. **Final Return**
   - The middleware forwards the finalized response to the client.

### How Industry-Grade Systems Use Middleware

In production web applications, middleware handles infrastructure-level tasks so developers don't have to repeat the same code in every endpoint.

#### Authentication & Authorization
 Authorization

- Intercepts incoming requests.
- Verifies JWT (JSON Web Tokens) or API keys.
- If the token is invalid or expired, the middleware immediately aborts the request and returns:

```text
401 Unauthorized
```

before the router or database processes anything.

---

#### CORS (Cross-Origin Resource Sharing)

- Browsers block frontend applications from requesting data from backends running on different ports or domains.
- CORS middleware automatically injects headers such as:

```text
Access-Control-Allow-Origin
```

to authorize specific domains.

#### Rate Limiting (IP Throttling)

- Tracks how many requests come from a single IP address.
- If a user exceeds a threshold (e.g., **60 requests per minute**), the middleware returns:


```text
429 Too Many Requests
```

to protect the backend from Denial-of-Service (DDoS) attacks.

---

#### Response Compression (Gzip)

- Automatically compresses response payloads before sending them over the network.
- Reduces:
  - Bandwidth usage.
  - Page load time.


### How Middleware is Used in Our Project

In our backend, we use custom ASGI middleware to measure and log performance.

- **File:** `middleware.py`
- **Class Name:** `LoggingMiddleware` *(extends Starlette's `BaseHTTPMiddleware`)*

#### The Implementation

```python
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Intercept Request: Start a timer and log the incoming endpoint
        start_time = time.time()
        logger.info(f"{request.method} request received at {request.url.path}")

        # 2. Pass down: Await the execution of the actual route
        response = await call_next(request)

        # 3. Intercept Response: Calculate time elapsed
        process_time = time.time() - start_time

        # 4. Log performance metrics and return response
        logger.info(
            f"{request.method} {request.url.path} "
            f"completed with status code {response.status_code} "
            f"in {process_time:.4f} seconds"
        )
        return response
```

This is registered globally in `main.py`.

Because of this middleware, every query sent to the `/chat` endpoint is timed, allowing us to monitor how fast the combined RAG searches (**Semantic + BM25 + Graph**) execute in real time.

### Alternative Request Interception Methods

You don't always have to use global middleware. Depending on your needs, you can choose these alternatives.

#### A. FastAPI Dependencies (Dependency Injection)

FastAPI has a native dependency injection framework (`Depends`).

- **How it works**
  - You write an interception function and attach it directly to specific endpoints instead of applying it globally.

- **When to use it**
  - When you only want interception on **some** routes.
  - Example:
    - `/admin` → Check admin credentials.
    - `/health` → Public.
    - `/chat` → Public.


#### B. Reverse Proxy (Nginx, Caddy, or Cloudflare)

Handle request-level operations completely **outside** of your Python application.

- **How it works**
  - Place a web server (such as **Nginx**) or a CDN (such as **Cloudflare**) in front of your FastAPI server.
  - Nginx handles:
    - SSL decryption.
    - Rate limiting.
    - Gzip compression.
  - It then forwards the clean request to Python.

- **When to use it**
  - This is the industry standard for production deployments.
  - Offloading network-related work from Python allows the CPU to spend its time running the RAG pipeline instead.

--- 

## 8) RAG Evaluations:
Building a retrieval-augmented chatbot is relatively easy, but proving that it actually works—and doesn't make things up—is notoriously difficult. In traditional software development, you write unit tests with exact assertions (e.g., `assert add(2, 2) == 4`). But LLM outputs are free-form, variable, and subjective, making standard assertions completely useless.


**RAG Evaluation** is the systematic process of measuring the quality of your retrieval systems and the accuracy of your generated responses using mathematical metrics and test datasets.

### How RAG Evaluation Works (LLM-as-a-Judge)
Because humans cannot manually read and grade thousands of chatbot conversations every day, modern evaluation frameworks use a technique called **LLM-as-a-Judge**. 
You feed a highly capable LLM (like GPT-4 or Llama 3.1 70B) a test case containing:
1. **The User Query:** What was asked.
2. **The Actual Output:** What the chatbot answered.
3. **The Retrieved Context:** The source documents retrieved to answer the query.
4. **The Ground Truth (Optional):** The gold-standard correct answer written by a human.


The judge LLM is prompted with strict mathematical scoring guidelines to analyze these parameters and output a normalized score between `0.0` (failing) and `1.0` (perfect).

### Evaluation Frameworks Available Online
There are several specialized libraries in the open-source ecosystem designed to automate this process:
#### A. Ragas (Retrieval Augmented Generation Assessment)
* **What it is:** The industry-standard framework built specifically for testing RAG pipelines.

* **Why we use it:** It focuses heavily on evaluating the relationship between the query, the retrieved contexts, and the final response. It calculates precise scores for retrieval accuracy.

#### B. DeepEval (by Confident AI)
* **What it is:** An open-source evaluation framework built to integrate directly with PyTest.
* **Why we use it:** It is extremely developer-friendly, provides a clean dashboard to track test runs, and features robust, standalone metrics for hallucinations, bias, and toxic outputs.
#### C. TruLens (by TruEra)
* **What it is:** A testing framework built around the concept of the **RAG Triad**.
* **Why we use it:** The RAG Triad breaks evaluation into three core relationships: Context Relevance (Did we get good docs?), Groundedness (Is the answer based *only* on those docs?), and Answer Relevance (Does the answer address the query?).

#### D. Phoenix (by Arize)
* **What it is:** An observability and evaluation tool designed to test models using in-memory datasets.
* **Why we use it:** Excellent for real-time trace analysis and tracking down step-by-step failures in complex LLM agent chains.

### How Evaluations are Implemented in Our Project
In our project, we chose to use both **Ragas** and **DeepEval**. We run these evaluations using Groq's `llama-3.1-8b-instant` as our judge LLM. 

Because we use Groq's free tier, we configured a LangChain `InMemoryRateLimiter` set to `0.2 requests per second` (1 call every 5 seconds) to ensure our evaluations do not crash from rate limit errors (`HTTP 429`).
#### 1. Ragas Implementation ([ragas_evaluation.py](file:///d:/projects/graph_rag/backend/evaluations/ragas_evaluation.py))
We evaluate our system across a dataset of test cases using four core Ragas metrics:
* **Faithfulness:** Measures if the generated answer is grounded *only* in the retrieved context. It checks if the model introduced outside assumptions or hallucinated facts.
* **Answer Relevancy:** Measures if the generated response directly addresses the user's question, penalizing answers that are too vague, incomplete, or off-topic.
* **Context Precision:** Evaluates the quality of our retrieval pipeline. It checks if the most relevant text chunks were ranked at the top of the context block.
* **Context Recall:** Compares the retrieved context against a human-written Ground Truth to verify if the search channels actually gathered all the facts required to answer the question.

#### 2. DeepEval Implementation ([deepeval_evaluation.py](file:///d:/projects/graph_rag/backend/evaluations/deepeval_evaluation.py))
We wrote a custom `GroqEvaluator` class extending `DeepEvalBaseLLM` to run evaluations locally, focusing on a single high-fidelity metric:
* **Hallucination Metric:** The judge model extracts individual factual statements from our chatbot's answer, checks them against the retrieved contexts one-by-one, and calculates a score. If the score exceeds `0.5`, the test case is flagged as a hallucination failure.

---

## 9) Langsmith Tracing: Observe anything 

langsmith is a part of langchain, specifically built to let users inspect very deeply into their system whatever they got. 

Few changes in your system lets you see whatever is passing in and out through a whatever function you want to inspect.

langsmith give you the power of observability. 

### now lets see how I implemented langsmith tracing, and also show you how can you enable it and get your tracing.

All starts with adding some new lines in the `.env` file.

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY='api_key'
LANGCHAIN_PROJECT=hybrid-graphrag
```
  - The first line enable the tracing
  - Go into the langsmith webpage, create a api key there, copy that and replace this term 'api_key' with that key.
  - The third line, the name of tracing, choose whatever you want.

The second change, which function you want to trace (observe)
- In my case, I only wanted to peak into the `rag_pipeline` function from the "grah_rag/pipelines/rag_pipeline.py".
- simply import traceable from the langsmith and add a decorator for above whatever function you want.
- see the script and you can see there.

Now normally run your project, execute the part of project which makes the `function tied with this traceable decorator` do some process, so that it shows its trace in the langsmith page.

Finally, go and search **langsmith** in browser, login the page and open it.

On the left panel, you can find a term `tracing`, click that you can see you tracing there.
- click on that and see what all that function got and what did it gave as output.

- use this for only specific function, which actually do some work. 