import pytest
from backend.ingestion.clean import DocumentCleaner, normalize_text
from backend.ingestion.deduplicate import DocumentDeduplicator


def test_normalize_text():
    raw_text = "  Hello \t world \n\r test   \x00 text!  "
    cleaned = normalize_text(raw_text)
    assert cleaned == "Hello world test text!"


def test_document_cleaner():
    cleaner = DocumentCleaner(target_language="kn")
    raw_item = {
        "query_id": 101,
        "target_lang": "kn",
        "query": "  ಕಾರ್ಪೊರೇಷನ್ ಎಂದರೇನು?  ",
        "Eng_Query": "What is a corporation?",
        "Answer": "  ಕಾರ್ಪೊರೇಷನ್ ಎಂದರೆ ಸಂಸ್ಥೆ... ",
        "Eng_Answer": "A corporation is an entity...",
        "passages": {
            "Translated_passages": [" ಪ್ಯಾರಾಗ್ರಾಫ್ 1 ... ", " ಪ್ಯಾರಾಗ್ರಾಫ್ 2 ... "],
            "English_passages": ["Passage 1...", "Passage 2..."],
            "is_selected": [1, 0],
        },
    }

    cleaned = cleaner.clean_record(raw_item)
    assert cleaned is not None
    assert cleaned["document_id"] == "msmarco_xi_101"
    assert cleaned["query_id"] == 101
    assert cleaned["language"] == "kn"
    assert cleaned["query"] == "ಕಾರ್ಪೊರೇಷನ್ ಎಂದರೇನು?"
    assert len(cleaned["passages"]) == 2
    assert cleaned["passages"][0]["is_selected"] is True
    assert cleaned["passages"][1]["is_selected"] is False


def test_cleaner_rejects_missing_query():
    cleaner = DocumentCleaner(target_language="kn")
    raw_item = {
        "query_id": 102,
        "target_lang": "kn",
        "query": "",
        "Eng_Query": "",
        "passages": {"Translated_passages": ["Sample passage"]},
    }
    cleaned = cleaner.clean_record(raw_item)
    assert cleaned is None


def test_document_deduplicator():
    dedup = DocumentDeduplicator()

    item1 = {
        "document_id": "msmarco_xi_201",
        "query": "What is AI?",
        "passages": [
            {"passage_index": 0, "text": "AI stands for Artificial Intelligence."},
            {"passage_index": 1, "text": "Machine learning is a subset of AI."},
        ],
    }

    # Duplicate query item
    item2 = {
        "document_id": "msmarco_xi_202",
        "query": "what is ai?",  # Same normalized query text
        "passages": [{"passage_index": 0, "text": "Different passage."}],
    }

    res1 = dedup.process_record(item1)
    res2 = dedup.process_record(item2)

    assert res1 is not None
    assert len(res1["passages"]) == 2
    assert res2 is None
    assert dedup.duplicate_doc_count == 1


def test_passage_level_deduplication():
    dedup = DocumentDeduplicator()

    item1 = {
        "document_id": "msmarco_xi_301",
        "query": "First query",
        "passages": [{"passage_index": 0, "text": "Shared passage text between queries."}],
    }

    item2 = {
        "document_id": "msmarco_xi_302",
        "query": "Second distinct query",
        "passages": [{"passage_index": 0, "text": "Shared passage text between queries."}],
    }

    res1 = dedup.process_record(item1)
    res2 = dedup.process_record(item2)

    assert res1 is not None
    assert res2 is None  # Rejects item2 because all its passages were duplicates
    assert dedup.duplicate_passage_count == 1
