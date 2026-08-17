import pytest
from backend.app.config import Settings


def test_default_settings_in_mock_mode():
    settings = Settings(MOCK_EXTERNAL_APIS=True)
    assert settings.MOCK_EXTERNAL_APIS is True
    assert settings.LLM_MODEL in ("gemini-3.7-flash", "gemini-2.5-flash")
    assert settings.EMBEDDING_MODEL in ("models/gemini-embedding-2", "BAAI/bge-m3")
    assert settings.DATASET_NAME == "ai4bharat/MSMARCO-XI"


def test_secret_masking():
    settings = Settings(
        MOCK_EXTERNAL_APIS=True,
        SARVAM_API_KEY="sarvam_secret_key_12345",
        GEMINI_API_KEY="gemini_secret_key_67890",
    )
    masked = settings.get_masked_config()
    assert masked["SARVAM_API_KEY"] == "sarv...2345"
    assert masked["GEMINI_API_KEY"] == "gemi...7890"
    assert "sarvam_secret_key_12345" not in str(masked)


def test_missing_keys_validation_fails_in_production_mode():
    with pytest.raises(ValueError, match="Configuration Error: Missing required secrets"):
        settings = Settings(
            MOCK_EXTERNAL_APIS=False,
            SARVAM_API_KEY=None,
            GEMINI_API_KEY=None,
        )
        settings.validate_production_keys()
