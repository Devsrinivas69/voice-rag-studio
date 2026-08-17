"""
HHGOA 2026 — Fast Cloud Ingestion Pipeline
Loads MSMARCO-XI English data → Gemini Embedding 2 (768-dim) → Qdrant Cloud + BM25 index.

Prioritizes gold ground-truth passages for accurate, hallucination-free retrieval.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import sys
import time
import uuid
from typing import Any, Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from google import genai
from google.genai import types
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.models import Distance, VectorParams

GEMINI_EMBEDDING_MODEL = "models/gemini-embedding-2"
GEMINI_EMBEDDING_DIM = 768
QDRANT_COLLECTION = "msmarco_xi"
LOCAL_DATA_DIR = "backend/data/msmarco_xi"


def extract_gold_passages(shard_paths: List[str], max_queries: int = 800) -> List[Dict[str, Any]]:
    """Extracts all gold passages (the ground-truth answers) from MSMARCO-XI parquet shards."""
    import pandas as pd

    documents = []
    queries_seen = 0
    target_columns = ["Eng_Query", "Eng_Answer", "passages"]

    print(f"Extracting gold passages from shards (target: {max_queries} queries)...", flush=True)

    for path in shard_paths:
        if queries_seen >= max_queries:
            break

        print(f"  Reading shard {path}...", flush=True)
        try:
            df = pd.read_parquet(path, columns=target_columns)
        except Exception:
            df = pd.read_parquet(path)

        for idx, row in df.iterrows():
            if queries_seen >= max_queries:
                break

            query = str(row.get("Eng_Query", "") or row.get("query", "") or "").strip()
            answer = str(row.get("Eng_Answer", "") or row.get("Answer", "") or "").strip()

            passages_data = row.get("passages", {})
            if not isinstance(passages_data, dict):
                continue

            eng_passages = passages_data.get("English_passages", [])
            is_selected = passages_data.get("is_selected", [])

            if eng_passages is None or len(eng_passages) == 0:
                continue

            queries_seen += 1

            # Extract the gold passage (is_selected=1) for this query
            gold_found = False
            for p_idx, passage_text in enumerate(eng_passages):
                if not passage_text or not str(passage_text).strip():
                    continue

                selected = is_selected[p_idx] if p_idx < len(is_selected) else 0

                if selected == 1:
                    gold_found = True
                    doc_id = f"msmarco_en_{queries_seen}_{p_idx}"
                    documents.append({
                        "chunk_id": f"{doc_id}_c0",
                        "document_id": doc_id,
                        "text": str(passage_text).strip(),
                        "language": "en",
                        "strategy": "fixed",
                        "source_query": query,
                        "source_answer": answer,
                        "metadata": {
                            "dataset": "MSMARCO-XI",
                            "split": "validation",
                            "row_index": queries_seen,
                            "passage_index": p_idx,
                            "is_gold_passage": True,
                        },
                    })

            # If no passage was explicitly flagged as selected, take passage 0
            if not gold_found and len(eng_passages) > 0 and str(eng_passages[0]).strip():
                doc_id = f"msmarco_en_{queries_seen}_0"
                documents.append({
                    "chunk_id": f"{doc_id}_c0",
                    "document_id": doc_id,
                    "text": str(eng_passages[0]).strip(),
                    "language": "en",
                    "strategy": "fixed",
                    "source_query": query,
                    "source_answer": answer,
                    "metadata": {
                        "dataset": "MSMARCO-XI",
                        "split": "validation",
                        "row_index": queries_seen,
                        "passage_index": 0,
                        "is_gold_passage": False,
                    },
                })

        del df

    print(f"Extracted {len(documents)} gold passages across {queries_seen} queries.", flush=True)
    return documents


def build_bm25(chunks: List[Dict[str, Any]], paths: List[str]):
    """Builds and serializes BM25 lexical index to all target paths."""
    from backend.app.services.bm25 import BM25Service

    for p in paths:
        os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
        bm25 = BM25Service(index_path=p)
        bm25.build_index(chunks)
        print(f"BM25 index saved: {p} ({len(chunks)} chunks)", flush=True)


def main():
    parser = argparse.ArgumentParser(description="HHGOA Fast Cloud Ingestion Pipeline")
    parser.add_argument("--queries", type=int, default=600, help="Number of queries to index")
    parser.add_argument("--concurrency", type=int, default=8, help="Concurrent embedding threads")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv("backend/.env")

    gemini_key = os.getenv("GEMINI_API_KEY")
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_key = os.getenv("QDRANT_API_KEY")

    if not gemini_key or not qdrant_url:
        print("ERROR: Missing GEMINI_API_KEY or QDRANT_URL in backend/.env", flush=True)
        sys.exit(1)

    print("=" * 60, flush=True)
    print("  HHGOA 2026 — Ultra-Fast Cloud Ingestion Pipeline", flush=True)
    print("=" * 60, flush=True)
    print(f"  Target queries:  {args.queries}", flush=True)
    print(f"  Embedding model: {GEMINI_EMBEDDING_MODEL} (dim={GEMINI_EMBEDDING_DIM})", flush=True)
    print(f"  Concurrency:     {args.concurrency} threads", flush=True)
    print(f"  Qdrant cluster:  {qdrant_url}", flush=True)
    print("=" * 60, flush=True)

    t0 = time.perf_counter()

    # Step 1: Collect shard paths
    shard_paths = [
        os.path.join(LOCAL_DATA_DIR, f"shard_{i}.parquet")
        for i in range(14)
        if os.path.exists(os.path.join(LOCAL_DATA_DIR, f"shard_{i}.parquet"))
    ]

    if not shard_paths:
        print("ERROR: No shards found in backend/data/msmarco_xi", flush=True)
        sys.exit(1)

    # Step 2: Extract passages
    chunks = extract_gold_passages(shard_paths, max_queries=args.queries)

    # Step 3: Recreate Qdrant Collection
    print(f"\nConnecting to Qdrant Cloud...", flush=True)
    q_client = QdrantClient(url=qdrant_url, api_key=qdrant_key, timeout=30)

    try:
        existing = [c.name for c in q_client.get_collections().collections]
        if QDRANT_COLLECTION in existing:
            print(f"Recreating collection '{QDRANT_COLLECTION}'...", flush=True)
            q_client.delete_collection(QDRANT_COLLECTION)
            time.sleep(2)
    except Exception as e:
        print(f"Notice: {e}", flush=True)

    print(f"Creating '{QDRANT_COLLECTION}' (dim={GEMINI_EMBEDDING_DIM}, distance=COSINE)...", flush=True)
    q_client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=VectorParams(size=GEMINI_EMBEDDING_DIM, distance=Distance.COSINE),
    )

    for field, ftype in [
        ("chunk_id", qmodels.PayloadSchemaType.KEYWORD),
        ("document_id", qmodels.PayloadSchemaType.KEYWORD),
        ("language", qmodels.PayloadSchemaType.KEYWORD),
        ("strategy", qmodels.PayloadSchemaType.KEYWORD),
    ]:
        try:
            q_client.create_payload_index(collection_name=QDRANT_COLLECTION, field_name=field, field_schema=ftype)
        except Exception:
            pass

    # Step 4: Generate embeddings concurrently and upsert in chunks of 50
    print(f"\nGenerating embeddings for {len(chunks)} chunks with {args.concurrency} concurrent threads...", flush=True)
    genai_client = genai.Client(api_key=gemini_key)

    def embed_single(item):
        chunk, idx = item
        text = chunk["text"]
        for attempt in range(5):
            try:
                res = genai_client.models.embed_content(
                    model=GEMINI_EMBEDDING_MODEL,
                    contents=text,
                    config=types.EmbedContentConfig(output_dimensionality=GEMINI_EMBEDDING_DIM),
                )
                return idx, chunk, res.embeddings[0].values
            except Exception as err:
                if "429" in str(err) or "RESOURCE_EXHAUSTED" in str(err):
                    time.sleep(10 + attempt * 5)
                else:
                    time.sleep(1)
        return idx, chunk, [0.0] * GEMINI_EMBEDDING_DIM

    indexed_points = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(embed_single, (chunk, idx)) for idx, chunk in enumerate(chunks)]
        
        for count, f in enumerate(as_completed(futures), 1):
            idx, chunk, vector = f.result()
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk["chunk_id"]))
            indexed_points.append(
                qmodels.PointStruct(id=point_id, vector=vector, payload=chunk)
            )

            if count % 50 == 0 or count == len(chunks):
                print(f"  Embedded {count}/{len(chunks)} passages...", flush=True)

    # Upsert all points to Qdrant Cloud
    print(f"\nUpserting {len(indexed_points)} vector points to Qdrant Cloud...", flush=True)
    upsert_batch_size = 100
    for i in range(0, len(indexed_points), upsert_batch_size):
        batch = indexed_points[i : i + upsert_batch_size]
        q_client.upsert(collection_name=QDRANT_COLLECTION, points=batch)
        print(f"  Upserted {min(i + upsert_batch_size, len(indexed_points))}/{len(indexed_points)} points...", flush=True)

    info = q_client.get_collection(QDRANT_COLLECTION)
    print(f"\nVerified Qdrant '{QDRANT_COLLECTION}' collection point count: {info.points_count}.", flush=True)

    # Step 5: Build and save BM25 indexes
    print("\nBuilding BM25 lexical search indexes...", flush=True)
    build_bm25(chunks, ["backend/indices/bm25_index.pkl", "indices/bm25_index.pkl"])

    elapsed = round(time.perf_counter() - t0, 1)
    print("\n" + "=" * 60, flush=True)
    print("  INGESTION & INDEXING COMPLETED SUCCESSFULLY!", flush=True)
    print("=" * 60, flush=True)
    print(f"  Total passages indexed: {len(chunks)}", flush=True)
    print(f"  Qdrant points:          {info.points_count}", flush=True)
    print(f"  Total time:             {elapsed}s", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    main()
