import asyncio
import pandas as pd
from deepeval.metrics import HallucinationMetric
from deepeval.test_case import LLMTestCase
from deepeval.models.base_model import DeepEvalBaseLLM
from langchain_openai import ChatOpenAI
from langchain_core.rate_limiters import InMemoryRateLimiter

from backend.core.config import GROQ_API_KEY
from backend.evaluations.evaluation_dataset import evaluation_dataset
from backend.pipelines.rag_pipeline import generate_answer
from backend.retrievals.bm25_retrieval import initialize_bm25


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

    def load_model(self):
        return self.client

    def get_model_name(self):
        return self.model_name

    def generate(self, prompt: str) -> str:
        return self.client.invoke(prompt).content

    async def a_generate(self, prompt: str) -> str:
        res = await self.client.ainvoke(prompt)
        return res.content


async def main():
    # Initialize BM25 index and documents once for evaluation
    bm25_index, documents = await initialize_bm25()

    # Configure Groq as the judge model for DeepEval
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
        
        # Rate limiting delay between evaluation test cases
        await asyncio.sleep(10)

    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(current_dir, "deepeval_results.csv")
    pd.DataFrame(results).to_csv(output_path, index=False)


if __name__ == "__main__":
    asyncio.run(main())
