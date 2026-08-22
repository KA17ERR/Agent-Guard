"""
Schemas for the Regression Tracker API (Section 13):

    GET /api/agents/{agent_id}/regression
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class RegressionRunSummary(BaseModel):
    run_id: str
    version: str
    reliability_score: float
    total_tests: int
    passed_tests: int
    failed_tests: int
    completed_at: Optional[datetime] = None


class DimensionChange(BaseModel):
    """version_a / version_b are the raw 0-100 scores for that dimension on
    each run; `change` is version_b - version_a (positive = improvement,
    negative = regression)."""

    version_a: float
    version_b: float
    change: float


class ScenarioRegressionDetail(BaseModel):
    scenario_id: str
    previous_status: str
    new_status: str
    previous_worst_severity: str
    new_worst_severity: str
    reason: str


class RegressionReport(BaseModel):
    agent_id: str
    agent_name: str
    run_a: RegressionRunSummary
    run_b: RegressionRunSummary

    overall: DimensionChange
    safety: DimensionChange
    tool_reliability: DimensionChange
    goal_adherence: DimensionChange
    truthfulness: DimensionChange
    task_success: DimensionChange

    newly_failing_scenarios: List[str]
    newly_passing_scenarios: List[str]
    scenario_regressions: List[ScenarioRegressionDetail]

    is_regression: bool
    regression_reasons: List[str]
