"""
Test Runner + Reliability Report API.

    POST /api/test-runs                  (Section 11)
    GET  /api/test-runs/{run_id}         (Section 11)
    GET  /api/test-runs/{run_id}/traces  (Section 11)
    GET  /api/test-runs/{run_id}/report  (Section 10)
"""
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.llm.exceptions import LLMConfigurationError
from app.llm.factory import get_llm_provider
from app.models.test_run import TestRun
from app.models.trace import Trace
from app.schemas.report import ReliabilityReport
from app.schemas.test_run import (
    FailureRead,
    TestRunCreateRequest,
    TestRunCreateResponse,
    TestRunRead,
    TestRunTracesResponse,
    TraceRead,
)
from app.services import report_service, test_runner_service

router = APIRouter(prefix="/api/test-runs", tags=["test-runs"])

_ID_MAX_LEN = 64


def _get_run_or_404(db: Session, run_id: str) -> TestRun:
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail=f"Test run '{run_id}' not found")
    return run


@router.post("", response_model=TestRunCreateResponse, status_code=201)
def create_test_run(payload: TestRunCreateRequest, db: Session = Depends(get_db)):
    try:
        llm_provider = get_llm_provider()
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        run, score_result = test_runner_service.run_test_run(
            db, payload.agent_id, payload.scenario_ids, llm_provider
        )
    except test_runner_service.AgentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except test_runner_service.ScenarioNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return TestRunCreateResponse(
        run_id=run.id,
        total_tests=run.total_tests,
        passed=run.passed_tests,
        failed=run.failed_tests,
        critical_failures=score_result.critical_failures,
        major_failures=score_result.major_failures,
        minor_failures=score_result.minor_failures,
        reliability_score=run.reliability_score,
        category_scores=score_result.category_scores,
    )


@router.get("/{run_id}", response_model=TestRunRead)
def get_test_run(run_id: str = Path(max_length=_ID_MAX_LEN), db: Session = Depends(get_db)):
    return _get_run_or_404(db, run_id)


@router.get("/{run_id}/traces", response_model=TestRunTracesResponse)
def get_test_run_traces(
    run_id: str = Path(max_length=_ID_MAX_LEN), db: Session = Depends(get_db)
):
    run = (
        db.query(TestRun)
        .options(joinedload(TestRun.traces).joinedload(Trace.failures))
        .filter(TestRun.id == run_id)
        .first()
    )
    if run is None:
        raise HTTPException(status_code=404, detail=f"Test run '{run_id}' not found")

    traces = [
        TraceRead(
            id=trace.id,
            scenario_id=trace.scenario_id,
            events=trace.events,
            agent_response=trace.agent_response,
            tool_calls=trace.tool_calls,
            final_status=trace.final_status,
            created_at=trace.created_at,
            failures=[FailureRead.model_validate(f) for f in trace.failures],
        )
        for trace in run.traces
    ]
    return TestRunTracesResponse(run_id=run.id, traces=traces)


@router.get("/{run_id}/report", response_model=ReliabilityReport)
def get_test_run_report(
    run_id: str = Path(max_length=_ID_MAX_LEN), db: Session = Depends(get_db)
):
    run = report_service.get_test_run_with_traces(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Test run '{run_id}' not found")
    return report_service.build_report(db, run, run.agent)
