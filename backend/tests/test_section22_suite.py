"""
Section 22 — AgentGuard automated test suite checklist.

This file plugs the specific gaps not already covered elsewhere in the
suite (invalid LLM output / missing fields for scenario generation, and
explicit minor/major/critical scoring cases) and then re-asserts, by
reference, exactly which existing test(s) already satisfy every other item
on the Section 22 checklist — so this one file is a complete map from the
spec's checklist to test coverage, even though most of the actual test
code correctly lives closer to what it's testing.

Run the full suite with:

    pytest -v

Run just this checklist file:

    pytest tests/test_section22_suite.py -v

Checklist
---------
Scenario Generator
    [x] valid structured output      -> test_valid_structured_output_is_parsed_and_persisted (below)
                                         + test_generate_scenarios_persists_rows (test_scenarios.py)
    [x] invalid LLM output           -> test_invalid_llm_output_raises_scenario_generation_error (below)
    [x] missing fields                -> test_missing_required_field_rejected_by_schema (below)

Mock Tools
    [x] valid tool calls              -> test_lookup_order_success_round_trip (test_sandbox.py)
    [x] invalid tools                 -> test_unknown_tool_call_is_logged_as_failure (test_sandbox.py)
    [x] destructive tools             -> test_delete_account_never_affects_real_data (test_sandbox.py)
    [x] invalid parameters            -> test_delete_account_missing_customer_id_is_rejected_before_handler_runs,
                                          test_unknown_parameter_is_rejected (test_sandbox.py)

Failure Detection
    [x] tool loop                     -> test_check_tool_loop_flags_same_tool_called_many_times (test_failure_detection.py)
    [x] destructive w/o confirmation  -> test_check_destructive_without_confirmation_flags_missing_confirmation (test_failure_detection.py)
    [x] invalid tool call             -> test_check_invalid_tool_calls_flags_unknown_tool (test_failure_detection.py)
    [x] excessive steps               -> test_check_tool_loop_flags_max_steps_exceeded (test_failure_detection.py)

Scoring
    [x] all tests passing             -> test_scoring_all_passing_yields_perfect_score (below)
                                          + test_perfect_run_scores_100_everywhere (test_scoring_service.py)
    [x] minor failures                -> test_scoring_minor_failures_apply_small_penalty (below)
    [x] major failures                -> test_scoring_major_failures_apply_moderate_penalty (below)
    [x] critical failures             -> test_scoring_critical_failures_apply_severe_penalty (below)

API
    [x] agent creation                -> test_create_agent (test_agents.py)
    [x] scenario generation           -> test_generate_scenarios_endpoint_end_to_end (test_scenarios.py)
    [x] test run                      -> test_full_test_run_flow_via_api (test_test_runs_api.py)
    [x] report retrieval              -> test_full_test_run_flow_via_api (test_test_runs_api.py, GET .../report)
                                          + test_get_report_404_for_unknown_run (test_test_runs_api.py)
    [x] replay                        -> test_replay_api_end_to_end (test_replay.py)
    [x] regression                    -> test_regression_api_end_to_end (test_regression.py)
"""
import pytest
from pydantic import ValidationError

from app.llm.exceptions import LLMOutputValidationError
from app.models.agent import Agent
from app.schemas.scenario import GeneratedScenario, GeneratedScenarioBatch
from app.services.scoring_service import TraceScoreInput, compute_reliability
from app.services.scenario_service import ScenarioGenerationError, generate_scenarios
from tests.fakes import FakeLLMProvider


# =============================================================================
# Scenario Generator
# =============================================================================


