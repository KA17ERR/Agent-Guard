"""
Test Runner (Section 11) — orchestrates the full AgentGuard pipeline for a
batch of scenarios against one agent:

    Load Agent -> Load Scenarios -> Execute (Section 8, fresh sandbox per
    scenario) -> Capture Trace -> Detect Failures (Section 9) -> Store
    Failures -> Score (Section 10) -> Store TestRun -> Return results.

The one hard guarantee this module provides: a single scenario blowing up
(executor crash, LLM outage, unexpected exception anywhere in its own
pipeline) is caught and turned into an "error" trace for that scenario
only — it never aborts the rest of the batch or leaves the TestRun stuck
in "running".
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Tuple

from sqlalchemy.orm import Session

from app.agent.executor import AgentExecutor
from app.core.database import commit_or_rollback
from app.llm.base import LLMProvider
from app.models.agent import Agent
from app.models.failure import Failure
from app.models.scenario import Scenario
from app.models.test_run import TestRun
from app.models.trace import Trace
from app.sandbox.registry import ToolExecutionController
from app.sandbox.state import SandboxState
from app.schemas.execution import ExecutionResult, TraceEvent
from app.schemas.failure import FailureDetectionResult
from app.services import agent_service
from app.services.failure_detection_service import detect_failures
from app.services.scoring_service import ReliabilityScoreResult, TraceScoreInput, compute_reliability

logger = logging.getLogger("agentguard.test_runner")

# Any failure at this severity or above always fails the trace outright,
# even if the executor itself reported status="completed".
_HARD_FAIL_SEVERITIES = {"critical"}


class TestRunnerError(Exception):
    """Base class for test-runner-level errors (as opposed to a single
    scenario's own execution error, which is captured in its trace instead
    of raised)."""


class AgentNotFoundError(TestRunnerError):
    pass


class ScenarioNotFoundError(TestRunnerError):
    pass


@dataclass
class _ScenarioOutcome:
    scenario: Scenario
    execution_result: ExecutionResult
    failures: List[FailureDetectionResult]
    final_status: str


def _load_agent(db: Session, agent_id: str) -> Agent:
    agent = agent_service.get_agent(db, agent_id)
    if agent is None:
        raise AgentNotFoundError(f"Agent '{agent_id}' not found")
    return agent


def _load_scenarios(db: Session, agent_id: str, scenario_ids: List[str]) -> List[Scenario]:
    scenarios = (
        db.query(Scenario)
        .filter(Scenario.agent_id == agent_id, Scenario.id.in_(scenario_ids))
        .all()
    )
    found_ids = {s.id for s in scenarios}
    missing = [sid for sid in scenario_ids if sid not in found_ids]
    if missing:
        raise ScenarioNotFoundError(
            f"Scenario(s) not found for agent '{agent_id}': {missing}"
        )
    # Preserve the order the caller requested rather than the DB's order.
    by_id = {s.id: s for s in scenarios}
    return [by_id[sid] for sid in scenario_ids]


def _execute_scenario(
    agent: Agent, scenario: Scenario, llm_provider: LLMProvider
) -> ExecutionResult:
    """Runs one scenario in a brand-new, independent sandbox. Never raises —
    any exception becomes an ExecutionResult with status='error' so the
    caller can keep going."""
    try:
        controller = ToolExecutionController(SandboxState.fresh())
        executor = AgentExecutor(llm_provider, agent.system_prompt, tool_controller=controller)
        return executor.run(scenario.user_input)
    except Exception as exc:  # noqa: BLE001 — deliberately broad: one bad
        # scenario must never take down the whole test run (Section 11).
        logger.exception("Scenario %s raised during execution", scenario.id)
        return ExecutionResult(
            final_response="",
            tool_calls=[],
            steps=0,
            trace=[TraceEvent(step=0, type="error", data={"error": str(exc)})],
            status="error",
        )


def _detect_scenario_failures(
    agent: Agent,
    scenario: Scenario,
    execution_result: ExecutionResult,
    llm_provider: LLMProvider,
) -> List[FailureDetectionResult]:
    """Wraps Section 9's detector so a judge-side exception degrades to "no
    additional failures found" instead of crashing the run. (llm_based_detect
    already catches LLMError internally; this is a second safety net for
    anything else, e.g. a bug in a rule check.)"""
    try:
        return detect_failures(agent, scenario, execution_result, llm_provider)
    except Exception:  # noqa: BLE001
        logger.exception("Failure detection raised for scenario %s", scenario.id)
        return []


def _derive_final_status(execution_result: ExecutionResult, failures: List[FailureDetectionResult]) -> str:
    """Trace.final_status ('passed' | 'failed' | 'error') combines the raw
    executor outcome with what the failure detectors found — a trace that
    "completed" can still be a failure (e.g. it hallucinated, or performed
    an unconfirmed destructive action)."""
    if execution_result.status == "error":
        return "error"
    if any(f.severity in _HARD_FAIL_SEVERITIES for f in failures):
        return "failed"
    if execution_result.status == "max_steps_exceeded":
        return "failed"
    if failures:
        return "failed"
    return "passed"


def run_test_run(
    db: Session,
    agent_id: str,
    scenario_ids: List[str],
    llm_provider: LLMProvider,
) -> Tuple[TestRun, ReliabilityScoreResult]:
    """POST /api/test-runs entry point. Returns the persisted TestRun row
    (with its Traces/Failures already committed) plus the full reliability
    score breakdown for that same data."""
    agent = _load_agent(db, agent_id)
    scenarios = _load_scenarios(db, agent_id, scenario_ids)

    run = TestRun(
        agent_id=agent.id,
        version=agent.version,
        status="running",
        total_tests=len(scenarios),
    )
    db.add(run)
    db.flush()  # assigns run.id without committing yet

    outcomes: List[_ScenarioOutcome] = []

    for scenario in scenarios:
        execution_result = _execute_scenario(agent, scenario, llm_provider)
        failures = _detect_scenario_failures(agent, scenario, execution_result, llm_provider)
        final_status = _derive_final_status(execution_result, failures)

        trace = Trace(
            test_run_id=run.id,
            scenario_id=scenario.id,
            events=[e.model_dump() for e in execution_result.trace],
            agent_response=execution_result.final_response,
            tool_calls=[tc.model_dump() for tc in execution_result.tool_calls],
            final_status=final_status,
        )
        db.add(trace)
        db.flush()  # assigns trace.id so failures can reference it

        for f in failures:
            db.add(
                Failure(
                    trace_id=trace.id,
                    category=f.category,
                    severity=f.severity,
                    explanation=f.explanation,
                    recommendation=f.recommendation,
                    confidence=f.confidence,
                )
            )

        outcomes.append(
            _ScenarioOutcome(
                scenario=scenario,
                execution_result=execution_result,
                failures=failures,
                final_status=final_status,
            )
        )

    score_result = compute_reliability(
        [TraceScoreInput(final_status=o.final_status, failures=o.failures) for o in outcomes]
    )

    passed_tests = sum(1 for o in outcomes if o.final_status == "passed")
    run.status = "completed"
    run.passed_tests = passed_tests
    run.failed_tests = len(outcomes) - passed_tests
    run.reliability_score = score_result.overall_score
    run.completed_at = datetime.now(timezone.utc)

    commit_or_rollback(db, context=f"completing test run for agent '{agent_id}'")
    db.refresh(run)

    return run, score_result
