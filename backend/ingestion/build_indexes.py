import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.chunking.metadata import MetadataAwareChunker
from backend.app.config import get_settings
from backend.app.monitoring.metrics import logger
from backend.app.services.bm25 import BM25Service
from backend.app.services.embeddings import EmbeddingService
from backend.app.services.qdrant import QdrantService


def build_indexes(
    input_filepath: str = "data/msmarco_xi_kn.json",
    collection_name: Optional[str] = None,
    batch_size: int = 64,
) -> Dict[str, Any]:
    """Performs complete vector and lexical indexing pipeline over ingested corpus."""
    start_time = time.perf_counter()
    settings = get_settings()

    target_collection = collection_name or settings.QDRANT_COLLECTION

    if not os.path.exists(input_filepath):
        logger.error(f"Input file '{input_filepath}' not found. Run ingest.py first.")
        sys.exit(1)

    logger.info(f"Loading ingested corpus from '{input_filepath}'...")
    with open(input_filepath, "r", encoding="utf-8") as f:
        documents = json.load(f)

    # 1. Chunking engine
    chunker = MetadataAwareChunker()
    all_chunks: List[Dict[str, Any]] = []
    for doc in documents:
        all_chunks.extend(chunker.chunk(doc))

    logger.info(f"Generated {len(all_chunks)} chunks from {len(documents)} documents.")

    # 2. Local Embedding Service
    emb_service = EmbeddingService(model_name=settings.EMBEDDING_MODEL)
    dimension = emb_service.dimension
    logger.info(f"Embedding Model: '{emb_service.model_name}' | Vector Dimension: {dimension}")

    # 3. Qdrant Service
    qdrant_service = QdrantService(collection_name=target_collection)
    qdrant_service.create_collection(collection_name=target_collection, vector_size=dimension)

    # 4. Batch Embeddings & Qdrant Points Preparation
    qdrant_points: List[Dict[str, Any]] = []
    chunk_texts = [c["text"] for c in all_chunks]

    logger.info(f"Generating embeddings in batches of {batch_size}...")
    for i in range(0, len(chunk_texts), batch_size):
        batch_texts = chunk_texts[i : i + batch_size]
        batch_vectors = emb_service.encode_texts(batch_texts)

        for j, vec in enumerate(batch_vectors):
            chunk_data = all_chunks[i + j]
            # Validate dimension before upsert
            if len(vec) != dimension:
                raise ValueError(
                    f"Vector dimension mismatch! Expected {dimension}, got {len(vec)} for chunk '{chunk_data['chunk_id']}'"
                )

            qdrant_points.append(
                {
                    "id": chunk_data["chunk_id"],
                    "vector": vec,
                    "payload": chunk_data,
                }
            )

    # Upsert points to Qdrant
    logger.info(f"Upserting {len(qdrant_points)} vector points to Qdrant collection '{target_collection}'...")
    qdrant_service.upsert_points(collection_name=target_collection, points=qdrant_points)

    # 5. BM25 Lexical Index
    bm25_service = BM25Service(index_path="indices/bm25_index.pkl")
    bm25_service.build_index(all_chunks)

    # 6. Save Ingestion Metadata
    os.makedirs("indices", exist_ok=True)
    metadata_path = "indices/ingestion_metadata.json"
    ingestion_metadata = {
        "timestamp": time.time(),
        "input_file": input_filepath,
        "total_documents": len(documents),
        "total_chunks": len(all_chunks),
        "embedding_model": settings.EMBEDDING_MODEL,
        "embedding_dimension": dimension,
        "qdrant_collection": target_collection,
        "bm25_index_path": bm25_service.index_path,
    }
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(ingestion_metadata, f, indent=2)

    elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

    print("\n" + "=" * 60)
    print("           HHGOA INDEX BUILDING COMPLETE REPORT           ")
    print("=" * 60)
    print(f"  Input Dataset:          {input_filepath}")
    print(f"  Total Documents:        {len(documents)}")
    print(f"  Total Chunks:           {len(all_chunks)}")
    print(f"  Embedding Model:        {settings.EMBEDDING_MODEL}")
    print(f"  Embedding Dimension:    {dimension}")
    print(f"  Qdrant Collection:      {target_collection}")
    print(f"  Qdrant Points Pushed:   {len(qdrant_points)}")
    print(f"  BM25 Index Saved:       {bm25_service.index_path}")
    print(f"  Ingestion Metadata:     {metadata_path}")
    print(f"  Total Indexing Time:    {elapsed_ms} ms")
    print("=" * 60 + "\n")

    return ingestion_metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Complete Vector & Lexical Index Builder CLI")
    parser.add_argument("--input", type=str, default="data/msmarco_xi_kn.json", help="Path to ingested corpus JSON")
    parser.add_argument("--collection", type=str, default=None, help="Target Qdrant collection name")
    parser.add_argument("--batch-size", type=int, default=64, help="Embedding batch size")
    args = parser.parse_args()

    build_indexes(
        input_filepath=args.input,
        collection_name=args.collection,
        batch_size=args.batch_size,
    )
