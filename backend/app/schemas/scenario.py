"""
Schemas for Scenario Generation (Section 7):

    POST /api/scenarios/generate

`GeneratedScenario` is what the LLM is asked to produce, one per test case.
`GeneratedScenarioBatch` wraps a list of them so a single structured-output
call can request several at once — LLM providers only round-trip one
top-level JSON object, not a bare array.
"""
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, field_validator

VALID_CATEGORIES = {
    "normal_task",
    "ambiguous_instruction",
    "prompt_injection",
    "instruction_hijacking",
    "tool_misuse",
    "tool_loop",
    "hallucination",
    "goal_drift",
    "unsafe_destructive_action",
    "unauthorized_action",
}

VALID_SEVERITIES = {"low", "medium", "high", "critical"}


class GeneratedScenario(BaseModel):
    """Validated shape of one LLM-generated scenario. Bounded max_length on
    every free-text field guards against a misbehaving/adversarial LLM
    response ballooning what gets stored in the database."""

    model_config = {"str_strip_whitespace": True}

    category: str = Field(description="One of the AgentGuard scenario categories")
    severity: str = Field(description="low | medium | high | critical")
    user_input: str = Field(
        max_length=4_000, description="The simulated user message that kicks off the test"
    )
    expected_behavior: str = Field(
        max_length=4_000, description="What the agent SHOULD do when faced with this"
    )
    attack_strategy: str = Field(
        default="",
        max_length=2_000,
        description="For adversarial categories: the technique being used",
    )
    reason_for_test: str = Field(max_length=2_000, description="Why this scenario is worth testing")

    @field_validator("category")
    @classmethod
    def category_valid(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(f"category must be one of {sorted(VALID_CATEGORIES)}")
        return v

    @field_validator("severity")
    @classmethod
    def severity_valid(cls, v: str) -> str:
        if v not in VALID_SEVERITIES:
            raise ValueError(f"severity must be one of {sorted(VALID_SEVERITIES)}")
        return v

    @field_validator("user_input", "expected_behavior", "reason_for_test")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be blank")
        return v


class GeneratedScenarioBatch(BaseModel):
    """Top-level shape requested from the LLM — a JSON object (not a bare
    array) containing the list of scenarios, since structured-output mode
    requires a single JSON object at the root."""
    scenarios: List[GeneratedScenario]


class ScenarioGenerateRequest(BaseModel):
    model_config = {"str_strip_whitespace": True}

    agent_id: str = Field(min_length=1, max_length=64)
    number_of_scenarios: int = Field(default=8, ge=1, le=30)


class ScenarioRead(BaseModel):
    id: str
    agent_id: str
    category: str
    severity: str
    user_input: str
    expected_behavior: str
    metadata: dict = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_scenario(cls, scenario) -> "ScenarioRead":
        """Scenario.scenario_metadata (Python attr) -> ScenarioRead.metadata
        (API field name); done explicitly here rather than via a Pydantic
        alias so ORM attribute lookup stays unambiguous."""
        return cls(
            id=scenario.id,
            agent_id=scenario.agent_id,
            category=scenario.category,
            severity=scenario.severity,
            user_input=scenario.user_input,
            expected_behavior=scenario.expected_behavior,
            metadata=scenario.scenario_metadata,
            created_at=scenario.created_at,
        )


class ScenarioGenerateResponse(BaseModel):
    agent_id: str
    requested: int
    generated: int
    scenarios: List[ScenarioRead]
