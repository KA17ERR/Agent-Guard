"""
Tests for the LLM abstraction layer — Section 6 of AgentGuard.
"""
import pytest
from pydantic import BaseModel

from app.core.config import Settings
from app.llm.exceptions import LLMConfigurationError
from app.llm.factory import get_llm_provider
from tests.fakes import FakeLLMProvider


def test_openai_provider_requires_api_key():
    settings = Settings(llm_provider="openai", openai_api_key="", database_url="sqlite://")
    with pytest.raises(LLMConfigurationError):
        get_llm_provider(settings)


def test_openai_provider_constructs_with_api_key():
    settings = Settings(
        llm_provider="openai", openai_api_key="sk-test-fake", database_url="sqlite://"
    )
    provider = get_llm_provider(settings)
    assert provider is not None


def test_unknown_provider_raises_configuration_error():
    settings = Settings(llm_provider="not-a-real-provider", database_url="sqlite://")
    with pytest.raises(LLMConfigurationError):
        get_llm_provider(settings)


class _Reply(BaseModel):
    reply: str


def test_fake_provider_generate_text_and_structured_output():
    """Exercises the LLMProvider interface shape itself via the test double
    used by Sections 7/8 tests."""
    fake = FakeLLMProvider(structured_outputs=[_Reply(reply="pong")], text_output="pong")

    text = fake.generate_text([])
    assert text == "pong"

    structured = fake.generate_structured_output([], _Reply)
    assert structured.reply == "pong"
