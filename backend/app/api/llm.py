"""
LLM connectivity check.

    GET /api/llm/test

Exercises both generate_text() and generate_structured_output() against
whichever provider is configured (LLM_PROVIDER in .env), so a broken API key
or network issue shows up here instead of surfacing confusingly later during
scenario generation or agent execution.
"""
from fastapi import APIRouter

from app.core.config import get_settings
from app.llm.base import LLMMessage
from app.llm.exceptions import LLMError
from app.llm.factory import get_llm_provider
from app.schemas.llm import LLMTestResponse, _PingReply

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.get("/test", response_model=LLMTestResponse)
def test_llm_connection():
    settings = get_settings()
    model_name = (
        settings.openai_model if settings.llm_provider == "openai" else settings.gemini_model
    )

    try:
        provider = get_llm_provider(settings)

        text = provider.generate_text(
            [
                LLMMessage(role="system", content="You are a terse test assistant."),
                LLMMessage(role="user", content="Reply with the single word: pong"),
            ],
            max_tokens=16,
            timeout=15.0,
        )

        # Also exercise the structured-output path so both interface methods
        # are verified in one health check.
        structured = provider.generate_structured_output(
            [
                LLMMessage(
                    role="user",
                    content='Reply with JSON: {"reply": "pong"}',
                )
            ],
            _PingReply,
            timeout=15.0,
        )

        return LLMTestResponse(
            provider=settings.llm_provider,
            model=model_name,
            ok=True,
            sample_output=f"text={text.strip()!r} structured={structured.reply!r}",
        )
    except LLMError as exc:
        return LLMTestResponse(
            provider=settings.llm_provider,
            model=model_name,
            ok=False,
            error=str(exc),
        )
