"""
Schemas for the Deterministic Replay API (Section 12):

    POST /api/traces/{trace_id}/replay

A Trace already persists everything a replay needs (see app/models/trace.py):
`events` is the exact ordered record of every LLM decision, tool call, and
final response from the original run, and `tool_calls` is the denormalized
list of mock tool inputs + outputs. Replay does not call the LLM again — it
re-executes ONLY the recorded mock tool calls against a freshly-seeded
sandbox and reports whether they reproduce byte-identical results, which is
the concrete meaning of "deterministic" here.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.schemas.test_run import FailureRead


class ReplayTimelineStep(BaseModel):
    """One step in the UI-friendly execution timeline. Mirrors the stored
    TraceEvent shape (step/type/data) so the frontend can render replay the
    same way it renders a live trace, with one addition: for tool_call steps,
    `replay_matches_original` records whether re-executing that mock tool
    call reproduced the originally recorded result."""

    step: int
    type: str
    data: Dict[str, Any]
    replay_matches_original: Optional[bool] = None


class ToolCallReplayComparison(BaseModel):
    """Side-by-side original vs. replayed result for one tool call, so a
    person can see exactly what (if anything) diverged."""

    step: int
    tool_name: str
    params: Dict[str, Any]
    original_success: bool
    original_data: Dict[str, Any]
    original_error: str
    replayed_success: bool
    replayed_data: Dict[str, Any]
    replayed_error: str
    match: bool


class TraceReplayResponse(BaseModel):
    trace_id: str
    test_run_id: str
    scenario_id: str
    agent_id: str
    agent_version: str
    original_final_status: str
    deterministic: bool
    total_steps: int
    timeline: List[ReplayTimelineStep]
    tool_call_comparisons: List[ToolCallReplayComparison]
    failures: List[FailureRead] = []
    replayed_at: datetime
    note: str = (
        "Replay re-executes only mocked tools against a freshly-seeded "
        "sandbox. No real destructive action is ever performed."
    )
