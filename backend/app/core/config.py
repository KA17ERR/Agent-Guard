"""
Central application settings.

All configuration is loaded from environment variables (or a local .env file
during development). No secrets are ever hardcoded here — see .env.example
for the full list of variables this app understands.
"""
import logging
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("agentguard.config")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- LLM provider abstraction ---
    llm_provider: str = "openai"  # "openai" | "gemini"

    # repr=False so these never appear if a Settings instance is ever
    # printed or logged (e.g. accidentally, in a debugging session) —
    # secrets should only ever be read programmatically, never displayed.
    openai_api_key: str = Field(default="", repr=False)
    openai_model: str = "gpt-4o-mini"

    gemini_api_key: str = Field(default="", repr=False)
    gemini_model: str = "gemini-3.6-flash"

    # --- Database ---
    database_url: str = "sqlite:///./agentguard.db"

    # --- CORS ---
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # --- Logging ---
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @field_validator("cors_origins")
    @classmethod
    def cors_origins_not_wildcard(cls, v: str) -> str:
        if v.strip() == "*":
            # Browsers reject "*" combined with allow_credentials=True
            # anyway, but fail loudly here rather than shipping a CORS
            # config that silently doesn't work (or that someone "fixes"
            # by disabling credentials/tightening nothing).
            raise ValueError(
                "CORS_ORIGINS must not be '*'. List the exact frontend "
                "origin(s) allowed to call this API, comma-separated."
            )
        return v

    @field_validator("log_level")
    @classmethod
    def log_level_valid(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.strip().upper()
        if upper not in valid:
            raise ValueError(f"LOG_LEVEL must be one of {sorted(valid)}")
        return upper


@lru_cache
def get_settings() -> Settings:
    """Settings are cached so the environment is only parsed once per process."""
    return Settings()
