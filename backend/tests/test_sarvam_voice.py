import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.sarvam import SarvamSTTService

client = TestClient(app)


def test_sarvam_stt_service_language_normalization():
    stt = SarvamSTTService()
    assert stt.normalize_language_code("kn") == "kn-IN"
    assert stt.normalize_language_code("hi-IN") == "hi-IN"
    assert stt.normalize_language_code("ta") == "ta-IN"
    assert stt.normalize_language_code("en") == "en-IN"


@pytest.mark.asyncio
async def test_sarvam_stt_mock_fallback():
    stt = SarvamSTTService()
    dummy_bytes = b"RIFF....WAVEfmt ....data...."
    res = await stt.transcribe_audio(dummy_bytes, filename="test.wav", language="kn-IN")

    assert "transcript" in res
    assert len(res["transcript"]) > 0
    assert res["language"] == "kn-IN"
    assert res["stt_ms"] >= 0.0


def test_voice_query_endpoint_empty_file():
    empty_file = io.BytesIO(b"")
    files = {"audio": ("empty.wav", empty_file, "audio/wav")}
    response = client.post("/api/voice/query", files=files)

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "EMPTY_AUDIO"


def test_voice_query_endpoint_success_pipeline():
    audio_content = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    audio_file = io.BytesIO(audio_content)
    files = {"audio": ("sample.wav", audio_file, "audio/wav")}
    data = {"language": "kn-IN", "top_k": 5}

    response = client.post("/api/voice/query", files=files, data=data)

    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    assert res["transcript"] is not None
    assert len(res["transcript"]) > 0
    assert res["answer"] is not None
    assert len(res["sources"]) > 0
    assert "latency" in res
    assert res["latency"]["stt_ms"] >= 0.0
    assert res["latency"]["dense_retrieval_ms"] >= 0.0
    assert res["latency"]["total_backend_ms"] >= 0.0
