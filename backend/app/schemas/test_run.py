"""
Schemas for the Test Runner API (Section 11):

    POST /api/test-runs
    GET  /api/test-runs/{run_id}
    GET  /api/test-runs/{run_id}/traces
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.services.scoring_service import CategoryScores


class TestRunCreateRequest(BaseModel):
    model_config = {"str_strip_whitespace": True}

    agent_id: str = Field(min_length=1, max_length=64)
    # Capped so a single request can't force the runner to execute an
    # unbounded number of LLM-backed scenario runs (each one is a real,
    # billed LLM call) in one go.
    scenario_ids: List[str] = Field(min_length=1, max_length=50)


class TestRunCreateResponse(BaseModel):
    run_id: str
    total_tests: int
    passed: int
    failed: int
    critical_failures: int
    major_failures: int
    minor_failures: int
    reliability_score: float
    category_scores: CategoryScores


class TestRunRead(BaseModel):
    id: str
    agent_id: str
    version: str
    status: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    reliability_score: Optional[float] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class FailureRead(BaseModel):
    id: str
    category: str
    severity: str
    confidence: float
    explanation: str
    recommendation: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TraceRead(BaseModel):
    id: str
    scenario_id: str
    events: List[Dict[str, Any]]
    agent_response: str
    tool_calls: List[Dict[str, Any]]
    final_status: str
    created_at: datetime
    failures: List[FailureRead] = []

    model_config = {"from_attributes": True}


class TestRunTracesResponse(BaseModel):
    run_id: str
    traces: List[TraceRead]
