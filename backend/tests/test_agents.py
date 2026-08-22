"""
Tests for the Agent Configuration API — Section 4 of AgentGuard.

Seeds the demo Customer Support Agent and its four tools, matching the
example request/response payloads used in the documentation.
"""

AGENT_PAYLOAD = {
    "name": "Customer Support Agent",
    "domain": "e-commerce customer support",
    "system_prompt": (
        "You are a helpful customer support agent for an online store. "
        "You can look up orders, issue refunds, send emails, and delete "
        "customer accounts when explicitly authorized. Always verify order "
        "ownership before taking action. Never delete an account without "
        "explicit, unambiguous confirmation from the account holder."
    ),
    "version": "v1",
    "description": "Handles order lookups, refunds, and account requests.",
}

TOOL_PAYLOADS = [
    {
        "name": "lookup_order",
        "description": "Look up an order by its order ID",
        "destructive": False,
        "risk_level": "low",
    },
    {
        "name": "refund_order",
        "description": "Issue a refund for a given order",
        "destructive": True,
        "risk_level": "high",
    },
    {
        "name": "send_email",
        "description": "Send an email to the customer",
        "destructive": False,
        "risk_level": "low",
    },
    {
        "name": "delete_account",
        "description": "Permanently delete a customer account",
        "destructive": True,
        "risk_level": "critical",
    },
]


def _create_agent(client, payload=None):
    return client.post("/api/agents", json=payload or AGENT_PAYLOAD)


# --- Agent CRUD --------------------------------------------------------

def test_create_agent(client):
    resp = _create_agent(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Customer Support Agent"
    assert body["version"] == "v1"
    assert body["tools"] == []
    assert body["id"]
    assert body["created_at"]


def test_create_agent_rejects_blank_fields(client):
    bad = {**AGENT_PAYLOAD, "name": "   "}
    resp = _create_agent(client, bad)
    assert resp.status_code == 422


def test_list_agents(client):
    _create_agent(client)
    _create_agent(client, {**AGENT_PAYLOAD, "name": "Second Agent"})

    resp = client.get("/api/agents")
    assert resp.status_code == 200
    names = {a["name"] for a in resp.json()}
    assert names == {"Customer Support Agent", "Second Agent"}


def test_get_agent(client):
    created = _create_agent(client).json()
    resp = client.get(f"/api/agents/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_agent_404(client):
    resp = client.get("/api/agents/does-not-exist")
    assert resp.status_code == 404
    assert "not found" in resp.json()["error"].lower()


def test_update_agent_put(client):
    created = _create_agent(client).json()

    resp = client.put(
        f"/api/agents/{created['id']}",
        json={"version": "v2", "system_prompt": "Updated prompt."},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == "v2"
    assert body["system_prompt"] == "Updated prompt."
    assert body["name"] == "Customer Support Agent"  # untouched field preserved


def test_update_agent_404(client):
    resp = client.put("/api/agents/does-not-exist", json={"version": "v2"})
    assert resp.status_code == 404


def test_delete_agent(client):
    created = _create_agent(client).json()
    resp = client.delete(f"/api/agents/{created['id']}")
    assert resp.status_code == 204

    resp = client.get(f"/api/agents/{created['id']}")
    assert resp.status_code == 404


def test_delete_agent_404(client):
    resp = client.delete("/api/agents/does-not-exist")
    assert resp.status_code == 404


# --- Tool sub-resource ---------------------------------------------------

def test_create_tool(client):
    agent = _create_agent(client).json()

    resp = client.post(f"/api/agents/{agent['id']}/tools", json=TOOL_PAYLOADS[1])
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "refund_order"
    assert body["destructive"] is True
    assert body["risk_level"] == "high"
    assert body["agent_id"] == agent["id"]


def test_create_tool_for_missing_agent_404(client):
    resp = client.post("/api/agents/does-not-exist/tools", json=TOOL_PAYLOADS[0])
    assert resp.status_code == 404


def test_create_tool_invalid_risk_level(client):
    agent = _create_agent(client).json()
    bad_tool = {**TOOL_PAYLOADS[0], "risk_level": "extreme"}
    resp = client.post(f"/api/agents/{agent['id']}/tools", json=bad_tool)
    assert resp.status_code == 422


def test_create_duplicate_tool_name_conflict(client):
    agent = _create_agent(client).json()
    client.post(f"/api/agents/{agent['id']}/tools", json=TOOL_PAYLOADS[0])
    resp = client.post(f"/api/agents/{agent['id']}/tools", json=TOOL_PAYLOADS[0])
    assert resp.status_code == 409


def test_list_tools(client):
    agent = _create_agent(client).json()
    for tool_payload in TOOL_PAYLOADS:
        r = client.post(f"/api/agents/{agent['id']}/tools", json=tool_payload)
        assert r.status_code == 201

    resp = client.get(f"/api/agents/{agent['id']}/tools")
    assert resp.status_code == 200
    names = {t["name"] for t in resp.json()}
    assert names == {t["name"] for t in TOOL_PAYLOADS}


def test_list_tools_for_missing_agent_404(client):
    resp = client.get("/api/agents/does-not-exist/tools")
    assert resp.status_code == 404


def test_get_agent_includes_tools(client):
    agent = _create_agent(client).json()
    client.post(f"/api/agents/{agent['id']}/tools", json=TOOL_PAYLOADS[0])

    resp = client.get(f"/api/agents/{agent['id']}")
    assert resp.status_code == 200
    tools = resp.json()["tools"]
    assert len(tools) == 1
    assert tools[0]["name"] == "lookup_order"


def test_deleting_agent_cascades_to_tools(client, db_session):
    from app.models.tool import Tool

    agent = _create_agent(client).json()
    client.post(f"/api/agents/{agent['id']}/tools", json=TOOL_PAYLOADS[0])

    client.delete(f"/api/agents/{agent['id']}")

    remaining = db_session.query(Tool).filter(Tool.agent_id == agent["id"]).all()
    assert remaining == []


def test_agent_version_snapshot_created_on_create_and_prompt_change(client, db_session):
    from app.models.agent import AgentVersion

    agent = _create_agent(client).json()
    versions = db_session.query(AgentVersion).filter(AgentVersion.agent_id == agent["id"]).all()
    assert len(versions) == 1
    assert versions[0].version == "v1"

    client.put(f"/api/agents/{agent['id']}", json={"version": "v2", "system_prompt": "New prompt"})

    versions = db_session.query(AgentVersion).filter(AgentVersion.agent_id == agent["id"]).all()
    assert len(versions) == 2
    assert {v.version for v in versions} == {"v1", "v2"}
