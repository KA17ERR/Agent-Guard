"""
LLM provider abstraction layer.

AgentGuard talks to LLMs in exactly two ways everywhere in the codebase:
  1. generate_text()               -> free-form text (used by the Agent
                                       Executor's "thinking" turns)
  2. generate_structured_output()  -> a validated Pydantic object (used by
                                       Scenario Generation and tool-call
                                       decisions)

Every concrete provider (OpenAI today, Gemini/others later) implements this
same interface, so the rest of the app never imports openai/google.generativeai
directly — only app.llm.factory.get_llm_provider(). Swapping providers is a
one-line change in config, not a refactor.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Literal, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

Role = Literal["system", "user", "assistant"]


@dataclass
class LLMMessage:
    role: Role
    content: str


class LLMProvider(ABC):
    """Abstract interface every LLM backend must implement."""

    @abstractmethod
    def generate_text(
        self,
        messages: List[LLMMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: float = 30.0,
    ) -> str:
        """Return a plain-text completion for the given conversation."""
        raise NotImplementedError

    @abstractmethod
    def generate_structured_output(
        self,
        messages: List[LLMMessage],
        response_model: Type[T],
        *,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        timeout: float = 30.0,
    ) -> T:
        """Return a completion parsed and validated into `response_model`.

        Implementations are responsible for instructing the underlying model
        to emit JSON matching the schema, parsing that JSON, and validating
        it with Pydantic. Must raise LLMOutputValidationError (see
        app.llm.exceptions) if the model's output cannot be coerced into a
        valid `response_model` instance.
        """
        raise NotImplementedError
