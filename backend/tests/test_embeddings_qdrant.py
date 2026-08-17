import numpy as np
import pytest
from backend.app.services.bm25 import BM25Service, tokenize_bm25
from backend.app.services.embeddings import EmbeddingService
from backend.app.services.qdrant import QdrantService


def test_embedding_service_dimension_and_normalization():
    emb_service = EmbeddingService()
    dim = emb_service.dimension
    assert dim > 0

    texts = ["HHGOA Voice RAG System", "Multilingual Indic retrieval test"]
    vectors = emb_service.encode_texts(texts)

    assert len(vectors) == 2
    assert len(vectors[0]) == dim
    assert len(vectors[1]) == dim

    # Check L2 normalization: norm of vector should be approximately 1.0
    norm0 = np.linalg.norm(vectors[0])
    norm1 = np.linalg.norm(vectors[1])
    assert abs(norm0 - 1.0) < 1e-3
    assert abs(norm1 - 1.0) < 1e-3


def test_qdrant_service_upsert_and_search():
    qdrant = QdrantService(collection_name="test_collection")
    assert qdrant.health_check() is True

    dim = 1024
    qdrant.create_collection("test_collection", vector_size=dim)

    # Generate dummy normalized vectors
    rng = np.random.RandomState(42)
    v1 = rng.randn(dim).astype(np.float32)
    v1 /= np.linalg.norm(v1)
    v2 = rng.randn(dim).astype(np.float32)
    v2 /= np.linalg.norm(v2)

    points = [
        {
            "id": "chunk_kn_001",
            "vector": v1.tolist(),
            "payload": {
                "chunk_id": "chunk_kn_001",
                "document_id": "doc_101",
                "text": "ಕಾರ್ಪೊರೇಷನ್ ವಿವರಣೆ",
                "language": "kn",
                "strategy": "fixed",
            },
        },
        {
            "id": "chunk_hi_002",
            "vector": v2.tolist(),
            "payload": {
                "chunk_id": "chunk_hi_002",
                "document_id": "doc_102",
                "text": "निगम की परिभाषा",
                "language": "hi",
                "strategy": "fixed",
            },
        },
    ]

    upsert_ok = qdrant.upsert_points("test_collection", points)
    assert upsert_ok is True

    # Search with v1 query vector
    results = qdrant.search("test_collection", query_vector=v1.tolist(), limit=5)
    assert len(results) > 0
    assert results[0]["payload"]["chunk_id"] == "chunk_kn_001"

    # Search with language filter
    kn_results = qdrant.search("test_collection", query_vector=v1.tolist(), limit=5, language_filter="kn")
    assert len(kn_results) == 1
    assert kn_results[0]["payload"]["language"] == "kn"


def test_bm25_service_build_save_load_search(tmp_path):
    index_file = str(tmp_path / "bm25_test_index.pkl")
    bm25_service = BM25Service(index_path=index_file)

    sample_chunks = [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "text": "ಕಾರ್ಪೊರೇಷನ್ ಎಂದರೆ ಒಂದು ಸಂಸ್ಥೆ",
            "language": "kn",
        },
        {
            "chunk_id": "c2",
            "document_id": "d2",
            "text": "ಭಾರತ ಸರ್ಕಾರ ಮತ್ತು ಆಡಳಿತ ನಿಯಮಗಳು",
            "language": "kn",
        },
    ]

    built_ok = bm25_service.build_index(sample_chunks)
    assert built_ok is True

    # Test BM25 search
    res = bm25_service.search("ಸಂಸ್ಥೆ", limit=5)
    assert len(res) > 0
    assert res[0]["chunk_id"] == "c1"

    # Test loading persisted index from disk
    new_bm25_service = BM25Service(index_path=index_file)
    load_ok = new_bm25_service.load_index()
    assert load_ok is True
    assert len(new_bm25_service.chunks) == 2

    res_loaded = new_bm25_service.search("ಸಂಸ್ಥೆ", limit=5)
    assert len(res_loaded) > 0
    assert res_loaded[0]["chunk_id"] == "c1"


def test_bm25_tokenization():
    tokens = tokenize_bm25("ಕಾರ್ಪೊರೇಷನ್! Hello, World? 123")
    assert "hello" in tokens
    assert "world" in tokens
    assert "123" in tokens
