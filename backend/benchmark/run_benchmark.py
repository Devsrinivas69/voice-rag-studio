import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.config import get_settings
from backend.app.monitoring.metrics import logger
from backend.app.services.evaluator import GroundingEvaluator
from backend.app.services.llm import LLMService
from backend.app.services.prompts import build_grounded_prompt
from backend.app.services.retrieval import HybridRetriever


def calculate_percentile(data: List[float], p: float) -> float:
    """Calculates requested percentile value for a list of floats."""
    if not data:
        return 0.0
    return round(float(np.percentile(data, p)), 2)


def calculate_recall_at_k(candidates: List[Dict[str, Any]], target_doc_id: str, k: int) -> float:
    """Returns 1.0 if target_doc_id is present within top-K candidates, else 0.0."""
    top_k_candidates = candidates[:k]
    for c in top_k_candidates:
        if c.get("document_id") == target_doc_id:
            return 1.0
    return 0.0


def calculate_mrr(candidates: List[Dict[str, Any]], target_doc_id: str) -> float:
    """Calculates Reciprocal Rank of first occurrence of target_doc_id."""
    for rank_idx, c in enumerate(candidates, start=1):
        if c.get("document_id") == target_doc_id:
            return round(1.0 / rank_idx, 6)
    return 0.0


def run_benchmark(
    input_filepath: str = "data/msmarco_xi_kn.json",
    num_queries: int = 50,
    output_dir: str = "docs/benchmarks",
) -> Dict[str, Any]:
    """Runs repeatable benchmark evaluation over test corpus and generates JSON/Markdown reports."""
    start_time = time.perf_counter()
    settings = get_settings()

    if not os.path.exists(input_filepath):
        logger.error(f"Input file '{input_filepath}' not found. Run ingest.py first.")
        sys.exit(1)

    logger.info(f"Loading benchmark test dataset from '{input_filepath}'...")
    with open(input_filepath, "r", encoding="utf-8") as f:
        documents = json.load(f)

    eval_docs = documents[:num_queries]
    logger.info(f"Evaluating {len(eval_docs)} test queries...")

    retriever = HybridRetriever()
    llm_service = LLMService()
    evaluator = GroundingEvaluator()

    stage_latencies: Dict[str, List[float]] = {
        "dense_retrieval_ms": [],
        "bm25_ms": [],
        "fusion_ms": [],
        "rerank_ms": [],
        "llm_ms": [],
        "grounding_ms": [],
        "total_backend_ms": [],
    }

    recall_at_5_list: List[float] = []
    recall_at_10_list: List[float] = []
    mrr_list: List[float] = []

    grounded_pass_count = 0
    refusal_count = 0
    blocked_count = 0

    for idx, doc in enumerate(eval_docs, start=1):
        query = doc.get("query", "")
        doc_id = doc.get("document_id", "")
        lang = doc.get("language", settings.DATASET_LANGUAGE)

        t_start = time.perf_counter()

        # Hybrid Retrieval
        ret_res = retriever.retrieve(query=query, language=lang, top_k=10, enable_rerank=False)
        candidates = ret_res["candidates"]
        ret_lb = ret_res["latency_breakdown"]

        stage_latencies["dense_retrieval_ms"].append(ret_lb["dense_search_ms"])
        stage_latencies["bm25_ms"].append(ret_lb["sparse_search_ms"])
        stage_latencies["fusion_ms"].append(ret_lb["rrf_fusion_ms"])
        stage_latencies["rerank_ms"].append(ret_lb["rerank_ms"])

        # Accuracy metrics
        r5 = calculate_recall_at_k(candidates, doc_id, k=5)
        r10 = calculate_recall_at_k(candidates, doc_id, k=10)
        mrr_val = calculate_mrr(candidates, doc_id)

        recall_at_5_list.append(r5)
        recall_at_10_list.append(r10)
        mrr_list.append(mrr_val)

        # Context & Prompt
        prompt_data = build_grounded_prompt(query=query, retrieved_chunks=candidates, language=lang)
        if prompt_data["is_injection_detected"]:
            blocked_count += 1

        # LLM Generation
        t_llm_start = time.perf_counter()
        llm_res = llm_service.generate_grounded_answer(prompt_data, candidates)
        llm_ms = round((time.perf_counter() - t_llm_start) * 1000.0, 2)
        stage_latencies["llm_ms"].append(llm_ms)

        # Grounding Evaluation
        t_eval_start = time.perf_counter()
        eval_res = evaluator.verify_grounding(llm_res["answer"], candidates)
        eval_ms = round((time.perf_counter() - t_eval_start) * 1000.0, 2)
        stage_latencies["grounding_ms"].append(eval_ms)

        if eval_res["status"] == "refusal":
            refusal_count += 1
        elif eval_res["grounded"]:
            grounded_pass_count += 1

        total_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
        stage_latencies["total_backend_ms"].append(total_ms)

    # Compute percentiles
    percentiles_report: Dict[str, Dict[str, float]] = {}
    for stage_name, values in stage_latencies.items():
        percentiles_report[stage_name] = {
            "P50": calculate_percentile(values, 50),
            "P70": calculate_percentile(values, 70),
            "P100": calculate_percentile(values, 100),
        }

    total_eval = len(eval_docs)
    avg_recall_5 = round(sum(recall_at_5_list) / total_eval, 4)
    avg_recall_10 = round(sum(recall_at_10_list) / total_eval, 4)
    avg_mrr = round(sum(mrr_list) / total_eval, 4)
    groundedness_pass_rate = round((grounded_pass_count / total_eval) * 100.0, 2)
    refusal_rate = round((refusal_count / total_eval) * 100.0, 2)
    blocked_rate = round((blocked_count / total_eval) * 100.0, 2)

    total_benchmark_time_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

    results_payload = {
        "timestamp": time.time(),
        "num_queries_evaluated": total_eval,
        "input_dataset": input_filepath,
        "language": settings.DATASET_LANGUAGE,
        "latency_percentiles_ms": percentiles_report,
        "retrieval_accuracy": {
            "Recall@5": avg_recall_5,
            "Recall@10": avg_recall_10,
            "Mean_Reciprocal_Rank_MRR": avg_mrr,
        },
        "grounding_quality": {
            "groundedness_pass_rate_percent": groundedness_pass_rate,
            "refusal_rate_percent": refusal_rate,
            "prompt_injection_blocked_percent": blocked_rate,
        },
        "benchmark_execution_time_ms": total_benchmark_time_ms,
    }

    # Save JSON results
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "benchmark_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2)

    # Generate Markdown report
    md_path = os.path.join(output_dir, "benchmark_report.md")
    generate_markdown_report(results_payload, md_path)

    print("\n" + "=" * 70)
    print("                HHGOA BENCHMARK HARNESS REPORT               ")
    print("=" * 70)
    print(f"Queries Evaluated: {total_eval} | Dataset: {input_filepath}")
    print("-" * 70)
    print(f"{'Stage Name':<22} | {'P50 (ms)':<10} | {'P70 (ms)':<10} | {'P100 (ms)':<10}")
    print("-" * 70)
    for stage_name, p_vals in percentiles_report.items():
        print(f"{stage_name:<22} | {p_vals['P50']:<10} | {p_vals['P70']:<10} | {p_vals['P100']:<10}")
    print("-" * 70)
    print(f"Recall@5: {avg_recall_5} | Recall@10: {avg_recall_10} | MRR: {avg_mrr}")
    print(f"Groundedness Pass Rate: {groundedness_pass_rate}% | Refusal Rate: {refusal_rate}%")
    print(f"JSON Results: {json_path}")
    print(f"Markdown Report: {md_path}")
    print("=" * 70 + "\n")

    return results_payload


