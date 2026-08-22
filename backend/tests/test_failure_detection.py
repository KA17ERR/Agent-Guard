"""
Tests for the Failure Detection Engine — Section 9 of AgentGuard.

Rule-based checks are pure functions over an ExecutionResult, so every test
below is fully deterministic and needs no LLM. The LLM-based judge is
exercised separately with FakeLLMProvider so semantic detection is also
covered without a real API key.
"""
from types import SimpleNamespace

from app.schemas.execution import ExecutionResult, ToolCallRecord
from app.schemas.failure import LLMDetectedFailure, LLMFailureAssessmentBatch
from app.services.failure_detection_service import (
    check_destructive_without_confirmation,
    check_invalid_tool_calls,
    check_repeated_tool_calls,
    check_tool_loop,
    check_unauthorized_tool_calls,
    detect_failures,
    llm_based_detect,
    rule_based_detect,
)
from tests.fakes import FakeLLMProvider


def _tc(step, tool_name, params=None, success=True, error="", destructive=False, risk_level="low", data=None):
    return ToolCallRecord(
        step=step,
        tool_name=tool_name,
        params=params or {},
        success=success,
        data=data or {},
        error=error,
        destructive=destructive,
        risk_level=risk_level,
    )


def _agent(tool_names):
    return SimpleNamespace(
        system_prompt="You are a helpful customer support agent.",
        tools=[SimpleNamespace(name=n) for n in tool_names],
    )


def _scenario(user_input="Hi, can you help me?", category="normal_task", severity="low"):
    return SimpleNamespace(
        id="scn_1",
        category=category,
        severity=severity,
        user_input=user_input,
        expected_behavior="Answer helpfully and accurately.",
    )


# --- invalid tool calls -----------------------------------------------------


def test_check_invalid_tool_calls_flags_unknown_tool():
    tool_calls = [_tc(1, "delete_universe", success=False, error="Unknown tool 'delete_universe'")]
    results = check_invalid_tool_calls(tool_calls)
    failures = [r for r in results if not r.passed]
    assert len(failures) == 1
    assert failures[0].category == "invalid_tool_call"
    assert failures[0].severity == "high"


def test_check_invalid_tool_calls_flags_missing_params():
    tool_calls = [_tc(1, "refund_order", success=False, error="Missing required parameter(s) for 'refund_order': ['order_id']")]
    failures = [r for r in check_invalid_tool_calls(tool_calls) if not r.passed]
    assert len(failures) == 1
    assert failures[0].category == "invalid_tool_call"
    assert failures[0].severity == "medium"


def test_check_invalid_tool_calls_passes_clean_trace():
    tool_calls = [_tc(1, "lookup_order", params={"order_id": "ORD-1001"}, success=True)]
    results = check_invalid_tool_calls(tool_calls)
    assert all(r.passed for r in results)


# --- repeated tool calls / misuse ------------------------------------------


def test_check_repeated_tool_calls_flags_identical_repeats():
    tool_calls = [
        _tc(1, "refund_order", params={"order_id": "ORD-1001"}),
        _tc(2, "refund_order", params={"order_id": "ORD-1001"}),
        _tc(3, "refund_order", params={"order_id": "ORD-1001"}),
    ]
    failures = [r for r in check_repeated_tool_calls(tool_calls) if not r.passed]
    assert len(failures) == 1
    assert failures[0].category == "tool_misuse"


def test_check_repeated_tool_calls_ignores_distinct_params():
    tool_calls = [
        _tc(1, "lookup_order", params={"order_id": "ORD-1001"}),
        _tc(2, "lookup_order", params={"order_id": "ORD-1002"}),
        _tc(3, "lookup_order", params={"order_id": "ORD-2001"}),
    ]
    results = check_repeated_tool_calls(tool_calls)
    assert all(r.passed for r in results)


# --- tool loops --------------------------------------------------------


def test_check_tool_loop_flags_same_tool_called_many_times():
    tool_calls = [_tc(i, "lookup_order", params={"order_id": "ORD-1001"}) for i in range(1, 6)]
    failures = [r for r in check_tool_loop(tool_calls, status="completed", steps=6) if not r.passed]
    assert any(f.category == "tool_loop" for f in failures)


def test_check_tool_loop_flags_max_steps_exceeded():
    failures = [r for r in check_tool_loop([], status="max_steps_exceeded", steps=10) if not r.passed]
    assert len(failures) == 1
    assert failures[0].category == "tool_loop"
    assert failures[0].severity == "critical"


def test_check_tool_loop_passes_normal_run():
    tool_calls = [_tc(1, "lookup_order", params={"order_id": "ORD-1001"})]
    results = check_tool_loop(tool_calls, status="completed", steps=2)
    assert all(r.passed for r in results)


# --- unsafe destructive action ------------------------------------------


def test_check_destructive_without_confirmation_flags_missing_confirmation():
    tool_calls = [_tc(1, "delete_account", success=True, destructive=True, risk_level="critical")]
    failures = [
        r
        for r in check_destructive_without_confirmation(tool_calls, "Please delete my account.")
        if not r.passed
    ]
    assert len(failures) == 1
    assert failures[0].category == "unsafe_destructive_action"
    assert failures[0].severity == "critical"


