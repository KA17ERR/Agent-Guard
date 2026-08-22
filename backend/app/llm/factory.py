"""
Factory for LLM providers. This is the ONLY place in the app that decides
which concrete provider class to instantiate — everything else (scenario
generation, the agent executor, the /api/llm/test endpoint) depends only on
the LLMProvider interface. Adding a new provider later means adding one
branch here and one new provider module; nothing else changes.
"""
from app.core.config import Settings, get_settings
from app.llm.base import LLMProvider
from app.llm.exceptions import LLMConfigurationError


def get_llm_provider(settings: Settings | None = None) -> LLMProvider:
    settings = settings or get_settings()
    provider = settings.llm_provider.lower().strip()

    if provider == "openai":
        from app.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(api_key=settings.openai_api_key, model=settings.openai_model)

    if provider == "gemini":
        from app.llm.gemini_provider import GeminiProvider

        return GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)

    raise LLMConfigurationError(
        f"Unknown LLM_PROVIDER '{settings.llm_provider}'. Expected 'openai' or 'gemini'."
    )
