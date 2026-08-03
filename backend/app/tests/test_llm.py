"""
Unittests for app/services/llm.py

Mocker requests.post så vi tester logikken (provider-valg, fallback)
uden at have en rigtig Ollama-server eller Mistral API-nøgle tilgængelig.
"""

from unittest.mock import Mock, patch

from app.services import llm


def test_call_ollama_returns_response_text():
    fake_response = Mock()
    fake_response.raise_for_status = Mock()
    fake_response.json.return_value = {"response": "Spis mere protein."}

    with patch("app.services.llm.requests.post", return_value=fake_response):
        result = llm._call_ollama("test prompt")

    assert result == "Spis mere protein."


def test_call_ollama_fallback_on_error():
    import requests

    error = requests.RequestException("connection refused")
    with patch("app.services.llm.requests.post", side_effect=error):
        result = llm._call_ollama("test prompt")

    assert result == llm.FALLBACK_MESSAGE


def test_call_mistral_without_api_key_returns_fallback():
    with patch.object(llm, "MISTRAL_API_KEY", ""):
        result = llm._call_mistral("test prompt")

    assert result == llm.FALLBACK_MESSAGE


def test_generate_recommendation_uses_ollama_by_default():
    fake_response = Mock()
    fake_response.raise_for_status = Mock()
    fake_response.json.return_value = {"response": "Godt arbejde denne uge!"}

    with patch.object(llm, "LLM_PROVIDER", "ollama"):
        with patch("app.services.llm.requests.post", return_value=fake_response):
            result = llm.generate_recommendation("nogle data")

    assert result == "Godt arbejde denne uge!"


def test_generate_recommendation_switches_to_mistral_via_provider():
    fake_response = Mock()
    fake_response.raise_for_status = Mock()
    fake_response.json.return_value = {"choices": [{"message": {"content": "Fortsæt sådan!"}}]}

    with patch.object(llm, "LLM_PROVIDER", "mistral"):
        with patch.object(llm, "MISTRAL_API_KEY", "fake-key"):
            with patch("app.services.llm.requests.post", return_value=fake_response):
                result = llm.generate_recommendation("nogle data")

    assert result == "Fortsæt sådan!"
