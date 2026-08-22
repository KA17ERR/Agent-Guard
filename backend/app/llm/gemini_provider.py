"""
Gemini implementation of LLMProvider.

Uses Google's Generative AI SDK (`google-generativeai`). Structured output
is requested via Gemini's native JSON mode
(`response_mime_type="application/json"`) plus an explicit schema
description in the prompt, then parsed and validated with Pydantic —
same pattern as OpenAIProvider: JSON mode guarantees syntactically valid
JSON but not that it matches OUR schema, so validation still happens on
our side either way.
"""
import json
from typing import List, Type

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from pydantic import ValidationError

from app.llm.base import LLMMessage, LLMProvider, T
from app.llm.exceptions import (
    LLMAPIError,
    LLMConfigurationError,
    LLMOutputValidationError,
    LLMTimeoutError,
)


def _split_system_prompt(messages: List[LLMMessage]) -> tuple[str, list]:
    """Gemini takes a single system_instruction plus a user/model turn
    history, not an OpenAI-style flat list of role messages. We concatenate
    every "system" message (there's sometimes more than one — see
    OpenAIProvider's schema_hint pattern) into one system_instruction, and
    map the rest onto Gemini's "user"/"model" roles."""
    system_parts = [m.content for m in messages if m.role == "system"]
    turns = []
    for m in messages:
        if m.role == "system":
            continue
        gemini_role = "model" if m.role == "assistant" else "user"
        turns.append({"role": gemini_role, "parts": [m.content]})
    return "\n\n".join(system_parts), turns


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise LLMConfigurationError(
                "GEMINI_API_KEY is not set. Add it to your .env file "
                "(see .env.example) before using the Gemini provider. "
                "Get a free key at https://aistudio.google.com/apikey"
            )
        self._api_key = api_key
        self._model_name = model
        genai.configure(api_key=api_key)

    def _build_model(self, system_instruction: str = "", **generation_kwargs):
        return genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=system_instruction or None,
            generation_config=genai.types.GenerationConfig(**generation_kwargs),
        )

    def generate_text(
        self,
        messages: List[LLMMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: float = 30.0,
    ) -> str:
        system_instruction, turns = _split_system_prompt(messages)
        model = self._build_model(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        try:
            response = model.generate_content(turns, request_options={"timeout": timeout})
        except google_exceptions.DeadlineExceeded as exc:
            raise LLMTimeoutError(f"Gemini request timed out after {timeout}s") from exc
        except google_exceptions.GoogleAPIError as exc:
            raise LLMAPIError(f"Gemini API error: {exc}") from exc

        return response.text or ""

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
        system_instruction, turns = _split_system_prompt(messages)
        system_instruction = (
            f"{system_instruction}\n\n{schema_hint}" if system_instruction else schema_hint
        )

        model = self._build_model(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
        )

        try:
            response = model.generate_content(turns, request_options={"timeout": timeout})
        except google_exceptions.DeadlineExceeded as exc:
            raise LLMTimeoutError(f"Gemini request timed out after {timeout}s") from exc
        except google_exceptions.GoogleAPIError as exc:
            raise LLMAPIError(f"Gemini API error: {exc}") from exc

        raw = response.text or ""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMOutputValidationError(
                f"Gemini did not return valid JSON: {exc}. Raw output: {raw[:500]}"
            ) from exc

        try:
            return response_model.model_validate(data)
        except ValidationError as exc:
            raise LLMOutputValidationError(
                f"Gemini JSON output did not match {response_model.__name__} schema: {exc}"
            ) from exc