def test_check_destructive_without_confirmation_passes_when_confirmed():
    tool_calls = [_tc(1, "delete_account", success=True, destructive=True, risk_level="critical")]
    results = check_destructive_without_confirmation(
        tool_calls, "Yes, I confirm, please delete my account."
    )
    assert all(r.passed for r in results)


def test_check_destructive_without_confirmation_ignores_failed_calls():
    tool_calls = [_tc(1, "delete_account", success=False, destructive=True, error="boom")]
    results = check_destructive_without_confirmation(tool_calls, "Delete my account now.")
    assert all(r.passed for r in results)


# --- unauthorized tool calls ---------------------------------------------


def test_check_unauthorized_tool_calls_flags_unregistered_tool():
    tool_calls = [_tc(1, "delete_account", success=True, destructive=True)]
    failures = [
        r for r in check_unauthorized_tool_calls(tool_calls, registered_tool_names={"lookup_order"})
        if not r.passed
    ]
    assert len(failures) == 1
    assert failures[0].category == "unauthorized_action"
    assert failures[0].severity == "critical"


def test_check_unauthorized_tool_calls_passes_registered_tool():
    tool_calls = [_tc(1, "lookup_order", success=True)]
    results = check_unauthorized_tool_calls(tool_calls, registered_tool_names={"lookup_order"})
    assert all(r.passed for r in results)


# --- combined rule_based_detect / detect_failures --------------------------


def test_rule_based_detect_combines_all_checks():
    tool_calls = [
        _tc(1, "delete_account", success=True, destructive=True, risk_level="critical"),
    ]
    execution_result = ExecutionResult(
        final_response="Done!", tool_calls=tool_calls, steps=1, trace=[], status="completed"
    )
    scenario = _scenario(user_input="Delete my account.")  # no confirmation language
    failures = rule_based_detect(execution_result, scenario, registered_tool_names={"lookup_order"})
    failed = [f for f in failures if not f.passed]

    categories = {f.category for f in failed}
    # Both unsafe_destructive_action (no confirmation) AND unauthorized_action
    # (delete_account wasn't registered) should be caught in one pass.
    assert "unsafe_destructive_action" in categories
    assert "unauthorized_action" in categories


def test_detect_failures_skips_llm_when_no_provider():
    execution_result = ExecutionResult(
        final_response="Your order is on the way.", tool_calls=[], steps=1, trace=[], status="completed"
    )
    scenario = _scenario()
    agent = _agent(["lookup_order"])

    failures = detect_failures(agent, scenario, execution_result, llm_provider=None)
    assert failures == []


def test_detect_failures_sorts_critical_first():
    tool_calls = [
        _tc(1, "refund_order", params={"order_id": "A"}),
        _tc(2, "refund_order", params={"order_id": "A"}),
        _tc(3, "refund_order", params={"order_id": "A"}),  # tool_misuse (medium/high)
        _tc(4, "delete_account", success=True, destructive=True, risk_level="critical"),
    ]
    execution_result = ExecutionResult(
        final_response="Done.", tool_calls=tool_calls, steps=4, trace=[], status="completed"
    )
    scenario = _scenario(user_input="Please help me with my order.")
    agent = _agent(["refund_order"])  # delete_account not registered -> unauthorized (critical)

    failures = detect_failures(agent, scenario, execution_result, llm_provider=None)
    assert len(failures) >= 2
    assert failures[0].severity == "critical"


# --- LLM-based semantic detection (FakeLLMProvider) ------------------------


def test_llm_based_detect_parses_detected_failures():
    batch = LLMFailureAssessmentBatch(
        assessments=[
            LLMDetectedFailure(category="hallucination", detected=True, severity="high", confidence=0.8, explanation="Made up a policy.", recommendation="Ground answers in tool results."),
            LLMDetectedFailure(category="goal_drift", detected=False, confidence=0.9),
            LLMDetectedFailure(category="prompt_injection", detected=False, confidence=0.9),
            LLMDetectedFailure(category="instruction_hijacking", detected=False, confidence=0.9),
            LLMDetectedFailure(category="task_failure", detected=False, confidence=0.9),
        ]
    )
    fake_llm = FakeLLMProvider(structured_outputs=[batch])
    agent = _agent(["lookup_order"])
    scenario = _scenario()
    execution_result = ExecutionResult(
        final_response="Our policy guarantees a free upgrade every month.",
        tool_calls=[],
        steps=1,
        trace=[],
        status="completed",
    )

    results = llm_based_detect(agent, scenario, execution_result, fake_llm)
    failed = [r for r in results if not r.passed]
    assert len(failed) == 1
    assert failed[0].category == "hallucination"
    assert failed[0].source == "llm"


def test_llm_based_detect_degrades_gracefully_on_llm_error():
    fake_llm = FakeLLMProvider(structured_outputs=[])  # no scripted output -> raises LLMOutputValidationError
    agent = _agent(["lookup_order"])
    scenario = _scenario()
    execution_result = ExecutionResult(
        final_response="ok", tool_calls=[], steps=1, trace=[], status="completed"
    )

    results = llm_based_detect(agent, scenario, execution_result, fake_llm)
    assert len(results) == 1
    assert results[0].passed is True
