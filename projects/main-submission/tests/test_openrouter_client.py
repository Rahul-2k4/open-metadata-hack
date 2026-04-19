import os
from unittest.mock import patch

from incident_copilot.openrouter_client import get_client, is_available


def test_is_available_false_when_no_key():
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("OPENROUTER_API_KEY", None)
        assert is_available() is False


def test_is_available_true_when_key_set():
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test"}):
        assert is_available() is True


def test_get_client_returns_openai_client():
    from openai import OpenAI
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test"}):
        client = get_client()
        assert isinstance(client, OpenAI)
        assert "openrouter" in str(client.base_url)
