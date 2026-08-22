"""
Error hierarchy for the LLM abstraction layer. Callers (scenario generation,
the agent executor, the /api/llm/test endpoint) catch `LLMError` and its
subclasses rather than provider-specific exceptions, so swapping providers
never changes error-handling code elsewhere in the app.
"""


class LLMError(Exception):
    """Base class for all LLM-layer errors."""


class LLMConfigurationError(LLMError):
    """Raised when a provider is selected but isn't configured (e.g. missing
    API key) — this is a setup problem, not a runtime API failure."""


class LLMTimeoutError(LLMError):
    """Raised when the underlying API call exceeds its timeout."""


class LLMAPIError(LLMError):
    """Raised when the underlying provider's API returns an error
    (auth failure, rate limit, 5xx, network error, etc.)."""


class LLMOutputValidationError(LLMError):
    """Raised when generate_structured_output() cannot parse/validate the
    model's response into the requested Pydantic schema."""
