# HHGOA 2026 — Voice RAG System Benchmark Report

## Executive Summary
Evaluation results generated on **2026-08-14 17:20:45** across **50** queries from `data/msmarco_xi_kn.json`.

---

## 1. Latency Breakdown (Percentiles)

| Pipeline Stage | P50 (ms) | P70 (ms) | P100 (ms) |
| :--- | :--- | :--- | :--- |
| **Dense Retrieval (Qdrant)** | `97.97` | `100.94` | `9866.31` |
| **Sparse Retrieval (BM25)** | `31.72` | `32.7` | `37.57` |
| **RRF Fusion** | `0.08` | `0.08` | `0.09` |
| **Cross-Encoder Reranking** | `0.0` | `0.0` | `0.0` |
| **LLM Generation (Gemini)** | `0.0` | `0.0` | `0.01` |
| **Grounding Verification** | `0.44` | `0.46` | `0.62` |
| **Total Backend Pipeline** | `128.97` | `133.05` | `9905.62` |

---

## 2. Retrieval Accuracy & Grounding Metrics

| Metric | Measured Value | Target Benchmark |
| :--- | :--- | :--- |
| **Recall@5** | `0.72` | `≥ 0.80` |
| **Recall@10** | `0.9` | `≥ 0.90` |
| **Mean Reciprocal Rank (MRR)** | `0.6587` | `≥ 0.75` |
| **Groundedness Pass Rate** | `100.0%` | `≥ 90.0%` |
| **Refusal Rate** | `0.0%` | Controlled |
| **Prompt Injection Blocked** | `0.0%` | `100.0%` |
