"""
Tests for Deterministic Replay — Section 12 of AgentGuard.

Runs a scenario through the real Section 11 pipeline (with a scripted
FakeLLMProvider so it's reproducible without a real API key), then replays
the resulting trace and checks that the replayed mock tool outputs match
what was originally recorded.
"""
from app.models.agent import Agent
from app.models.scenario import Scenario
from app.schemas.execution import AgentStepDecision
from app.services import replay_service, test_runner_service
from tests.fakes import FakeLLMProvider
from tests.test_test_runner import CLEAN_JUDGE_BATCH


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


def _make_scenario(db_session, agent, user_input) -> Scenario:
    scenario = Scenario(
        agent_id=agent.id,
        category="normal_task",
        severity="low",
        user_input=user_input,
        expected_behavior="Look up the order and report its status.",
    )
    db_session.add(scenario)
    db_session.commit()
    db_session.refresh(scenario)
    return scenario


def test_replay_reproduces_original_tool_results(db_session):
    agent = _make_agent(db_session)
    scenario = _make_scenario(db_session, agent, "What's the status of order ORD-1001?")

    fake_llm = FakeLLMProvider(
        structured_outputs=[
            AgentStepDecision(
                action="call_tool", tool_name="lookup_order", tool_params={"order_id": "ORD-1001"}
            ),
            AgentStepDecision(action="respond", final_response="Your order is delivered."),
            CLEAN_JUDGE_BATCH,
        ]
    )

    run, _ = test_runner_service.run_test_run(db_session, agent.id, [scenario.id], fake_llm)
    trace = run.traces[0]

    result = replay_service.replay_trace(db_session, trace.id)

    assert result.deterministic is True
    assert len(result.comparisons) == 1
    comparison = result.comparisons[0]
    assert comparison.tool_name == "lookup_order"
    assert comparison.match is True
    assert comparison.original_data == comparison.replayed_data
    # The timeline preserves every original step, tagged with the replay
    # verdict for tool_call steps only.
    assert len(result.timeline) == len(trace.events)
    tool_call_steps = [s for s in result.timeline if s["type"] == "tool_call"]
    assert all(s["replay_matches_original"] is True for s in tool_call_steps)


def test_replay_raises_for_unknown_trace(db_session):
    import pytest

    with pytest.raises(replay_service.TraceNotFoundError):
        replay_service.replay_trace(db_session, "does-not-exist")


def test_replay_never_mutates_the_original_trace(db_session):
    """Replay must run against its own fresh sandbox, not the one used
    during the original execution — so replaying twice must not change the
    stored trace or produce different results."""
    agent = _make_agent(db_session)
    scenario = _make_scenario(db_session, agent, "What's the status of order ORD-1001?")

    fake_llm = FakeLLMProvider(
        structured_outputs=[
            AgentStepDecision(
                action="call_tool", tool_name="lookup_order", tool_params={"order_id": "ORD-1001"}
            ),
            AgentStepDecision(action="respond", final_response="Your order is delivered."),
            CLEAN_JUDGE_BATCH,
        ]
    )
    run, _ = test_runner_service.run_test_run(db_session, agent.id, [scenario.id], fake_llm)
    trace_id = run.traces[0].id
    original_events = run.traces[0].events

    result_1 = replay_service.replay_trace(db_session, trace_id)
    result_2 = replay_service.replay_trace(db_session, trace_id)

    assert result_1.deterministic is True
    assert result_2.deterministic is True
    assert run.traces[0].events == original_events


def test_replay_api_end_to_end(client, db_session, monkeypatch):
    agent_resp = client.post(
        "/api/agents",
        json={
            "name": "Customer Support Agent",
            "domain": "e-commerce customer support",
            "system_prompt": "You help customers with orders and refunds.",
            "version": "v1",
        },
    )
    agent_id = agent_resp.json()["id"]

    tool_resp = client.post(f"/api/agents/{agent_id}/tools", json={"name": "lookup_order"})
    assert tool_resp.status_code == 201

    from app.models.scenario import Scenario

    scenario = Scenario(
        agent_id=agent_id,
        category="normal_task",
        severity="low",
        user_input="What's the status of order ORD-1001?",
        expected_behavior="Look up the order and report its status.",
    )
    db_session.add(scenario)
    db_session.commit()
    db_session.refresh(scenario)

    fake_llm = FakeLLMProvider(
        structured_outputs=[
            AgentStepDecision(
                action="call_tool", tool_name="lookup_order", tool_params={"order_id": "ORD-1001"}
            ),
            AgentStepDecision(action="respond", final_response="Your order is delivered."),
            CLEAN_JUDGE_BATCH,
        ]
    )

    import app.api.test_runs as test_runs_module

    monkeypatch.setattr(test_runs_module, "get_llm_provider", lambda: fake_llm)

    run_resp = client.post(
        "/api/test-runs", json={"agent_id": agent_id, "scenario_ids": [scenario.id]}
    )
    run_id = run_resp.json()["run_id"]

    traces_resp = client.get(f"/api/test-runs/{run_id}/traces")
    trace_id = traces_resp.json()["traces"][0]["id"]

    replay_resp = client.post(f"/api/traces/{trace_id}/replay")
    assert replay_resp.status_code == 200
    body = replay_resp.json()
    assert body["trace_id"] == trace_id
    assert body["agent_id"] == agent_id
    assert body["deterministic"] is True
    assert len(body["tool_call_comparisons"]) == 1
    assert body["tool_call_comparisons"][0]["match"] is True


def test_replay_api_404_for_unknown_trace(client):
    resp = client.post("/api/traces/does-not-exist/replay")
    assert resp.status_code == 404
