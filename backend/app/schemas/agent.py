"""
Pydantic schemas for the Agent Configuration API
(POST/GET/PUT/DELETE /api/agents).
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.tool import ToolRead

# Generous but bounded — prevents an accidental (or malicious) multi-MB
# payload from being stored as an "agent name" while still comfortably
# fitting any realistic system prompt.
_NAME_MAX = 200
_DOMAIN_MAX = 200
_VERSION_MAX = 50
_SYSTEM_PROMPT_MAX = 20_000
_DESCRIPTION_MAX = 2_000


class AgentBase(BaseModel):
    model_config = {"str_strip_whitespace": True}

    name: str = Field(min_length=1, max_length=_NAME_MAX)
    domain: str = Field(min_length=1, max_length=_DOMAIN_MAX)
    system_prompt: str = Field(min_length=1, max_length=_SYSTEM_PROMPT_MAX)
    version: str = Field(default="v1", min_length=1, max_length=_VERSION_MAX)
    description: str = Field(default="", max_length=_DESCRIPTION_MAX)

    @field_validator("name", "domain", "system_prompt", "version")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be blank")
        return v


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    """Full update (PUT) — all fields optional so a client can send a partial
    body if desired, but this endpoint is intended to replace the agent's
    configuration wholesale."""

    model_config = {"str_strip_whitespace": True}

    name: Optional[str] = Field(default=None, max_length=_NAME_MAX)
    domain: Optional[str] = Field(default=None, max_length=_DOMAIN_MAX)
    system_prompt: Optional[str] = Field(default=None, max_length=_SYSTEM_PROMPT_MAX)
    version: Optional[str] = Field(default=None, max_length=_VERSION_MAX)
    description: Optional[str] = Field(default=None, max_length=_DESCRIPTION_MAX)

    @field_validator("name", "domain", "system_prompt", "version")
    @classmethod
    def not_blank_if_present(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("must not be blank")
        return v


class AgentRead(AgentBase):
    id: str
    created_at: datetime
    tools: List[ToolRead] = []

    model_config = {"from_attributes": True}
