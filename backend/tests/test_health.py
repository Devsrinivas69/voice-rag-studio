import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "environment" in data
    assert "mock_mode" in data


def test_ready_endpoint():
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "components" in data


def test_request_id_header_propagation():
    custom_req_id = "test-correlation-id-999"
    response = client.get("/health", headers={"X-Request-ID": custom_req_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_req_id


def test_text_query_contract():
    payload = {"query": "What is the capital of India?", "language": "en-IN"}
    response = client.post("/api/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "request_id" in data
    assert "answer" in data
    assert "latency" in data
    assert len(data["sources"]) > 0


def test_voice_query_empty_audio_rejection():
    empty_file = ("question.webm", io.BytesIO(b""), "audio/webm")
    response = client.post("/api/voice/query", files={"audio": empty_file}, data={"language": "kn-IN"})
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "EMPTY_AUDIO"


def test_config_status_sanitized():
    response = client.get("/api/config/status")
    assert response.status_code == 200
    data = response.json()
    assert "EMBEDDING_MODEL" in data
    # Ensure sensitive fields are not raw string secrets
    assert data.get("SARVAM_API_KEY") is None or "..." in data.get("SARVAM_API_KEY", "")
