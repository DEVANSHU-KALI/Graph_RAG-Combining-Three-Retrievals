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

