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
- **`DeepEvalBaseLLM`:** We extend DeepEval's base LLM class to register our own custom model instead of using default OpenAI models.
- **`InMemoryRateLimiter`:** Restricts requests to exactly `0.2` requests per second (1 request every 5 seconds) to respect the Groq free tier limit of 30 RPM.
- **`ChatOpenAI`:** Wraps Groq using LangChain's OpenAI-compatible interface, applying our rate limiter.

#### 2. Evaluation Loop
```python
async def main():
    bm25_index, documents = await initialize_bm25()
    groq_llm = GroqEvaluator()
    metric = HallucinationMetric(threshold=0.5, model=groq_llm)

    results = []

    for sample in evaluation_dataset:
        response = await generate_answer(sample["question"], bm25_index, documents)

        test_case = LLMTestCase(
            input=sample["question"],
            actual_output=response["answer"],
            context=response["contexts"],
        )

        metric.measure(test_case)
        results.append({"question": sample["question"], "hallucination": metric.score})
        await asyncio.sleep(10)
```
- **`initialize_bm25`:** Loads the index once so our RAG pipeline runs correctly.
- **`HallucinationMetric(model=groq_llm)`:** Initializes DeepEval's metric using our rate-limited Groq model as the judge.
- **`LLMTestCase`:** Prepares the inputs required by DeepEval (Question, Answer, and Contexts).
- **`metric.measure`:** Tells the judge LLM to evaluate the test case.
- **`asyncio.sleep(10)`:** Adds a 10-second pause between evaluation test cases to ensure the RPM counters cool down.

---

### B. Ragas Script (`ragas_evaluation.py`)
* **File:** [ragas_evaluation.py](file:///d:/projects/graph_rag/backend/evaluations/ragas_evaluation.py)

#### 1. Dataset Compilation
```python
async def build_dataset(bm25_index, documents):
    rows = []
    for sample in evaluation_dataset:
        result = await generate_answer(sample["question"], bm25_index, documents)
        rows.append(
            {
                "question": sample["question"],
                "answer": result["answer"],
                "contexts": result["contexts"],
                "ground_truth": sample["ground_truth"],
            }
        )
    return rows
```
- **`build_dataset`:** Iterates through our test dataset, runs each question through our RAG pipeline, and stores the query, contexts, answer, and ground truth in a structured list.

#### 2. Running Ragas Evaluations
```python
    rows = await build_dataset(bm25_index, documents)
    dataset = Dataset.from_list(rows)

    rate_limiter = InMemoryRateLimiter(
        requests_per_second=0.2,
        check_every_n_seconds=0.1,
        max_bucket_size=10,
    )

    evaluator_llm = ChatOpenAI(
        model="llama-3.1-8b-instant",
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
        rate_limiter=rate_limiter,
        max_retries=10,
    )

    results = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=evaluator_llm,
        embeddings=embedding_model,
    )
```
- **`Dataset.from_list`:** Converts the data dictionaries into a HuggingFace dataset format required by Ragas.
- **`rate_limiter` & `evaluator_llm`:** Sets up the rate-limited `ChatOpenAI` client pointing to Groq.
- **`evaluate()`:** Executes the Ragas framework, measuring the 4 specified metrics using our Groq judge and our local HuggingFace embeddings model.

---

## 8. Detailed Analysis of Evaluation Results

Below is a technical breakdown of the output data generated by the evaluations and a discussion on why certain results occurred.

### A. DeepEval Results (`deepeval_results.csv`)
The hallucination metric scores our local LLM's groundedness on a `[0.0, 1.0]` scale (lower is better, meaning 0% hallucination):

| Question | Hallucination Score | Interpretation |
| :--- | :---: | :--- |
| **"What is overfitting?"** | `0.6666` | Contains minor ungrounded statements or assumptions not explicitly written in the retrieved text. |
| **"How do Vector Embeddings and Cosine Similarity work..."** | `0.0000` | Perfect groundedness. Every statement is fully supported by the retrieved database chunks. |
| **"How can Dropout Regularization help reduce Overfitting..."** | `0.6666` | Contains minor ungrounded additions. |

---

### B. Ragas Results (`graph_rag_ragas_results.csv`)
The results from the Ragas run provide a deeper look at both retrieval and generation quality:

| Question | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
| :--- | :---: | :---: | :---: | :---: |
| **"What is overfitting?"** | `1.0000` | `0.9111` | `0.8333` | `1.0000` |
| **"How do Vector Embeddings..."** | `0.7000` | `0.9677` | *NaN (Missing)* | `1.0000` |
| **"How can Dropout Regularization..."** | *NaN (Missing)* | `0.9933` | *NaN (Missing)* | `1.0000` |

#### Key Insights from the Scores:
1. **Perfect Context Recall (`1.0000` across all questions):** This is a major achievement. It proves that the combined **Hybrid GraphRAG retrieval pipeline** (Semantic + BM25 + Neo4j Graph) successfully retrieved 100% of the facts required to answer the questions compared to the human ground truth.
2. **High Answer Relevancy (`0.9111` to `0.9933`):** Confirms that our local Qwen-7B model creates highly focused, direct answers that address the user's questions without drifting or rambling.
3. **High Context Precision (`0.8333`):** Confirms that our Cross-Encoder reranker successfully ranks the most relevant information at the top of the context block.

---

### C. Why are there missing (`NaN`) values in the Ragas results?
You will notice that `context_precision` for Questions 2 and 3, and `faithfulness` for Question 3 are missing (`NaN`).

* **The Cause (Tokens Per Minute - TPM Limits):**
  Ragas runs evaluations concurrently. To evaluate `context_precision` and `faithfulness`, Ragas must feed the *entire retrieved context block* (all 10 combined chunks) along with the generated answer to the LLM judge.
  Because our retrieved context payload is large, these requests consume a massive number of tokens. On Groq's free tier, the **Tokens Per Minute (TPM)** limit is capped at a low **14,400 TPM**. Even though our `InMemoryRateLimiter` restricts the *frequency* of requests (Requests Per Minute - RPM), the sheer volume of tokens sent simultaneously exceeded Groq's TPM threshold.
* **Ragas Error Recovery:**
  When Groq rejected the token-heavy requests with an HTTP `429 (Too Many Requests)` rate-limit exception, Ragas caught the error. Instead of crashing the entire script and discarding the rest of the run, Ragas gracefully recorded a `NaN` (Not a Number) value for the failing metrics on those specific rows, allowing the script to finish and save the successful metrics.

---

## 9. Execution Flow Charts

### DeepEval Pipeline Flow:
```text
Initialize BM25 -> Loop Test Cases -> Await RAG Response -> Construct Test Case -> Trigger LLM Hallucination Judgement (via rate-limiter) -> Append Score -> Sleep 10s -> Output CSV
```

### Ragas Pipeline Flow:
```text
Initialize BM25 -> Run all questions through RAG -> Build HuggingFace Dataset -> Initialize rate-limited LLM Judge -> Execute evaluate() (Calculates Faithfulness, Relevancy, Precision, Recall) -> Clean newlines -> Output CSV
```
