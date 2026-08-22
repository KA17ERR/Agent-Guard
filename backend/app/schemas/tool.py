"""
Pydantic schemas for the Tool sub-resource (POST/GET /api/agents/{id}/tools).
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

VALID_RISK_LEVELS = {"low", "medium", "high", "critical"}

_NAME_MAX = 100
_DESCRIPTION_MAX = 1_000


class ToolBase(BaseModel):
    model_config = {"str_strip_whitespace": True}

    name: str = Field(min_length=1, max_length=_NAME_MAX)
    description: str = Field(default="", max_length=_DESCRIPTION_MAX)
    destructive: bool = False
    risk_level: str = "low"

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be blank")
        return v

    @field_validator("risk_level")
    @classmethod
    def risk_level_valid(cls, v: str) -> str:
        if v not in VALID_RISK_LEVELS:
            raise ValueError(f"risk_level must be one of {sorted(VALID_RISK_LEVELS)}")
        return v


class ToolCreate(ToolBase):
    pass


class ToolRead(ToolBase):
    id: str
    agent_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
