import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
import sys
import os
import httpx
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gemini_client import get_conversational_chain  # Replace with your actual module name


@patch("gemini_client.ChatGoogleGenerativeAI")
def test_get_conversational_chain_success(mock_chat_model):
    """Test successful creation of conversational chain."""
    mock_model_instance = MagicMock()
    mock_chat_model.return_value = mock_model_instance

    chain = get_conversational_chain()
    assert chain is not None
    mock_chat_model.assert_called_once_with(model="gemini-1.5-flash")


@patch("gemini_client.time.sleep", return_value=None)  # Mock time.sleep to avoid delays
@patch("gemini_client.ChatGoogleGenerativeAI")
def test_get_conversational_chain_rate_limit(mock_chat_model, mock_sleep):
    """Test handling of API rate-limiting with retry."""
    response_mock = MagicMock()
    response_mock.status_code = 429
    response_mock.headers = {"Retry-After": "1"}
    response_mock.text = "Rate limit exceeded"

    def mock_side_effect(*args, **kwargs):
        raise httpx.HTTPStatusError("429 Too Many Requests", request=None, response=response_mock)

    mock_chat_model.side_effect = mock_side_effect

    with pytest.raises(HTTPException) as exc_info:
        get_conversational_chain()

    assert exc_info.value.status_code == 429
    assert "Gemini API Error" in exc_info.value.detail
    assert mock_sleep.call_count == 5  # Retries up to the max_retries limit

@patch("gemini_client.ChatGoogleGenerativeAI")
def test_get_conversational_chain_request_error(mock_chat_model):
    """Test handling of connection or timeout errors."""
    def mock_side_effect(*args, **kwargs):
        raise httpx.RequestError("Connection error", request=None)

    mock_chat_model.side_effect = mock_side_effect

    with pytest.raises(HTTPException) as exc_info:
        get_conversational_chain()

    assert exc_info.value.status_code == 504
    assert "Timeout or connection error" in exc_info.value.detail


@patch("gemini_client.ChatGoogleGenerativeAI")
def test_get_conversational_chain_unexpected_error(mock_chat_model):
    """Test handling of unexpected errors."""
    mock_chat_model.side_effect = Exception("Unexpected error")

    with pytest.raises(HTTPException) as exc_info:
        get_conversational_chain()

    assert exc_info.value.status_code == 500
    assert "Unexpected error" in exc_info.value.detail
