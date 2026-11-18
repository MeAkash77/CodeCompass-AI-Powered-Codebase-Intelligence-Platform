import os
import ast
import time
import numpy as np
import requests
from typing import List, Optional
from datasets import Dataset
from langchain.schema import LLMResult, Generation
from langchain.embeddings import HuggingFaceEmbeddings
from ragas import evaluate
from ragas.llms.base import BaseRagasLLM
from ragas.metrics import faithfulness, context_precision, context_recall, answer_relevancy
from google import genai
from google.genai import types
from dotenv import load_dotenv

class GeminiModel(BaseRagasLLM):
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash-lite"):
        super().__init__()
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def generate_text(self, prompt, n: int = 1, temperature: float = 0.01, stop: Optional[List[str]] = None, callbacks=None,  **kwargs):
        """ Sync generation for RAGAS """
        try:
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=8192
            )
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
            text = response.text or ""
        except Exception as e:
            print(f"Gemini generation error: {e}")
            text = ""
        gen_objs = [Generation(text=text) for _ in range(n)]
        return LLMResult(generations=[gen_objs])

    async def agenerate_text(self, prompt, n: int = 1, temperature: float = 0.01, stop: Optional[List[str]] = None, callbacks=None,  **kwargs):
        """ Async fallback for RAGAS (just calls sync) """
        return self.generate_text(prompt, n, temperature, stop, callbacks, **kwargs)

    def is_finished(self, response: LLMResult) -> bool:
        try:
            for generation_list in response.generations:
                for generation in generation_list:
                    if not generation.text or generation.text.strip() == "":
                        return False
            return True
        except Exception:
            return False


load_dotenv()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
API_URL = "http://localhost:8000/ask"

llm = GeminiModel(GEMINI_API_KEY, GEMINI_MODEL)
embedding = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5")


def ask_rag_service(question: str):
    """ Send a prompt to the code-compass API and get back the response and citations """
    payload = {"prompt": question, "max_tokens": 8192}
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            print(f"code-compass service error: {data.get('error')}")
            return None

        data = data["data"]
        return {
            "question": question,
            "answer": data.get("content"),
            "citations": data.get("citations", [])
        }
    except Exception as e:
        print(f"Request failed: {e}")
        return None


def evaluate_with_ragas(question: str, answer: str, contexts: list, reference: str = ""):
    """ Evaluate a single RAG response using RAGAS metrics """
    context_texts = []
    for c in contexts:
        if isinstance(c, dict):
            context_texts.append(c.get('content', ''))
        elif isinstance(c, str):
            context_texts.append(c)

    dataset = Dataset.from_dict({
        "user_input": [question],
        "response": [answer],
        "retrieved_contexts": [context_texts],
        "reference": [reference or ""]
    })

    metric_list = [faithfulness, context_precision, context_recall, answer_relevancy]
    metric_results = {}

    for metric in metric_list:
        results = evaluate(
            dataset=dataset,
            metrics=[metric],
            llm=llm,
            embeddings=embedding,
            raise_exceptions=True,
            return_executor=False,
        )
        metric_results[metric.name] = results.scores[0][metric.name] # type: ignore
        time.sleep(60)
    return metric_results


def main():
    print("Starting RAGAS evaluation for local RAG service...\n")
    start_time = time.time()
    all_scores = {
        "faithfulness": [],
        "context_precision": [],
        "context_recall": [],
        "answer_relevancy": [],
    }

    file_path = "evaluation_test_data.txt"
    with open(file_path, "r", encoding="utf-8") as f:
        file_content = f.read()
    test_queries = ast.literal_eval(file_content)

    for question, reference in test_queries:
        print(f"    Query: {question}")
        result = ask_rag_service(question)
        if not result:
            continue

        answer = result["answer"]
        contexts = result["citations"]
        print(f"    Answer: {answer}")
        print(f"    Retrieved contexts: {len(contexts)}\n")

        ragas_result = evaluate_with_ragas(question, answer, contexts, reference)
        print(f"    RAGAS Evaluation Results:")
        for metric, score in ragas_result.items():
            print(f"    {metric}: {score:.3f}")
            all_scores[metric].append(score)
        print("-" * 60)
        time.sleep(60)

    print("\nAggregate Metrics Summary:")
    for metric, values in all_scores.items():
        if values:
            mean_val = np.mean(values)
            median_val = np.median(values)
            print(f"   {metric}: Mean = {mean_val:.3f}, Median = {median_val:.3f}")
        else:
            print(f"   {metric}: No data")

    end_time = time.time()
    elapsed_seconds = end_time - start_time
    elapsed_minutes = elapsed_seconds / 60
    
    print("\nTotal Evaluation Time:")
    print(f"{elapsed_seconds:.1f} seconds ({elapsed_minutes:.2f} minutes)")
    print("\nEvaluation complete.")


if __name__ == "__main__":
    main()
