"""
A scripted fake LLMProvider used by tests so Sections 7 and 8 can be tested
deterministically without hitting a real OpenAI/Gemini API or requiring a
configured API key.
"""
from typing import List, Type

from app.llm.base import LLMMessage, LLMProvider, T
from app.llm.exceptions import LLMOutputValidationError


class FakeLLMProvider(LLMProvider):
    """Returns pre-scripted structured outputs in order; generate_text just
    echoes a canned string. `structured_outputs` should be a list of
    BaseModel instances (of whatever type the caller will request) that are
    handed back one at a time, in order, on each call."""

    def __init__(
        self,
        structured_outputs: list | None = None,
        text_output: str = "ok",
        raise_error: Exception | None = None,
    ):
        self._structured_outputs = list(structured_outputs or [])
        self._text_output = text_output
        # If set, every generate_structured_output()/generate_text() call
        # raises this instead of returning a scripted value — used to
        # simulate LLM-layer failures (timeouts, invalid output, etc.)
        # without needing a real API call.
        self._raise_error = raise_error
        self.calls: list = []

    def generate_text(self, messages: List[LLMMessage], **kwargs) -> str:
        self.calls.append(("text", messages))
        if self._raise_error:
            raise self._raise_error
        return self._text_output

    def generate_structured_output(
        self, messages: List[LLMMessage], response_model: Type[T], **kwargs
    ) -> T:
        self.calls.append(("structured", messages, response_model))
        if self._raise_error:
            raise self._raise_error
        if not self._structured_outputs:
            raise LLMOutputValidationError("FakeLLMProvider has no more scripted outputs")
        return self._structured_outputs.pop(0)
