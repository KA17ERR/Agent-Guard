"""
Regression Tracker API:

    GET /api/agents/{agent_id}/regression

Wraps `regression_service.compare_runs` (Section 13) — compares two
TestRuns of the same agent (selected either by version or by explicit
run id, one selector per side) and returns the full diff: dimension score
changes, newly failing/passing scenarios, and an automatic regression
verdict.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.regression import (
    DimensionChange,
    RegressionReport,
    RegressionRunSummary,
    ScenarioRegressionDetail,
)
from app.services import regression_service
from app.services.regression_service import RegressionResult

router = APIRouter(prefix="/api/agents", tags=["regression"])

_DIMENSIONS = ("safety", "tool_reliability", "goal_adherence", "truthfulness", "task_success")
_ID_MAX_LEN = 64
_VERSION_MAX_LEN = 50


def _run_summary(snapshot) -> RegressionRunSummary:
    run = snapshot.run
    return RegressionRunSummary(
        run_id=run.id,
        version=run.version,
        reliability_score=snapshot.score.overall_score,
        total_tests=run.total_tests,
        passed_tests=run.passed_tests,
        failed_tests=run.failed_tests,
        completed_at=run.completed_at,
    )


def _dimension_change(snapshot_a, snapshot_b, dimension: str) -> DimensionChange:
    value_a = getattr(snapshot_a.score.category_scores, dimension)
    value_b = getattr(snapshot_b.score.category_scores, dimension)
    return DimensionChange(version_a=value_a, version_b=value_b, change=value_b - value_a)


def _to_report(result: RegressionResult) -> RegressionReport:
    overall = DimensionChange(
        version_a=result.snapshot_a.score.overall_score,
        version_b=result.snapshot_b.score.overall_score,
        change=result.snapshot_b.score.overall_score - result.snapshot_a.score.overall_score,
    )
    dimension_changes = {
        dim: _dimension_change(result.snapshot_a, result.snapshot_b, dim) for dim in _DIMENSIONS
    }

    return RegressionReport(
        agent_id=result.agent.id,
        agent_name=result.agent.name,
        run_a=_run_summary(result.snapshot_a),
        run_b=_run_summary(result.snapshot_b),
        overall=overall,
        **dimension_changes,
        newly_failing_scenarios=result.newly_failing,
        newly_passing_scenarios=result.newly_passing,
        scenario_regressions=[
            ScenarioRegressionDetail(**d) for d in result.scenario_regressions
        ],
        is_regression=result.is_regression,
        regression_reasons=result.regression_reasons,
    )


@router.get("/{agent_id}/regression", response_model=RegressionReport)
def get_regression_report(
    agent_id: str = Path(max_length=_ID_MAX_LEN),
    version_a: Optional[str] = Query(default=None, max_length=_VERSION_MAX_LEN),
    version_b: Optional[str] = Query(default=None, max_length=_VERSION_MAX_LEN),
    run_id_a: Optional[str] = Query(default=None, max_length=_ID_MAX_LEN),
    run_id_b: Optional[str] = Query(default=None, max_length=_ID_MAX_LEN),
    db: Session = Depends(get_db),
):
    try:
        result = regression_service.compare_runs(
            db,
            agent_id,
            version_a=version_a,
            version_b=version_b,
            run_id_a=run_id_a,
            run_id_b=run_id_b,
        )
    except regression_service.AgentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except regression_service.RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (regression_service.AmbiguousRunSelectionError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _to_report(result)
