"""
Deterministic Replay API.

    POST /api/traces/{trace_id}/replay  (Section 12)
"""
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.replay import (
    ReplayTimelineStep,
    ToolCallReplayComparison,
    TraceReplayResponse,
)
from app.schemas.test_run import FailureRead
from app.services import replay_service

router = APIRouter(prefix="/api/traces", tags=["traces"])

_ID_MAX_LEN = 64


@router.post("/{trace_id}/replay", response_model=TraceReplayResponse)
def replay_trace(trace_id: str = Path(max_length=_ID_MAX_LEN), db: Session = Depends(get_db)):
    try:
        result = replay_service.replay_trace(db, trace_id)
    except replay_service.TraceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    trace = result.trace
    run = trace.test_run

    return TraceReplayResponse(
        trace_id=trace.id,
        test_run_id=trace.test_run_id,
        scenario_id=trace.scenario_id,
        agent_id=run.agent_id,
        agent_version=run.version,
        original_final_status=trace.final_status,
        deterministic=result.deterministic,
        total_steps=len(result.timeline),
        timeline=[ReplayTimelineStep(**step) for step in result.timeline],
        tool_call_comparisons=[
            ToolCallReplayComparison(
                step=c.step,
                tool_name=c.tool_name,
                params=c.params,
                original_success=c.original_success,
                original_data=c.original_data,
                original_error=c.original_error,
                replayed_success=c.replayed_success,
                replayed_data=c.replayed_data,
                replayed_error=c.replayed_error,
                match=c.match,
            )
            for c in result.comparisons
        ],
        failures=[FailureRead.model_validate(f) for f in trace.failures],
        replayed_at=result.replayed_at,
    )
