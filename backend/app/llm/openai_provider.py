"""
OpenAI implementation of LLMProvider.

Uses the Chat Completions API. Structured output is requested via
`response_format={"type": "json_object"}` plus an explicit schema
description in the prompt, then parsed and validated with Pydantic —
OpenAI's JSON mode guarantees syntactically valid JSON but not that it
matches our schema, so validation still has to happen on our side.
"""
import json
from typing import List, Type

import openai
from pydantic import BaseModel, ValidationError

from app.llm.base import LLMMessage, LLMProvider, T
from app.llm.exceptions import (
    LLMAPIError,
    LLMConfigurationError,
    LLMOutputValidationError,
    LLMTimeoutError,
)


def _to_openai_messages(messages: List[LLMMessage]) -> list:
    return [{"role": m.role, "content": m.content} for m in messages]


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise LLMConfigurationError(
                "OPENAI_API_KEY is not set. Add it to your .env file "
                "(see .env.example) before using the OpenAI provider."
            )
        self._model = model
        self._client = openai.OpenAI(api_key=api_key)

    def generate_text(
        self,
        messages: List[LLMMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: float = 30.0,
    ) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=_to_openai_messages(messages),
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
        except openai.APITimeoutError as exc:
            raise LLMTimeoutError(f"OpenAI request timed out after {timeout}s") from exc
        except openai.APIError as exc:
            raise LLMAPIError(f"OpenAI API error: {exc}") from exc

        content = response.choices[0].message.content
        return content or ""

    def generate_structured_output(
        self,
        messages: List[LLMMessage],
        response_model: Type[T],
        *,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        timeout: float = 30.0,
    ) -> T:
        schema_hint = (
            "Respond with ONLY a single valid JSON object — no markdown "
            "fences, no commentary before or after it. It must conform to "
            f"this JSON schema:\n{json.dumps(response_model.model_json_schema())}"
        )
        openai_messages = _to_openai_messages(messages)
        openai_messages.append({"role": "system", "content": schema_hint})

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
                response_format={"type": "json_object"},
            )
        except openai.APITimeoutError as exc:
            raise LLMTimeoutError(f"OpenAI request timed out after {timeout}s") from exc
        except openai.APIError as exc:
            raise LLMAPIError(f"OpenAI API error: {exc}") from exc

        raw = response.choices[0].message.content or ""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMOutputValidationError(
                f"OpenAI did not return valid JSON: {exc}. Raw output: {raw[:500]}"
            ) from exc

        try:
            return response_model.model_validate(data)
        except ValidationError as exc:
            raise LLMOutputValidationError(
                f"OpenAI JSON output did not match {response_model.__name__} schema: {exc}"
            ) from exc
