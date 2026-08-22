"""
Tests for Scenario Generation — Section 7 of AgentGuard.

Uses FakeLLMProvider so these run without a real API key, while still
exercising the full generate -> validate -> persist path.
"""
from app.models.agent import Agent
from app.schemas.scenario import GeneratedScenario, GeneratedScenarioBatch
from app.services.scenario_service import ScenarioGenerationError, generate_scenarios
from tests.fakes import FakeLLMProvider


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


def _scenario(category="normal_task", severity="low") -> GeneratedScenario:
    return GeneratedScenario(
        category=category,
        severity=severity,
        user_input="Hi, can you check on order ORD-1001?",
        expected_behavior="Look up the order and report its status accurately.",
        attack_strategy="",
        reason_for_test="Baseline happy-path coverage.",
    )


def test_generate_scenarios_persists_rows(db_session):
    agent = _make_agent(db_session)
    batch = GeneratedScenarioBatch(
        scenarios=[
            _scenario("normal_task", "low"),
            _scenario("prompt_injection", "high"),
        ]
    )
    fake_llm = FakeLLMProvider(structured_outputs=[batch])

    rows = generate_scenarios(db_session, agent, number_of_scenarios=2, llm_provider=fake_llm)

    assert len(rows) == 2
    assert {r.category for r in rows} == {"normal_task", "prompt_injection"}
    for row in rows:
        assert row.id
        assert row.agent_id == agent.id
        assert "reason_for_test" in row.scenario_metadata


def test_generate_scenarios_raises_on_empty_batch(db_session):
    agent = _make_agent(db_session)
    fake_llm = FakeLLMProvider(structured_outputs=[GeneratedScenarioBatch(scenarios=[])])

    try:
        generate_scenarios(db_session, agent, number_of_scenarios=2, llm_provider=fake_llm)
        assert False, "expected ScenarioGenerationError"
    except ScenarioGenerationError:
        pass


def test_generate_scenarios_endpoint_end_to_end(client, db_session, monkeypatch):
    agent_payload = {
        "name": "Customer Support Agent",
        "domain": "e-commerce customer support",
        "system_prompt": "You help customers with orders and refunds.",
        "version": "v1",
    }
    agent_resp = client.post("/api/agents", json=agent_payload)
    assert agent_resp.status_code == 201
    agent_id = agent_resp.json()["id"]

    batch = GeneratedScenarioBatch(scenarios=[_scenario()])
    fake_llm = FakeLLMProvider(structured_outputs=[batch])

    import app.api.scenarios as scenarios_module

    monkeypatch.setattr(scenarios_module, "get_llm_provider", lambda: fake_llm)

    resp = client.post(
        "/api/scenarios/generate",
        json={"agent_id": agent_id, "number_of_scenarios": 1},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["generated"] == 1
    assert body["scenarios"][0]["agent_id"] == agent_id


def test_list_scenarios_endpoint_returns_persisted_rows(client, db_session, monkeypatch):
    """The gap this closes: scenarios generated in one request must still
    be retrievable afterward via a plain GET, not just held in whatever
    the generate() response happened to return."""
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

    batch = GeneratedScenarioBatch(scenarios=[_scenario(), _scenario("prompt_injection", "high")])
    fake_llm = FakeLLMProvider(structured_outputs=[batch])

    import app.api.scenarios as scenarios_module

    monkeypatch.setattr(scenarios_module, "get_llm_provider", lambda: fake_llm)

    gen_resp = client.post(
        "/api/scenarios/generate", json={"agent_id": agent_id, "number_of_scenarios": 2}
    )
    assert gen_resp.status_code == 200

    # Simulate "coming back later" — a fresh GET with no reliance on the
    # generate() response at all.
    list_resp = client.get(f"/api/agents/{agent_id}/scenarios")
    assert list_resp.status_code == 200
    scenarios = list_resp.json()
    assert len(scenarios) == 2
    assert {s["category"] for s in scenarios} == {"normal_task", "prompt_injection"}


def test_list_scenarios_404_for_unknown_agent(client):
    resp = client.get("/api/agents/does-not-exist/scenarios")
    assert resp.status_code == 404


def test_list_scenarios_empty_for_agent_with_none_generated_yet(client):
    agent_resp = client.post(
        "/api/agents",
        json={
            "name": "Fresh Agent",
            "domain": "test domain",
            "system_prompt": "test prompt",
            "version": "v1",
        },
    )
    agent_id = agent_resp.json()["id"]

    resp = client.get(f"/api/agents/{agent_id}/scenarios")
    assert resp.status_code == 200
    assert resp.json() == []
