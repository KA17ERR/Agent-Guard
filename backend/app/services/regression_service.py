"""
Regression Tracker (Section 13).

Compares two completed TestRuns of the same Agent — typically one from an
earlier version and one from a newer version — and reports:

    - the change in the overall reliability score and each of the five
      scoring dimensions from Section 10 (task_success, safety,
      tool_reliability, goal_adherence, truthfulness)
    - which Scenarios (matched by scenario_id — the same Scenario set is
      normally re-run across an agent's versions) newly started failing,
      newly started passing, or got a more severe failure even while still
      nominally passing
    - an automatic regression verdict with human-readable reasons

Scores are recomputed from each run's persisted Traces/Failures using the
same deterministic `compute_reliability` formula as the Reliability Report
(Section 10) rather than trusting a cached number, so this stays consistent
with the report even if the run's stored `reliability_score` is stale.

A run to compare is resolved either by an explicit TestRun id, or by the
most recently completed TestRun for a given `version` string on this agent
— whichever the caller supplies.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.agent import Agent
from app.models.test_run import TestRun
from app.models.trace import Trace
from app.schemas.failure import SEVERITY_RANK
from app.services.scoring_service import (
    CategoryScores,
    ReliabilityScoreResult,
    TraceScoreInput,
    compute_reliability,
)

# Dimensions whose regression we always surface as a top-level reason,
# regardless of magnitude — these are the ones the spec calls out by name.
_TRACKED_DIMENSIONS = (
    "task_success",
    "safety",
    "tool_reliability",
    "goal_adherence",
    "truthfulness",
)

# A tiny epsilon avoids flagging float noise (e.g. 79.999999...) as a
# "regression" when nothing meaningfully changed.
_EPSILON = 1e-6


class RegressionError(Exception):
    """Base class for regression-tracker errors."""


class AgentNotFoundError(RegressionError):
    pass


class RunNotFoundError(RegressionError):
    pass


class AmbiguousRunSelectionError(RegressionError):
    pass


@dataclass
class _RunSnapshot:
    run: TestRun
    score: ReliabilityScoreResult
    # scenario_id -> Trace, for the scenarios present in this run
    traces_by_scenario: Dict[str, Trace] = field(default_factory=dict)


@dataclass
class RegressionResult:
    agent: Agent
    snapshot_a: _RunSnapshot
    snapshot_b: _RunSnapshot
    newly_failing: List[str]
    newly_passing: List[str]
    scenario_regressions: List[dict]
    is_regression: bool
    regression_reasons: List[str]


def _get_agent(db: Session, agent_id: str) -> Agent:
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if agent is None:
        raise AgentNotFoundError(f"Agent '{agent_id}' not found")
    return agent


def _load_run_with_traces(db: Session, run_id: str, agent_id: str) -> TestRun:
    run = (
        db.query(TestRun)
        .options(joinedload(TestRun.traces).joinedload(Trace.failures))
        .filter(TestRun.id == run_id, TestRun.agent_id == agent_id)
        .first()
    )
    if run is None:
        raise RunNotFoundError(f"Test run '{run_id}' not found for agent '{agent_id}'")
    return run


def _load_latest_run_for_version(db: Session, agent_id: str, version: str) -> TestRun:
    run = (
        db.query(TestRun)
        .options(joinedload(TestRun.traces).joinedload(Trace.failures))
        .filter(
            TestRun.agent_id == agent_id,
            TestRun.version == version,
            TestRun.status == "completed",
        )
        .order_by(TestRun.completed_at.desc())
        .first()
    )
    if run is None:
        raise RunNotFoundError(
            f"No completed test run found for agent '{agent_id}' version '{version}'"
        )
    return run


def _resolve_run(
    db: Session, agent_id: str, version: Optional[str], run_id: Optional[str]
) -> TestRun:
    if run_id and version:
        raise AmbiguousRunSelectionError(
            "Provide either a run id or a version, not both, for the same run"
        )
    if run_id:
        return _load_run_with_traces(db, run_id, agent_id)
    if version:
        return _load_latest_run_for_version(db, agent_id, version)
    raise ValueError("Either a version or a run id must be provided")


def _snapshot(run: TestRun) -> _RunSnapshot:
    trace_inputs = [
        TraceScoreInput(final_status=t.final_status, failures=list(t.failures))
        for t in run.traces
    ]
    score = compute_reliability(trace_inputs)
    traces_by_scenario = {t.scenario_id: t for t in run.traces}
    return _RunSnapshot(run=run, score=score, traces_by_scenario=traces_by_scenario)


def _worst_severity(trace: Trace) -> str:
    if not trace.failures:
        return "none"
    worst = max(trace.failures, key=lambda f: SEVERITY_RANK.get(f.severity, 0))
    return worst.severity


def _worst_rank(trace: Trace) -> int:
    if not trace.failures:
        return 0
    return max(SEVERITY_RANK.get(f.severity, 0) for f in trace.failures)


def _dimension_value(scores: CategoryScores, dimension: str) -> float:
    return getattr(scores, dimension)


def compare_runs(
    db: Session,
    agent_id: str,
    version_a: Optional[str] = None,
    version_b: Optional[str] = None,
    run_id_a: Optional[str] = None,
    run_id_b: Optional[str] = None,
) -> RegressionResult:
    """The single entry point: resolve the two runs to compare, score each
    from its persisted traces/failures, and diff them scenario-by-scenario
    and dimension-by-dimension."""
    agent = _get_agent(db, agent_id)

    run_a = _resolve_run(db, agent_id, version_a, run_id_a)
    run_b = _resolve_run(db, agent_id, version_b, run_id_b)

    snap_a = _snapshot(run_a)
    snap_b = _snapshot(run_b)

    common_scenario_ids = set(snap_a.traces_by_scenario) & set(snap_b.traces_by_scenario)

    newly_failing: List[str] = []
    newly_passing: List[str] = []
    scenario_regressions: List[dict] = []

    for scenario_id in sorted(common_scenario_ids):
        trace_a = snap_a.traces_by_scenario[scenario_id]
        trace_b = snap_b.traces_by_scenario[scenario_id]

        was_passing = trace_a.final_status == "passed"
        now_passing = trace_b.final_status == "passed"

        if was_passing and not now_passing:
            newly_failing.append(scenario_id)
        elif not was_passing and now_passing:
            newly_passing.append(scenario_id)

        rank_a = _worst_rank(trace_a)
        rank_b = _worst_rank(trace_b)

        # A regression at the scenario level: it got a strictly more severe
        # failure than before, whether or not its pass/fail verdict flipped
        # (e.g. still "failed" overall but now has a critical failure where
        # it previously only had a low-severity one).
        if rank_b > rank_a:
            reason = (
                f"scenario now fails with '{_worst_severity(trace_b)}' severity, up from "
                f"'{_worst_severity(trace_a)}'"
                if was_passing and not now_passing
                else (
                    f"failure severity increased from '{_worst_severity(trace_a)}' to "
                    f"'{_worst_severity(trace_b)}'"
                )
            )
            scenario_regressions.append(
                {
                    "scenario_id": scenario_id,
                    "previous_status": trace_a.final_status,
                    "new_status": trace_b.final_status,
                    "previous_worst_severity": _worst_severity(trace_a),
                    "new_worst_severity": _worst_severity(trace_b),
                    "reason": reason,
                }
            )

    regression_reasons: List[str] = []

    overall_change = snap_b.score.overall_score - snap_a.score.overall_score
    if overall_change < -_EPSILON:
        regression_reasons.append(
            f"overall reliability score dropped by {abs(overall_change):.2f} points"
        )

    for dimension in _TRACKED_DIMENSIONS:
        change = _dimension_value(snap_b.score.category_scores, dimension) - _dimension_value(
            snap_a.score.category_scores, dimension
        )
        if change < -_EPSILON:
            label = dimension.replace("_", " ")
            regression_reasons.append(f"{label} score dropped by {abs(change):.2f} points")

    if newly_failing:
        regression_reasons.append(
            f"{len(newly_failing)} previously passing scenario(s) now fail: "
            f"{', '.join(newly_failing)}"
        )

    if scenario_regressions:
        regression_reasons.append(
            f"{len(scenario_regressions)} scenario(s) show a more severe failure than before"
        )

    is_regression = len(regression_reasons) > 0

    return RegressionResult(
        agent=agent,
        snapshot_a=snap_a,
        snapshot_b=snap_b,
        newly_failing=newly_failing,
        newly_passing=newly_passing,
        scenario_regressions=scenario_regressions,
        is_regression=is_regression,
        regression_reasons=regression_reasons,
    )
