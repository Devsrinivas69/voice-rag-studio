import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.bm25 import BM25Service
from backend.app.services.embeddings import EmbeddingService
from backend.app.services.qdrant import QdrantService
from backend.app.services.retrieval import HybridRetriever, compute_rrf_score

client = TestClient(app)


def test_rrf_score_calculation():
    # Dense rank 1, Sparse rank 2, k=60
    # RRF = 1/(60+1) + 1/(60+2) = 1/61 + 1/62 = 0.0163934 + 0.016129 = 0.032523
    score = compute_rrf_score(dense_rank=1, sparse_rank=2, k=60)
    expected = round(1.0 / 61 + 1.0 / 62, 6)
    assert score == expected

    # Dense rank only
    score_d_only = compute_rrf_score(dense_rank=1, sparse_rank=None, k=60)
    assert score_d_only == round(1.0 / 61, 6)


def test_hybrid_retriever_pipeline(tmp_path):
    # Setup mock store in Qdrant & BM25
    qdrant = QdrantService(collection_name="test_hybrid_col")
    bm25 = BM25Service(index_path=str(tmp_path / "bm25_hybrid.pkl"))
    embeddings = EmbeddingService()

    chunks = [
        {
            "chunk_id": "chunk_kn_01",
            "document_id": "doc_101",
            "text": "ಕಾರ್ಪೊರೇಷನ್ ಎಂದರೆ ಒಂದು ಸಂಸ್ಥೆ",
            "language": "kn",
            "strategy": "fixed",
        },
        {
            "chunk_id": "chunk_kn_02",
            "document_id": "doc_102",
            "text": "ಸರ್ಕಾರದ ನಿಯಮಗಳು ಮತ್ತು ಆಡಳಿತ ಪ್ರಕ್ರಿಯೆ",
            "language": "kn",
            "strategy": "fixed",
        },
    ]

    bm25.build_index(chunks)

    # Upsert to Qdrant in-memory fallback store
    points = [
        {
            "id": c["chunk_id"],
            "vector": embeddings.encode_single(c["text"]),
            "payload": c,
        }
        for c in chunks
    ]
    qdrant.upsert_points("test_hybrid_col", points)

    retriever = HybridRetriever(
        embedding_service=embeddings,
        qdrant_service=qdrant,
        bm25_service=bm25,
        rrf_k=60,
    )

    result = retriever.retrieve(query="ಸಂಸ್ಥೆ", language="kn", top_k=5)

    assert "candidates" in result
    assert "latency_breakdown" in result
    assert len(result["candidates"]) > 0

    first = result["candidates"][0]
    assert "chunk_id" in first
    assert "rrf_score" in first
    assert "final_score" in first

    lb = result["latency_breakdown"]
    assert "dense_search_ms" in lb
    assert "sparse_search_ms" in lb
    assert "rrf_fusion_ms" in lb
    assert "total_retrieval_ms" in lb


def test_post_query_endpoint_hybrid_retrieval():
    payload = {
        "query": "ಕಾರ್ಪೊರೇಷನ್ ಎಂದರೇನು?",
        "language": "kn",
        "top_k": 5,
        "enable_rerank": False,
    }
    response = client.post("/api/query", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert len(data["sources"]) > 0
    assert "latency" in data
    assert data["latency"]["dense_retrieval_ms"] >= 0.0
    assert data["latency"]["bm25_ms"] >= 0.0
    assert data["latency"]["fusion_ms"] >= 0.0