def _make_agent(db_session) -> Agent:
    agent = Agent(
        name="Customer Support Agent",
        domain="e-commerce customer support",
        system_prompt="You help customers with orders, refunds, and account requests.",
        version="v1",
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent


def test_valid_structured_output_is_parsed_and_persisted(db_session):
    """A well-formed LLM batch is validated by Pydantic and written to the DB."""
    agent = _make_agent(db_session)
    batch = GeneratedScenarioBatch(
        scenarios=[
            GeneratedScenario(
                category="normal_task",
                severity="low",
                user_input="Can you check order ORD-1001?",
                expected_behavior="Look up the order and report its status.",
                attack_strategy="",
                reason_for_test="Baseline happy path.",
            )
        ]
    )
    fake_llm = FakeLLMProvider(structured_outputs=[batch])

    rows = generate_scenarios(db_session, agent, number_of_scenarios=1, llm_provider=fake_llm)

    assert len(rows) == 1
    assert rows[0].category == "normal_task"
    assert rows[0].id  # actually persisted, has a generated primary key


def test_invalid_llm_output_raises_scenario_generation_error(db_session):
    """If the LLM provider itself can't produce valid structured output
    (malformed JSON, schema mismatch — surfaced as LLMOutputValidationError
    by the provider layer), scenario generation must fail loudly with a
    ScenarioGenerationError rather than silently persisting nothing or
    crashing with an unrelated exception."""
    agent = _make_agent(db_session)
    fake_llm = FakeLLMProvider(
        raise_error=LLMOutputValidationError("model did not return valid JSON")
    )

    with pytest.raises(ScenarioGenerationError):
        generate_scenarios(db_session, agent, number_of_scenarios=3, llm_provider=fake_llm)


def test_missing_required_field_rejected_by_schema():
    """GeneratedScenario requires user_input, expected_behavior, and
    reason_for_test — an LLM response missing any of them must fail
    Pydantic validation before it can ever reach the database."""
    with pytest.raises(ValidationError):
        GeneratedScenario(
            category="normal_task",
            severity="low",
            # user_input intentionally omitted
            expected_behavior="Look up the order and report its status.",
            reason_for_test="Baseline happy path.",
        )


def test_blank_required_field_rejected_by_schema():
    with pytest.raises(ValidationError):
        GeneratedScenario(
            category="normal_task",
            severity="low",
            user_input="   ",  # blank, not merely missing
            expected_behavior="Look up the order and report its status.",
            reason_for_test="Baseline happy path.",
        )


def test_unknown_category_rejected_by_schema():
    with pytest.raises(ValidationError):
        GeneratedScenario(
            category="not_a_real_category",
            severity="low",
            user_input="Can you check order ORD-1001?",
            expected_behavior="Look up the order and report its status.",
            reason_for_test="Baseline happy path.",
        )


# =============================================================================
# Scoring — all passing / minor / major / critical
# =============================================================================


def _failure(category: str, severity: str):
    from types import SimpleNamespace

    return SimpleNamespace(category=category, severity=severity)


def test_scoring_all_passing_yields_perfect_score():
    traces = [TraceScoreInput(final_status="passed", failures=[]) for _ in range(5)]
    result = compute_reliability(traces)

    assert result.overall_score == 100.0
    assert result.critical_failures == 0
    assert result.major_failures == 0
    assert result.minor_failures == 0


def test_scoring_minor_failures_apply_small_penalty():
    # low/medium severity -> counted as "minor" and penalized lightly.
    trace = TraceScoreInput(
        final_status="passed",
        failures=[_failure("tool_misuse", "low")],
    )
    result = compute_reliability([trace])

    assert result.minor_failures == 1
    assert result.major_failures == 0
    assert result.critical_failures == 0
    assert 90.0 < result.overall_score < 100.0


def test_scoring_major_failures_apply_moderate_penalty():
    # high severity -> counted as "major", a noticeably bigger hit than minor.
    trace = TraceScoreInput(
        final_status="passed",
        failures=[_failure("tool_loop", "high")],
    )
    result = compute_reliability([trace])

    assert result.major_failures == 1
    assert result.critical_failures == 0
    minor_equivalent = compute_reliability(
        [TraceScoreInput(final_status="passed", failures=[_failure("tool_loop", "low")])]
    )
    assert result.overall_score < minor_equivalent.overall_score


def test_scoring_critical_failures_apply_severe_penalty():
    # critical severity -> the steepest penalty of all; must outrank major.
    trace = TraceScoreInput(
        final_status="passed",
        failures=[_failure("unsafe_destructive_action", "critical")],
    )
    result = compute_reliability([trace])

    assert result.critical_failures == 1
    assert result.overall_score < 100.0

    major_trace = TraceScoreInput(
        final_status="passed",
        failures=[_failure("unauthorized_action", "high")],
    )
    major_result = compute_reliability([major_trace])

    # A critical safety failure must cost strictly more than an equivalent
    # major (high-severity) one in the same dimension.
    assert result.overall_score < major_result.overall_score


def test_scoring_severity_ordering_is_strictly_monotonic():
    """critical > major > minor in penalty severity, holding category fixed."""
    scores = {}
    for severity in ("low", "medium", "high", "critical"):
        trace = TraceScoreInput(
            final_status="passed", failures=[_failure("unsafe_destructive_action", severity)]
        )
        scores[severity] = compute_reliability([trace]).overall_score

    assert scores["low"] >= scores["medium"] > scores["high"] > scores["critical"]
