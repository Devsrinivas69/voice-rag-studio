import argparse
import hashlib
import json
import os
import sys
import time
from typing import Any, Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.chunking.fixed import FixedTokenChunker
from backend.app.chunking.metadata import MetadataAwareChunker
from backend.app.chunking.semantic import SemanticChunker
from backend.app.chunking.sentence import SentenceChunker


def run_chunking_benchmark(input_filepath: str) -> Dict[str, Any]:
    """Evaluates all 4 chunking strategies on the dataset and prints a benchmark report."""
    if not os.path.exists(input_filepath):
        print(f"Error: Input dataset file '{input_filepath}' not found. Run ingest.py first.")
        sys.exit(1)

    with open(input_filepath, "r", encoding="utf-8") as f:
        documents = json.load(f)

    chunkers = [
        FixedTokenChunker(),
        SentenceChunker(),
        SemanticChunker(),
        MetadataAwareChunker(),
    ]

    benchmark_results: Dict[str, Any] = {}

    print("\n" + "=" * 70)
    print("                HHGOA CHUNKING ENGINE BENCHMARK REPORT               ")
    print("=" * 70)
    print(f"Input Dataset: {input_filepath} | Total Documents: {len(documents)}")
    print("-" * 70)
    print(f"{'Strategy':<18} | {'Chunks':<7} | {'Avg Words':<10} | {'Min/Max':<10} | {'Time (ms)':<10} | {'Dup Rate':<8}")
    print("-" * 70)

    for chunker in chunkers:
        start_time = time.perf_counter()
        all_chunks: List[Dict[str, Any]] = []

        for doc in documents:
            doc_chunks = chunker.chunk(doc)
            all_chunks.extend(doc_chunks)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        if not all_chunks:
            continue

        word_counts = [c["metadata"]["length_words"] for c in all_chunks]
        avg_words = round(sum(word_counts) / len(word_counts), 1)
        min_words = min(word_counts)
        max_words = max(word_counts)

        # Duplicate chunk calculation (by text hash)
        unique_hashes = set(hashlib.sha256(c["text"].strip().lower().encode("utf-8")).hexdigest() for c in all_chunks)
        dup_count = len(all_chunks) - len(unique_hashes)
        dup_rate = round((dup_count / len(all_chunks)) * 100.0, 2)

        strategy_name = chunker.strategy_name
        benchmark_results[strategy_name] = {
            "total_chunks": len(all_chunks),
            "avg_chunk_size_words": avg_words,
            "min_chunk_size_words": min_words,
            "max_chunk_size_words": max_words,
            "processing_time_ms": elapsed_ms,
            "duplicate_rate_percent": dup_rate,
        }

        min_max_str = f"{min_words}/{max_words}"
        print(
            f"{strategy_name:<18} | {len(all_chunks):<7} | {avg_words:<10} | {min_max_str:<10} | {elapsed_ms:<10} | {dup_rate}%"
        )

    print("=" * 70 + "\n")
    return benchmark_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chunking Engine Benchmark CLI")
    parser.add_argument(
        "--input", type=str, default="data/msmarco_xi_kn.json", help="Path to ingested corpus JSON"
    )
    args = parser.parse_args()

    run_chunking_benchmark(args.input)
