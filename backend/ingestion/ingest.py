import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List

# Add repository root to pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.config import get_settings
from backend.app.monitoring.metrics import logger
from backend.ingestion.clean import DocumentCleaner
from backend.ingestion.deduplicate import DocumentDeduplicator
from backend.ingestion.load_dataset import MSMarcoLoader


def run_ingestion(
    language: str = "kn",
    sample_size: int = 5000,
    full_ingest: bool = False,
    output_dir: str = "data",
) -> Dict[str, Any]:
    """Runs end-to-end dataset ingestion: stream -> clean -> dedup -> save."""
    start_time = time.perf_counter()

    loader = MSMarcoLoader(
        language=language,
        sample_size=sample_size,
        full_ingest=full_ingest,
    )
    cleaner = DocumentCleaner(target_language=language)
    deduplicator = DocumentDeduplicator()

    processed_records: List[Dict[str, Any]] = []
    total_raw_records = 0
    total_passages_count = 0

    logger.info(f"Starting MSMARCO-XI ingestion pipeline for language '{language}'...")

    for raw_item in loader.stream_records():
        total_raw_records += 1
        cleaned = cleaner.clean_record(raw_item)
        if not cleaned:
            continue

        deduped = deduplicator.process_record(cleaned)
        if not deduped:
            continue

        processed_records.append(deduped)
        total_passages_count += len(deduped["passages"])

    os.makedirs(output_dir, exist_ok=True)
    output_filepath = os.path.join(output_dir, f"msmarco_xi_{language}.json")

    with open(output_filepath, "w", encoding="utf-8") as f:
        json.dump(processed_records, f, ensure_ascii=False, indent=2)

    elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

    stats = {
        "dataset_name": loader.dataset_name,
        "language": language,
        "raw_records_inspected": total_raw_records,
        "documents_ingested": len(processed_records),
        "passages_ingested": total_passages_count,
        "duplicate_documents_removed": deduplicator.duplicate_doc_count,
        "duplicate_passages_removed": deduplicator.duplicate_passage_count,
        "output_file": output_filepath,
        "ingestion_time_ms": elapsed_ms,
    }

    print("\n" + "=" * 50)
    print("        MSMARCO-XI INGESTION STATISTICS        ")
    print("=" * 50)
    print(f"  Language:                    {stats['language']}")
    print(f"  Raw Records Inspected:       {stats['raw_records_inspected']}")
    print(f"  Documents Ingested:          {stats['documents_ingested']}")
    print(f"  Total Passages Ingested:     {stats['passages_ingested']}")
    print(f"  Duplicate Documents Removed: {stats['duplicate_documents_removed']}")
    print(f"  Duplicate Passages Removed:  {stats['duplicate_passages_removed']}")
    print(f"  Output File Saved:           {stats['output_file']}")
    print(f"  Ingestion Time:              {stats['ingestion_time_ms']} ms")
    print("=" * 50 + "\n")

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MSMARCO-XI Ingestion CLI")
    parser.add_argument("--language", type=str, default="kn", help="Language code (e.g. kn, hi, ta, en)")
    parser.add_argument("--sample-size", type=int, default=5000, help="Max records for sample ingestion")
    parser.add_argument("--full-ingest", action="store_true", help="Explicit flag for full ingestion")
    parser.add_argument("--output-dir", type=str, default="data", help="Target output directory")

    args = parser.parse_args()
    run_ingestion(
        language=args.language,
        sample_size=args.sample_size,
        full_ingest=args.full_ingest,
        output_dir=args.output_dir,
    )
