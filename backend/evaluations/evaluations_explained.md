# RAG Evaluations Explanation

This document explains the evaluation framework implemented in the project. It details the necessity of evaluations in RAG, the specific libraries and metrics chosen, how the rate-limiting bottlenecks were resolved, and provides a complete code walkthrough for the scripts inside the `backend/evaluations/` directory.

---

## 1. The Need for Evaluation in RAG

In traditional software development, code is tested using deterministic assertions (e.g., verifying that a function returns a specific integer). However, Retrieval-Augmented Generation (RAG) applications deal with natural language and non-deterministic LLM generations. 

Standard assertions are useless for checking free-form answers. We need automated evaluations to measure:
1. **Hallucination Detection:** Does the model generate facts not supported by our document database?
2. **Retrieval Quality:** Are we fetching the correct, relevant document chunks to feed the prompt?
3. **Generation Quality:** Is the LLM producing high-quality answers that directly address the user's question?

Evaluations run a test dataset through the pipeline, grading search results and final answers to generate normalized scores.

---

## 2. Evaluation Frameworks and Chosen Metrics

Our project leverages two popular RAG evaluation frameworks: **Ragas** and **DeepEval**, using Groq's `llama-3.1-8b-instant` as our judge model. 

Instead of running every metric available, we selected **5 specific metrics** to prevent resource exhaustion:

| Framework | Metric | What It Measures | Target |
| :--- | :--- | :--- | :--- |
| **DeepEval** | **Hallucination** | Compares the generated answer against the retrieved context. Scores close to `0.0` represent high groundedness; scores close to `1.0` indicate hallucinated claims. | Generation |
| **Ragas** | **Faithfulness** | Verifies if all factual statements in the generated response can be directly inferred from the retrieved contexts. | Generation |
| **Ragas** | **Answer Relevancy** | Assesses if the generated response directly answers the user query, penalizing redundant or off-topic information. | Generation |
| **Ragas** | **Context Precision** | Measures if the most relevant retrieved text chunks were ranked at the top of the context block. | Retrieval |
| **Ragas** | **Context Recall** | Compares the retrieved context against the human-written Ground Truth to verify if the search pipeline gathered all necessary facts. | Retrieval |

---

## 3. The Rate-Limiting Problem & Solution

### The Problem
Automated evaluation requires the judge LLM to perform multiple reasoning steps per metric (e.g., extracting factual claims, checking alignment, generating reasoning steps). For a dataset of just 3 questions evaluated across 5 metrics, the system can trigger **dozens of API calls** in quick succession.

Under Groq’s free-tier limits, running these scripts at full speed immediately triggers **HTTP 429 (Too Many Requests)** errors and crashes the pipeline.

### The Solutions Implemented
To ensure stable, error-free execution, we implemented three solutions:
1. **Metric Limitation:** We strictly restricted our evaluation to the 5 critical metrics listed above, avoiding unnecessary API calls.
2. **In-Memory Rate Limiting:** We wrapped the judge client with LangChain’s `InMemoryRateLimiter` set to `0.2 requests_per_second`. This guarantees a **5-second delay** between API requests.
3. **Execution Sleep Buffers:** In `deepeval_evaluation.py`, we added an explicit `await asyncio.sleep(10)` delay between test cases to allow the API limits to reset.

---

## 4. The Evaluation Dataset (`evaluation_dataset.py`)

* **File:** [evaluation_dataset.py](file:///d:/projects/graph_rag/backend/evaluations/evaluation_dataset.py)

The dataset contains a list of dictionaries, representing our testing benchmark. Each sample contains the user's `question` and a human-compiled `ground_truth` answer:

```python
evaluation_dataset = [
    {
        "id": 1,
        "question": "What is overfitting?",
        "ground_truth": "Overfitting occurs when a machine learning model memorizes training data...",
    },
    ...
]
```

---

## 5. How to Run the Evaluations

To run the evaluations locally, navigate to the project root directory, activate your virtual environment, and run the following terminal commands:

### Run DeepEval Evaluation:
```bash
PYTHONPATH=. python backend/evaluations/deepeval_evaluation.py
```

### Run Ragas Evaluation:
```bash
PYTHONPATH=. python backend/evaluations/ragas_evaluation.py
```

---

## 6. Evaluation Results Generated

Upon execution, the scripts generate CSV files summarizing the run metrics:
* **DeepEval Output (`deepeval_results.csv`):** Stores columns `question` and the calculated `hallucination` score.
* **Ragas Output (`evaluation_results.csv`):** Stores columns `question`, `answer`, `contexts`, `ground_truth`, and the calculated Ragas metric scores (`faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`).

---

## 7. Code Breakdown

### A. DeepEval Script (`deepeval_evaluation.py`)
* **File:** [deepeval_evaluation.py](file:///d:/projects/graph_rag/backend/evaluations/deepeval_evaluation.py)

#### 1. Custom Groq Judge Model
```python
class GroqEvaluator(DeepEvalBaseLLM):
    def __init__(self, model_name="llama-3.1-8b-instant"):
        self.model_name = model_name
        
        # Configure rate limiter for Groq to stay under 30 RPM
        rate_limiter = InMemoryRateLimiter(
            requests_per_second=0.2,
            check_every_n_seconds=0.1,
            max_bucket_size=10,
        )
        
        self.client = ChatOpenAI(
            model=model_name,
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            rate_limiter=rate_limiter,
            max_retries=10,
        )
```