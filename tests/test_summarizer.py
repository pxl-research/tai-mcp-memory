from unittest.mock import MagicMock, patch

import pytest

from utils.summarizer import Summarizer

_SAMPLE_TEXT = (
    "Quantum computing leverages quantum mechanics to perform calculations. "
    "Unlike classical computers that use bits, quantum computers use qubits "
    "which can exist in superposition, allowing parallel processing of vast "
    "amounts of information."
)


@pytest.fixture
def mock_summarizer():
    """Summarizer with a mocked OpenRouterClient so no real API calls are made."""
    with patch("utils.summarizer.OpenRouterClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Mocked summary output."
        mock_client.create_completions_stream.return_value = mock_response

        summarizer = Summarizer(api_key="fake-key")
        yield summarizer, mock_client


def test_generate_summary_abstractive(mock_summarizer):
    summarizer, mock_client = mock_summarizer
    result = summarizer.generate_summary(_SAMPLE_TEXT, summary_type="abstractive", length="medium")
    assert result == "Mocked summary output."
    mock_client.create_completions_stream.assert_called_once()


def test_generate_summary_extractive(mock_summarizer):
    summarizer, mock_client = mock_summarizer
    result = summarizer.generate_summary(_SAMPLE_TEXT, summary_type="extractive", length="short")
    assert result == "Mocked summary output."


def test_generate_summary_query_focused(mock_summarizer):
    summarizer, mock_client = mock_summarizer
    result = summarizer.generate_summary(
        _SAMPLE_TEXT,
        summary_type="query_focused",
        length="detailed",
        query="What are the benefits of quantum computing?",
    )
    assert result == "Mocked summary output."


def test_generate_summary_api_failure(mock_summarizer):
    summarizer, mock_client = mock_summarizer
    mock_client.create_completions_stream.side_effect = Exception("API error")
    result = summarizer.generate_summary(_SAMPLE_TEXT, summary_type="abstractive", length="short")
    assert result is None


def test_generate_summary_query_focused_no_query(mock_summarizer):
    """query_focused without a query raises ValueError before the try block — it propagates."""
    summarizer, mock_client = mock_summarizer
    with pytest.raises(ValueError, match="Query must be provided"):
        summarizer.generate_summary(_SAMPLE_TEXT, summary_type="query_focused", length="short")


def test_get_system_prompt_all_types():
    summarizer = Summarizer(api_key="fake-key")

    prompt = summarizer._get_system_prompt("abstractive", "medium", None)
    assert "abstractive" in prompt
    assert "3-5 sentences" in prompt

    prompt = summarizer._get_system_prompt("extractive", "short", None)
    assert "extractive" in prompt
    assert "1-2 sentences" in prompt

    prompt = summarizer._get_system_prompt("query_focused", "detailed", "What is a qubit?")
    assert "What is a qubit?" in prompt
    assert "5-10 sentences" in prompt


def test_get_system_prompt_query_focused_no_query_raises():
    summarizer = Summarizer(api_key="fake-key")
    with pytest.raises(ValueError, match="Query must be provided"):
        summarizer._get_system_prompt("query_focused", "short", None)
