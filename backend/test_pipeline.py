import os
from dotenv import load_dotenv

load_dotenv("backend/.env")

from backend.app.schemas.query import TextQueryRequest
from backend.app.services.evaluator import GroundingEvaluator
from backend.app.services.llm import LLMService
from backend.app.services.prompts import build_grounded_prompt
from backend.app.services.retrieval import HybridRetriever


def test_pipeline():
    print("=" * 60, flush=True)
    print("Testing Complete RAG Pipeline Locally (Same as /api/query)", flush=True)
    print("=" * 60, flush=True)

    query = "What is a corporation?"
    print(f"\n1. Query: '{query}'", flush=True)

    retriever = HybridRetriever()
    retrieval_res = retriever.retrieve(query=query, language="en-IN", top_k=5)
    candidates = retrieval_res["candidates"]
    latencies = retrieval_res["latency_breakdown"]

    print(f"\n2. Hybrid Retrieval: Retrieved {len(candidates)} candidates (total {latencies['total_retrieval_ms']}ms)", flush=True)
    for i, c in enumerate(candidates[:3]):
        print(f"   [{i+1}] Score: {c['final_score']:.4f} | RRF: {c.get('rrf_score')} | Dense: {c.get('dense_rank')} | BM25: {c.get('sparse_rank')}", flush=True)
        print(f"       Text: {c['text'][:120]}...", flush=True)

    prompt_data = build_grounded_prompt(query=query, retrieved_chunks=candidates, language="en-IN")
    print(f"\n3. Prompt Built: {len(prompt_data['user_prompt'])} chars, injection={prompt_data['is_injection_detected']}", flush=True)

    llm_service = LLMService()
    llm_res = llm_service.generate_grounded_answer(prompt_data=prompt_data, retrieved_chunks=candidates)
    answer = llm_res["answer"]
    print(f"\n4. LLM Answer (Mocked: {llm_res.get('mock', False)}, Model: {llm_res.get('model_used')}):\n   {answer}", flush=True)

    evaluator = GroundingEvaluator()
    eval_res = evaluator.verify_grounding(answer=answer, retrieved_chunks=candidates)
    print(f"\n5. Grounding Verification:", flush=True)
    print(f"   - Grounded:      {eval_res['grounded']}", flush=True)
    print(f"   - Confidence:    {eval_res['confidence']:.4f}", flush=True)
    print(f"   - Should Answer: {eval_res['should_answer']}", flush=True)
    print(f"   - Status:        {eval_res['status']}", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    test_pipeline()
