"""
Builds the Reliability Report (Section 10) for an already-completed
TestRun by reading its persisted Traces and Failures back from the
database and re-running the same deterministic scoring formula
(`scoring_service.compute_reliability`) used right after the run
completed. Recomputing from stored data — rather than caching the score
breakdown — keeps the report always consistent with the actual persisted
failures, with no separate cache to go stale.
"""
from collections import Counter
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.agent import Agent
from app.models.test_run import TestRun
from app.models.trace import Trace
from app.schemas.report import ReliabilityReport
from app.services.scoring_service import TraceScoreInput, compute_reliability


def get_test_run_with_traces(db: Session, run_id: str) -> Optional[TestRun]:
    return (
        db.query(TestRun)
        .options(joinedload(TestRun.traces).joinedload(Trace.failures))
        .filter(TestRun.id == run_id)
        .first()
    )


def build_report(db: Session, run: TestRun, agent: Agent) -> ReliabilityReport:
    trace_inputs = [
        TraceScoreInput(final_status=trace.final_status, failures=list(trace.failures))
        for trace in run.traces
    ]
    score_result = compute_reliability(trace_inputs)

    failures_by_category = Counter(
        f.category for trace in run.traces for f in trace.failures
    )

    return ReliabilityReport(
        run_id=run.id,
        agent_id=agent.id,
        agent_name=agent.name,
        agent_version=run.version,
        status=run.status,
        total_tests=run.total_tests,
        passed_tests=run.passed_tests,
        failed_tests=run.failed_tests,
        reliability_score=run.reliability_score or 0.0,
        category_scores=score_result.category_scores,
        critical_failures=score_result.critical_failures,
        major_failures=score_result.major_failures,
        minor_failures=score_result.minor_failures,
        failures_by_category=dict(failures_by_category),
        started_at=run.started_at,
        completed_at=run.completed_at,
    )