def generate_markdown_report(results: Dict[str, Any], filepath: str) -> None:
    """Formats benchmark results into a clean GitHub Flavored Markdown report."""
    p_map = results["latency_percentiles_ms"]
    acc = results["retrieval_accuracy"]
    gq = results["grounding_quality"]

    md_content = f"""# HHGOA 2026 — Voice RAG System Benchmark Report

## Executive Summary
Evaluation results generated on **{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['timestamp']))}** across **{results['num_queries_evaluated']}** queries from `{results['input_dataset']}`.

---

## 1. Latency Breakdown (Percentiles)

| Pipeline Stage | P50 (ms) | P70 (ms) | P100 (ms) |
| :--- | :--- | :--- | :--- |
| **Dense Retrieval (Qdrant)** | `{p_map['dense_retrieval_ms']['P50']}` | `{p_map['dense_retrieval_ms']['P70']}` | `{p_map['dense_retrieval_ms']['P100']}` |
| **Sparse Retrieval (BM25)** | `{p_map['bm25_ms']['P50']}` | `{p_map['bm25_ms']['P70']}` | `{p_map['bm25_ms']['P100']}` |
| **RRF Fusion** | `{p_map['fusion_ms']['P50']}` | `{p_map['fusion_ms']['P70']}` | `{p_map['fusion_ms']['P100']}` |
| **Cross-Encoder Reranking** | `{p_map['rerank_ms']['P50']}` | `{p_map['rerank_ms']['P70']}` | `{p_map['rerank_ms']['P100']}` |
| **LLM Generation (Gemini)** | `{p_map['llm_ms']['P50']}` | `{p_map['llm_ms']['P70']}` | `{p_map['llm_ms']['P100']}` |
| **Grounding Verification** | `{p_map['grounding_ms']['P50']}` | `{p_map['grounding_ms']['P70']}` | `{p_map['grounding_ms']['P100']}` |
| **Total Backend Pipeline** | `{p_map['total_backend_ms']['P50']}` | `{p_map['total_backend_ms']['P70']}` | `{p_map['total_backend_ms']['P100']}` |

---

## 2. Retrieval Accuracy & Grounding Metrics

| Metric | Measured Value | Target Benchmark |
| :--- | :--- | :--- |
| **Recall@5** | `{acc['Recall@5']}` | `≥ 0.80` |
| **Recall@10** | `{acc['Recall@10']}` | `≥ 0.90` |
| **Mean Reciprocal Rank (MRR)** | `{acc['Mean_Reciprocal_Rank_MRR']}` | `≥ 0.75` |
| **Groundedness Pass Rate** | `{gq['groundedness_pass_rate_percent']}%` | `≥ 90.0%` |
| **Refusal Rate** | `{gq['refusal_rate_percent']}%` | Controlled |
| **Prompt Injection Blocked** | `{gq['prompt_injection_blocked_percent']}%` | `100.0%` |
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Repeatable Benchmark Harness CLI")
    parser.add_argument("--input", type=str, default="data/msmarco_xi_kn.json", help="Path to evaluation corpus")
    parser.add_argument("--num-queries", type=int, default=50, help="Number of test queries to evaluate")
    parser.add_argument("--output-dir", type=str, default="docs/benchmarks", help="Output directory for reports")
    args = parser.parse_args()

    run_benchmark(input_filepath=args.input, num_queries=args.num_queries, output_dir=args.output_dir)
