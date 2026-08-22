"""
Schemas for the Reliability Report API (Section 10):

    GET /api/test-runs/{run_id}/report
"""
from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel

from app.services.scoring_service import CategoryScores


class ReliabilityReport(BaseModel):
    run_id: str
    agent_id: str
    agent_name: str
    agent_version: str
    status: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    reliability_score: float
    category_scores: CategoryScores
    critical_failures: int
    major_failures: int
    minor_failures: int
    failures_by_category: Dict[str, int]
    started_at: datetime
    completed_at: Optional[datetime] = None
