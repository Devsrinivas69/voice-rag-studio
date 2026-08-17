import os
import pytest
from backend.benchmark.run_benchmark import (
    calculate_mrr,
    calculate_percentile,
    calculate_recall_at_k,
    generate_markdown_report,
)


def test_calculate_percentile():
    data = [10.0, 20.0, 30.0, 40.0, 50.0]
    p50 = calculate_percentile(data, 50)
    p100 = calculate_percentile(data, 100)
    assert p50 == 30.0
    assert p100 == 50.0


def test_calculate_recall_at_k():
    candidates = [
        {"document_id": "doc_101"},
        {"document_id": "doc_102"},
        {"document_id": "doc_103"},
    ]
    assert calculate_recall_at_k(candidates, "doc_101", k=1) == 1.0
    assert calculate_recall_at_k(candidates, "doc_102", k=2) == 1.0
    assert calculate_recall_at_k(candidates, "doc_103", k=2) == 0.0
    assert calculate_recall_at_k(candidates, "doc_103", k=3) == 1.0


def test_calculate_mrr():
    candidates = [
        {"document_id": "doc_101"},
        {"document_id": "doc_102"},
        {"document_id": "doc_103"},
    ]
    assert calculate_mrr(candidates, "doc_101") == 1.0  # 1/1
    assert calculate_mrr(candidates, "doc_102") == 0.5  # 1/2
    assert calculate_mrr(candidates, "doc_103") == round(1.0 / 3.0, 6)
    assert calculate_mrr(candidates, "doc_999") == 0.0


def test_generate_markdown_report(tmp_path):
    dummy_results = {
        "timestamp": 1700000000,
        "num_queries_evaluated": 10,
        "input_dataset": "data/sample.json",
        "latency_percentiles_ms": {
            "dense_retrieval_ms": {"P50": 5.0, "P70": 7.0, "P100": 10.0},
            "bm25_ms": {"P50": 2.0, "P70": 3.0, "P100": 5.0},
            "fusion_ms": {"P50": 1.0, "P70": 1.5, "P100": 2.0},
            "rerank_ms": {"P50": 0.0, "P70": 0.0, "P100": 0.0},
            "llm_ms": {"P50": 100.0, "P70": 150.0, "P100": 200.0},
            "grounding_ms": {"P50": 1.0, "P70": 2.0, "P100": 3.0},
            "total_backend_ms": {"P50": 110.0, "P70": 160.0, "P100": 220.0},
        },
        "retrieval_accuracy": {
            "Recall@5": 0.90,
            "Recall@10": 0.95,
            "Mean_Reciprocal_Rank_MRR": 0.85,
        },
        "grounding_quality": {
            "groundedness_pass_rate_percent": 95.0,
            "refusal_rate_percent": 0.0,
            "prompt_injection_blocked_percent": 0.0,
        },
    }

    report_path = str(tmp_path / "test_report.md")
    generate_markdown_report(dummy_results, report_path)

    assert os.path.exists(report_path)
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "HHGOA 2026" in content
    assert "Dense Retrieval" in content
    assert "Recall@5" in content
