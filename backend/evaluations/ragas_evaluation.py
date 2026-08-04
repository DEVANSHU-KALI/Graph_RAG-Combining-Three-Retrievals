import asyncio
import pandas as pd
from datasets import Dataset
from langchain_openai import ChatOpenAI
from langchain_core.rate_limiters import InMemoryRateLimiter

from backend.core.config import GROQ_API_KEY
from backend.embedding_model import embedding_model
from backend.evaluations.evaluation_dataset import evaluation_dataset
from backend.pipelines.rag_pipeline import generate_answer
from backend.retrievals.bm25_retrieval import initialize_bm25
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)


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


async def main():
    # Initialize BM25 index and documents once for evaluation
    bm25_index, documents = await initialize_bm25()

    rows = await build_dataset(bm25_index, documents)
    dataset = Dataset.from_list(rows)

    # Configure an in-memory rate limiter to stay below Groq's 30 RPM free limit.
    # 0.2 requests_per_second restricts requests to exactly 1 call every 5 seconds.
    rate_limiter = InMemoryRateLimiter(
        requests_per_second=0.2,
        check_every_n_seconds=0.1,
        max_bucket_size=10,
    )

    # Use Groq via OpenAI-compatible SDK for Ragas evaluation
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

    df = results.to_pandas()
    # Clean up newlines in cells to prevent row splitting in simple CSV viewers
    for col in df.columns:
        df[col] = df[col].apply(lambda x: x.replace("\n", " ") if isinstance(x, str) else x)
        df[col] = df[col].apply(lambda x: [item.replace("\n", " ") for item in x] if isinstance(x, list) else x)
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(current_dir, "evaluation_results.csv")
    df.to_csv(output_path, index=False)
    print(df)


if __name__ == "__main__":
    asyncio.run(main())
