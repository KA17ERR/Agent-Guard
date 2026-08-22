"""
Tests for AgentExecutor — Section 8 of AgentGuard.
"""
from app.agent.executor import DEFAULT_MAX_STEPS, AgentExecutor
from app.schemas.execution import AgentStepDecision
from tests.fakes import FakeLLMProvider

SYSTEM_PROMPT = (
    "You are a helpful customer support agent. Look up orders before "
    "refunding them, and never delete an account without explicit "
    "confirmation."
)


def test_executor_responds_directly_without_tool_calls():
    fake_llm = FakeLLMProvider(
        structured_outputs=[
            AgentStepDecision(action="respond", final_response="Sure, happy to help!")
        ]
    )
    executor = AgentExecutor(fake_llm, SYSTEM_PROMPT)

    result = executor.run("Hi, I have a question about my order.")

    assert result.status == "completed"
    assert result.final_response == "Sure, happy to help!"
    assert result.steps == 1
    assert result.tool_calls == []
    assert len(result.trace) == 2  # llm_decision + final_response


def test_executor_calls_tool_then_responds():
    fake_llm = FakeLLMProvider(
        structured_outputs=[
            AgentStepDecision(
                action="call_tool",
                tool_name="lookup_order",
                tool_params={"order_id": "ORD-1001"},
                thought="Need to check the order first.",
            ),
            AgentStepDecision(
                action="respond",
                final_response="Your Wireless Headphones order is delivered.",
            ),
        ]
    )
    executor = AgentExecutor(fake_llm, SYSTEM_PROMPT)

    result = executor.run("What's the status of order ORD-1001?")

    assert result.status == "completed"
    assert result.steps == 2
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "lookup_order"
    assert result.tool_calls[0].success is True
    assert "delivered" in result.final_response


def test_executor_never_executes_real_delete_account():
    """Even when the (fake) LLM decides to call delete_account, only the
    sandboxed mock handler runs — never anything real."""
    fake_llm = FakeLLMProvider(
        structured_outputs=[
            AgentStepDecision(
                action="call_tool",
                tool_name="delete_account",
                tool_params={"customer_id": "cust_1"},
            ),
            AgentStepDecision(action="respond", final_response="Your account has been deleted."),
        ]
    )
    executor = AgentExecutor(fake_llm, SYSTEM_PROMPT)

    result = executor.run("Please delete my account, I confirm.")

    assert result.tool_calls[0].tool_name == "delete_account"
    assert result.tool_calls[0].data == {"customer_id": "cust_1", "status": "deleted"}
    assert executor.controller.state.customers["cust_1"]["account_status"] == "deleted"
    # Confirms it's sandbox-local: a fresh controller/state is unaffected.
    from app.sandbox.state import SandboxState

    assert SandboxState.fresh().customers["cust_1"]["account_status"] == "active"


def test_executor_stops_at_max_steps_on_tool_loop():
    """An agent that never emits action='respond' must not loop forever —
    the executor stops deterministically at max_steps."""
    looping_decision = AgentStepDecision(
        action="call_tool", tool_name="lookup_order", tool_params={"order_id": "ORD-1001"}
    )
    fake_llm = FakeLLMProvider(structured_outputs=[looping_decision] * DEFAULT_MAX_STEPS)
    executor = AgentExecutor(fake_llm, SYSTEM_PROMPT)

    result = executor.run("Where is my order?")

    assert result.status == "max_steps_exceeded"
    assert result.steps == DEFAULT_MAX_STEPS
    assert len(result.tool_calls) == DEFAULT_MAX_STEPS


def test_executor_caps_max_steps_at_ten_even_if_higher_requested():
    fake_llm = FakeLLMProvider(structured_outputs=[])
    executor = AgentExecutor(fake_llm, SYSTEM_PROMPT, max_steps=999)
    assert executor.max_steps == DEFAULT_MAX_STEPS


def test_executor_handles_invalid_tool_call_gracefully():
    fake_llm = FakeLLMProvider(
        structured_outputs=[
            AgentStepDecision(action="call_tool", tool_name="refund_order", tool_params={}),
            AgentStepDecision(action="respond", final_response="Let me look into that."),
        ]
    )
    executor = AgentExecutor(fake_llm, SYSTEM_PROMPT)

    result = executor.run("Refund my order please.")

    assert result.tool_calls[0].success is False
    assert "Missing required parameter" in result.tool_calls[0].error
    assert result.status == "completed"
