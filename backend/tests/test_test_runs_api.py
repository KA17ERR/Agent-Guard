"""
End-to-end API tests for POST /api/test-runs and the report/traces
read endpoints (Sections 10-11).
"""
from app.schemas.execution import AgentStepDecision
from tests.fakes import FakeLLMProvider
from tests.test_test_runner import CLEAN_JUDGE_BATCH


def test_full_test_run_flow_via_api(client, db_session, monkeypatch):
    agent_resp = client.post(
        "/api/agents",
        json={
            "name": "Customer Support Agent",
            "domain": "e-commerce customer support",
            "system_prompt": "You help customers with orders and refunds.",
            "version": "v1",
        },
    )
    assert agent_resp.status_code == 201
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
    assert run_resp.status_code == 201
    run_body = run_resp.json()
    assert run_body["total_tests"] == 1
    assert run_body["passed"] == 1
    run_id = run_body["run_id"]

    get_resp = client.get(f"/api/test-runs/{run_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "completed"

    traces_resp = client.get(f"/api/test-runs/{run_id}/traces")
    assert traces_resp.status_code == 200
    assert len(traces_resp.json()["traces"]) == 1

    report_resp = client.get(f"/api/test-runs/{run_id}/report")
    assert report_resp.status_code == 200
    report = report_resp.json()
    assert report["agent_id"] == agent_id
    assert report["total_tests"] == 1
    assert "category_scores" in report


def test_test_run_404_for_unknown_agent(client, monkeypatch):
    import app.api.test_runs as test_runs_module

    monkeypatch.setattr(test_runs_module, "get_llm_provider", lambda: FakeLLMProvider())

    resp = client.post(
        "/api/test-runs", json={"agent_id": "does-not-exist", "scenario_ids": ["s1"]}
    )
    assert resp.status_code == 404


def test_get_report_404_for_unknown_run(client):
    resp = client.get("/api/test-runs/does-not-exist/report")
    assert resp.status_code == 404
