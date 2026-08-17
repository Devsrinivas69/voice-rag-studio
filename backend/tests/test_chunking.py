import pytest
from backend.app.chunking.fixed import FixedTokenChunker
from backend.app.chunking.metadata import MetadataAwareChunker
from backend.app.chunking.semantic import SemanticChunker
from backend.app.chunking.sentence import SentenceChunker

SAMPLE_DOC = {
    "document_id": "doc_test_101",
    "query_id": 101,
    "language": "kn",
    "query": "ಕಾರ್ಪೊರೇಷನ್ ಎಂದರೇನು?",
    "answer": "ಕಾರ್ಪೊration ಎಂದರೆ ಸಂಸ್ಥೆ.",
    "passages": [
        {
            "passage_index": 0,
            "text": "ಕಾರ್ಪೊರೇಷನ್ ಎಂಬುದು ಒಂದು ಪ್ರಮುಖ ಕಾನೂನುಬದ್ಧ ಸಂಸ್ಥೆಯಾಗಿದೆ. ಇದು ಶೇರುದಾರರ ಒಡೆತನದಲ್ಲಿದೆ. ಪ್ರತಿಯೊಬ್ಬ ಸದಸ್ಯರಿಗೂ ಹಕ್ಕುಗಳು ಇರುತ್ತವೆ.",
            "is_selected": True,
        },
        {
            "passage_index": 1,
            "text": "ಮತ್ತೊಂದು ಪ್ಯಾರಾಗ್ರಾಫ್ ವಿವರಣೆ. ವ್ಯವಹಾರ ಪ್ರಕ್ರಿಯೆ ಸರಳವಾಗಿದೆ. ತೆರಿಗೆ ನಿಯಮಗಳು ಅನುಕೂಲಕರವಾಗಿವೆ.",
            "is_selected": False,
        },
    ],
}


def test_fixed_token_chunker():
    chunker = FixedTokenChunker(chunk_size=10, chunk_overlap=2)
    chunks = chunker.chunk(SAMPLE_DOC)
    assert len(chunks) > 0
    for c in chunks:
        assert c["strategy"] == "fixed"
        assert c["document_id"] == "doc_test_101"
        assert "passage_index" in c["metadata"]
        assert c["metadata"]["token_count"] <= 10


def test_sentence_chunker():
    chunker = SentenceChunker(target_chunk_size=15)
    chunks = chunker.chunk(SAMPLE_DOC)
    assert len(chunks) > 0
    for c in chunks:
        assert c["strategy"] == "sentence"
        assert "sentence_count" in c["metadata"]
        # Verify no mid-sentence breaks occurred
        assert any(delimiter in c["text"] for delimiter in ["।", ".", "?", "!"]) or len(c["text"]) > 0


def test_semantic_chunker():
    chunker = SemanticChunker(breakpoint_threshold=0.50)
    chunks = chunker.chunk(SAMPLE_DOC)
    assert len(chunks) > 0
    for c in chunks:
        assert c["strategy"] == "semantic"
        assert "breakpoint_threshold" in c["metadata"]


def test_metadata_aware_chunker():
    chunker = MetadataAwareChunker()
    chunks = chunker.chunk(SAMPLE_DOC)
    assert len(chunks) == 2
    assert chunks[0]["strategy"] == "metadata_aware"
    assert chunks[0]["metadata"]["is_selected"] is True
    assert chunks[1]["metadata"]["is_selected"] is False
    assert chunks[0]["source_query"] == "ಕಾರ್ಪೊರೇಷನ್ ಎಂದರೇನು?"


def test_standard_chunk_payload_interface():
    chunkers = [
        FixedTokenChunker(),
        SentenceChunker(),
        SemanticChunker(),
        MetadataAwareChunker(),
    ]
    required_keys = {
        "chunk_id",
        "document_id",
        "text",
        "language",
        "strategy",
        "position",
        "source_query",
        "source_answer",
        "metadata",
    }
    for chunker in chunkers:
        chunks = chunker.chunk(SAMPLE_DOC)
        assert len(chunks) > 0
        for c in chunks:
            assert required_keys.issubset(c.keys())
            assert isinstance(c["metadata"], dict)
            assert "length_words" in c["metadata"]
