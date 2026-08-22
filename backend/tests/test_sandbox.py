"""
Tests for the mock tool sandbox — Section 5 of AgentGuard.

The most important test in this file is
`test_delete_account_never_affects_real_data`: it proves that even the most
destructive tool in the registry only mutates an in-memory SandboxState and
returns a SIMULATED response, never touching anything real.
"""
import pytest

from app.sandbox.registry import ToolExecutionController, TOOL_REGISTRY, get_tool_spec
from app.sandbox.exceptions import ToolNotFoundError
from app.sandbox.state import SandboxState


def test_registry_contains_all_four_demo_tools():
    assert set(TOOL_REGISTRY.keys()) == {
        "lookup_order",
        "refund_order",
        "send_email",
        "delete_account",
    }


def test_delete_account_is_flagged_destructive_and_critical():
    spec = get_tool_spec("delete_account")
    assert spec.destructive is True
    assert spec.risk_level == "critical"


def test_get_tool_spec_unknown_tool_raises():
    with pytest.raises(ToolNotFoundError):
        get_tool_spec("wire_transfer_all_funds")


def test_delete_account_never_affects_real_data():
    """The core safety guarantee of the whole sandbox."""
    state = SandboxState.fresh()
    controller = ToolExecutionController(state)

    assert state.customers["cust_1"]["account_status"] == "active"

    result = controller.execute("delete_account", {"customer_id": "cust_1"})

    assert result.success is True
    assert result.data == {"customer_id": "cust_1", "status": "deleted"}
    # Only the in-memory sandbox copy changed — there is no real backing
    # store, no network call, no filesystem write. Fetching a brand-new
    # SandboxState proves the "deletion" didn't escape this instance.
    assert state.customers["cust_1"]["account_status"] == "deleted"
    fresh_state = SandboxState.fresh()
    assert fresh_state.customers["cust_1"]["account_status"] == "active"


def test_delete_account_missing_customer_id_is_rejected_before_handler_runs():
    controller = ToolExecutionController()
    result = controller.execute("delete_account", {})
    assert result.success is False
    assert "Missing required parameter" in result.error


def test_unknown_tool_call_is_logged_as_failure():
    controller = ToolExecutionController()
    result = controller.execute("wire_transfer_all_funds", {"amount": 1000000})
    assert result.success is False
    assert "Unknown tool" in result.error
    assert len(controller.state.call_log) == 1
    assert controller.state.call_log[0].success is False


def test_unknown_parameter_is_rejected():
    controller = ToolExecutionController()
    result = controller.execute(
        "lookup_order", {"order_id": "ORD-1001", "unexpected_param": "x"}
    )
    assert result.success is False
    assert "Unknown parameter" in result.error


def test_lookup_order_success_round_trip():
    controller = ToolExecutionController()
    result = controller.execute("lookup_order", {"order_id": "ORD-1001"})
    assert result.success is True
    assert result.data["found"] is True
    assert result.data["item"] == "Wireless Headphones"


def test_every_call_is_recorded_in_order_in_the_execution_trace():
    controller = ToolExecutionController()
    controller.execute("lookup_order", {"order_id": "ORD-1001"})
    controller.execute("refund_order", {"order_id": "ORD-1001"})
    controller.execute("send_email", {"to": "alice@example.com", "body": "Refund issued."})

    log = controller.state.call_log
    assert [entry.tool_name for entry in log] == ["lookup_order", "refund_order", "send_email"]
    assert [entry.index for entry in log] == [0, 1, 2]
    assert all(entry.success for entry in log)
    assert log[1].is_destructive is True


def test_refund_more_than_order_total_is_rejected():
    controller = ToolExecutionController()
    result = controller.execute("refund_order", {"order_id": "ORD-1001", "amount": 9999})
    assert result.success is False
    assert "exceeds order total" in result.error


def test_snapshot_is_json_serializable_and_independent_copy():
    controller = ToolExecutionController()
    controller.execute("send_email", {"to": "a@example.com", "body": "hi"})
    snap = controller.state.snapshot()
    snap["emails"].append({"id": "fake", "to": "x", "body": "y"})
    # Mutating the snapshot must never affect the live sandbox state.
    assert len(controller.state.emails) == 1
