"""
Tests for GeminiProvider — mirrors the OpenAIProvider tests in test_llm.py.

The google-generativeai SDK is mocked out entirely (via monkeypatch on
genai.GenerativeModel) so these tests run instantly and never make a real
network call or require a real API key.
"""
from types import SimpleNamespace

import pytest
from pydantic import BaseModel, ValidationError

from app.llm.base import LLMMessage
from app.llm.exceptions import (
    LLMAPIError,
    LLMConfigurationError,
    LLMOutputValidationError,
    LLMTimeoutError,
)
from app.llm.gemini_provider import GeminiProvider


class _Reply(BaseModel):
    reply: str


def test_gemini_provider_requires_api_key():
    with pytest.raises(LLMConfigurationError):
        GeminiProvider(api_key="", model="gemini-1.5-flash")


def test_gemini_generate_text_returns_response_text(monkeypatch):
    provider = GeminiProvider(api_key="fake-key", model="gemini-1.5-flash")

    class _FakeModel:
        def __init__(self, **kwargs):
            pass

        def generate_content(self, turns, request_options=None):
            return SimpleNamespace(text="pong")

    monkeypatch.setattr("app.llm.gemini_provider.genai.GenerativeModel", _FakeModel)

    result = provider.generate_text([LLMMessage(role="user", content="ping")])
    assert result == "pong"


def test_gemini_generate_structured_output_parses_and_validates(monkeypatch):
    provider = GeminiProvider(api_key="fake-key", model="gemini-1.5-flash")

    class _FakeModel:
        def __init__(self, **kwargs):
            pass

        def generate_content(self, turns, request_options=None):
            return SimpleNamespace(text='{"reply": "pong"}')

    monkeypatch.setattr("app.llm.gemini_provider.genai.GenerativeModel", _FakeModel)

    result = provider.generate_structured_output(
        [LLMMessage(role="user", content="reply with JSON")], _Reply
    )
    assert result.reply == "pong"


def test_gemini_generate_structured_output_raises_on_invalid_json(monkeypatch):
    provider = GeminiProvider(api_key="fake-key", model="gemini-1.5-flash")

    class _FakeModel:
        def __init__(self, **kwargs):
            pass

        def generate_content(self, turns, request_options=None):
            return SimpleNamespace(text="not valid json at all")

    monkeypatch.setattr("app.llm.gemini_provider.genai.GenerativeModel", _FakeModel)

    with pytest.raises(LLMOutputValidationError):
        provider.generate_structured_output([LLMMessage(role="user", content="x")], _Reply)


def test_gemini_generate_structured_output_raises_on_schema_mismatch(monkeypatch):
    provider = GeminiProvider(api_key="fake-key", model="gemini-1.5-flash")

    class _FakeModel:
        def __init__(self, **kwargs):
            pass

        def generate_content(self, turns, request_options=None):
            # Valid JSON, but missing the required "reply" field.
            return SimpleNamespace(text='{"unexpected_field": "oops"}')

    monkeypatch.setattr("app.llm.gemini_provider.genai.GenerativeModel", _FakeModel)

    with pytest.raises(LLMOutputValidationError):
        provider.generate_structured_output([LLMMessage(role="user", content="x")], _Reply)


def test_gemini_generate_text_wraps_timeout(monkeypatch):
    from google.api_core import exceptions as google_exceptions

    provider = GeminiProvider(api_key="fake-key", model="gemini-1.5-flash")

    class _FakeModel:
        def __init__(self, **kwargs):
            pass

        def generate_content(self, turns, request_options=None):
            raise google_exceptions.DeadlineExceeded("timed out")

    monkeypatch.setattr("app.llm.gemini_provider.genai.GenerativeModel", _FakeModel)

    with pytest.raises(LLMTimeoutError):
        provider.generate_text([LLMMessage(role="user", content="x")])


def test_gemini_generate_text_wraps_api_error(monkeypatch):
    from google.api_core import exceptions as google_exceptions

    provider = GeminiProvider(api_key="fake-key", model="gemini-1.5-flash")

    class _FakeModel:
        def __init__(self, **kwargs):
            pass

        def generate_content(self, turns, request_options=None):
            raise google_exceptions.ResourceExhausted("quota exceeded")

    monkeypatch.setattr("app.llm.gemini_provider.genai.GenerativeModel", _FakeModel)

    with pytest.raises(LLMAPIError):
        provider.generate_text([LLMMessage(role="user", content="x")])


def test_split_system_prompt_separates_system_from_turns():
    from app.llm.gemini_provider import _split_system_prompt

    messages = [
        LLMMessage(role="system", content="You are terse."),
        LLMMessage(role="user", content="Hello"),
        LLMMessage(role="assistant", content="Hi there"),
        LLMMessage(role="system", content="Always JSON."),
    ]
    system_instruction, turns = _split_system_prompt(messages)

    assert "You are terse." in system_instruction
    assert "Always JSON." in system_instruction
    assert turns == [
        {"role": "user", "parts": ["Hello"]},
        {"role": "model", "parts": ["Hi there"]},
    ]
