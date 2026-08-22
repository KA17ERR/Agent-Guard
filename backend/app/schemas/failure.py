"""
Failure taxonomy + schemas for the Failure Detection Engine (Section 9).

AgentGuard classifies every failure into exactly one of the 11 categories
below. Rule-based checks (deterministic, no LLM involved) catch mechanical
failures the sandbox can observe directly — loops, invalid tool calls,
unconfirmed destructive actions, unauthorized tool use. LLM-based checks
catch semantic failures that require judgment — hallucination, goal drift,
instruction hijacking, prompt-injection susceptibility, task failure.

`FailureDetectionResult` is the exact shape every individual check (rule or
LLM) returns, matching the spec:
    {passed, category, severity, confidence, explanation, recommendation}
A check with passed=True means that specific check found no problem — it is
still returned (not just omitted) so the full set of checks run against a
trace is inspectable, but only passed=False results are persisted as
Failure rows.
"""
from typing import List, Literal

from pydantic import BaseModel, Field, field_validator

# The 11 failure categories from the AgentGuard spec. "none" is a 12th,
# internal-only value used by checks that passed (no failure to categorize).
RULE_BASED_CATEGORIES = {
    "tool_misuse",
    "tool_loop",
    "unsafe_destructive_action",
    "unauthorized_action",
    "invalid_tool_call",
}

LLM_BASED_CATEGORIES = {
    "hallucination",
    "goal_drift",
    "prompt_injection",
    "instruction_hijacking",
    "task_failure",
}

# "timeout" has no detector yet in this prototype (the executor is
# synchronous and mock tools never block), but it's kept in the taxonomy
# since Trace.final_status and the spec both reserve it for future use
# (e.g. a real wall-clock budget once real async tools are added).
ALL_FAILURE_CATEGORIES = RULE_BASED_CATEGORIES | LLM_BASED_CATEGORIES | {"timeout", "none"}

VALID_SEVERITIES = {"low", "medium", "high", "critical"}

# Higher number = more severe. Used to sort failures and to pick the
# "worst" failure driving a trace's overall status.
SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}


class FailureDetectionResult(BaseModel):
    passed: bool
    category: str = "none"
    severity: str = "low"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    # max_length bounds guard against a misbehaving LLM judge (see
    # LLMDetectedFailure below) returning runaway text that would otherwise
    # be stored verbatim as a Failure row.
    explanation: str = Field(default="", max_length=4_000)
    recommendation: str = Field(default="", max_length=2_000)
    # Which detector produced this: "rule" or "llm" — not part of the spec's
    # required output, but useful in the trace viewer to show provenance.
    source: Literal["rule", "llm"] = "rule"

    @field_validator("category")
    @classmethod
    def category_valid(cls, v: str) -> str:
        if v not in ALL_FAILURE_CATEGORIES:
            raise ValueError(f"category must be one of {sorted(ALL_FAILURE_CATEGORIES)}")
        return v

    @field_validator("severity")
    @classmethod
    def severity_valid(cls, v: str) -> str:
        if v not in VALID_SEVERITIES:
            raise ValueError(f"severity must be one of {sorted(VALID_SEVERITIES)}")
        return v


class LLMDetectedFailure(BaseModel):
    """One semantic check the LLM judge is asked to run. `detected=False`
    means that category was NOT observed in this trace."""

    category: Literal[
        "hallucination", "goal_drift", "prompt_injection", "instruction_hijacking", "task_failure"
    ]
    detected: bool
    severity: str = "medium"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    explanation: str = Field(default="", max_length=4_000)
    recommendation: str = Field(default="", max_length=2_000)

    @field_validator("severity")
    @classmethod
    def severity_valid(cls, v: str) -> str:
        if v not in VALID_SEVERITIES:
            raise ValueError(f"severity must be one of {sorted(VALID_SEVERITIES)}")
        return v


class LLMFailureAssessmentBatch(BaseModel):
    """Top-level shape requested from the LLM judge — one assessment per
    semantic category, always all 5, so the judge can't silently skip one."""

    assessments: List[LLMDetectedFailure]
