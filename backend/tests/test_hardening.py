"""
Tests for the backend hardening pass: input validation/sanitization,
CORS configuration, LLM provider configuration errors, database rollback
behavior, and removal of the duplicate regression route.
"""
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.database import commit_or_rollback
from app.llm.exceptions import LLMConfigurationError
from app.llm.factory import get_llm_provider
from app.schemas.agent import AgentCreate
from app.schemas.scenario import ScenarioGenerateRequest
from app.schemas.test_run import TestRunCreateRequest
from app.schemas.tool import ToolCreate

AGENT_PAYLOAD = {
    "name": "Customer Support Agent",
    "domain": "e-commerce customer support",
    "system_prompt": "You help customers with orders and refunds.",
    "version": "v1",
}


# --- API-level validation ---------------------------------------------------


def test_create_agent_rejects_blank_name(client):
    resp = client.post("/api/agents", json={**AGENT_PAYLOAD, "name": "   "})
    assert resp.status_code == 422
    assert resp.json()["status_code"] == 422


def test_create_agent_rejects_missing_field(client):
    payload = {k: v for k, v in AGENT_PAYLOAD.items() if k != "system_prompt"}
    resp = client.post("/api/agents", json=payload)
    assert resp.status_code == 422


def test_create_agent_rejects_oversized_name(client):
    resp = client.post("/api/agents", json={**AGENT_PAYLOAD, "name": "x" * 500})
    assert resp.status_code == 422


def test_create_agent_strips_whitespace(client):
    resp = client.post("/api/agents", json={**AGENT_PAYLOAD, "name": "  Support Bot  "})
    assert resp.status_code == 201
    assert resp.json()["name"] == "Support Bot"


def test_create_tool_rejects_invalid_risk_level(client):
    agent_resp = client.post("/api/agents", json=AGENT_PAYLOAD)
    agent_id = agent_resp.json()["id"]
    resp = client.post(
        f"/api/agents/{agent_id}/tools",
        json={"name": "lookup_order", "risk_level": "apocalyptic"},
    )
    assert resp.status_code == 422


def test_create_tool_duplicate_name_returns_409(client):
    agent_resp = client.post("/api/agents", json=AGENT_PAYLOAD)
    agent_id = agent_resp.json()["id"]
    first = client.post(f"/api/agents/{agent_id}/tools", json={"name": "lookup_order"})
    assert first.status_code == 201
    second = client.post(f"/api/agents/{agent_id}/tools", json={"name": "lookup_order"})
    assert second.status_code == 409


def test_get_agent_rejects_overlong_path_id(client):
    resp = client.get(f"/api/agents/{'x' * 500}")
    assert resp.status_code == 422


def test_get_agent_unknown_id_returns_404(client):
    resp = client.get("/api/agents/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["status_code"] == 404


def test_test_run_request_rejects_empty_scenario_list(client):
    resp = client.post("/api/test-runs", json={"agent_id": "abc", "scenario_ids": []})
    assert resp.status_code == 422


def test_test_run_request_rejects_too_many_scenarios():
    with pytest.raises(ValidationError):
        TestRunCreateRequest(agent_id="abc", scenario_ids=[str(i) for i in range(51)])


def test_scenario_generate_request_bounds_count():
    with pytest.raises(ValidationError):
        ScenarioGenerateRequest(agent_id="abc", number_of_scenarios=100)


# --- Pydantic schema unit tests (no HTTP layer) -----------------------------


def test_agent_create_rejects_blank_domain():
    with pytest.raises(ValidationError):
        AgentCreate(**{**AGENT_PAYLOAD, "domain": "  "})


def test_tool_create_strips_and_bounds_description():
    tool = ToolCreate(name="lookup_order", description="  looks up an order  ")
    assert tool.description == "looks up an order"

    with pytest.raises(ValidationError):
        ToolCreate(name="lookup_order", description="x" * 2000)


# --- CORS configuration ------------------------------------------------------


def test_settings_rejects_wildcard_cors_origin():
    with pytest.raises(ValidationError):
        Settings(cors_origins="*", database_url="sqlite://")


def test_settings_parses_multiple_cors_origins():
    settings = Settings(
        cors_origins="http://localhost:5173, http://localhost:3000",
        database_url="sqlite://",
    )
    assert settings.cors_origin_list == ["http://localhost:5173", "http://localhost:3000"]


def test_cors_preflight_allows_configured_origin(client):
    resp = client.options(
        "/api/agents",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"


# --- Settings: secret hygiene -------------------------------------------------


def test_api_key_not_exposed_via_repr():
    settings = Settings(openai_api_key="sk-super-secret-value", database_url="sqlite://")
    assert "sk-super-secret-value" not in repr(settings)


def test_log_level_validated():
    with pytest.raises(ValidationError):
        Settings(log_level="LOUD", database_url="sqlite://")
    settings = Settings(log_level="debug", database_url="sqlite://")
    assert settings.log_level == "DEBUG"


# --- LLM provider factory -----------------------------------------------------


def test_gemini_provider_raises_clear_configuration_error_when_key_missing():
    """GeminiProvider (like OpenAIProvider) must fail with a clear,
    catchable LLMConfigurationError when its API key isn't set — never an
    ImportError or an unhandled exception leaking out of the factory."""
    settings = Settings(llm_provider="gemini", gemini_api_key="", database_url="sqlite://")
    with pytest.raises(LLMConfigurationError):
        get_llm_provider(settings)


def test_gemini_provider_constructs_with_api_key():
    settings = Settings(
        llm_provider="gemini", gemini_api_key="fake-key-for-test", database_url="sqlite://"
    )
    provider = get_llm_provider(settings)
    assert provider is not None


# --- Database error handling --------------------------------------------------


def test_commit_or_rollback_rolls_back_and_reraises_on_failure(db_session):
    from app.models.agent import Agent

    # Commit something invalid at the DB layer (NOT NULL violation) and
    # confirm commit_or_rollback rolls back cleanly and re-raises rather
    # than leaving the session in a broken, half-committed state.
    bad_agent = Agent(name=None, domain="x", system_prompt="x", version="v1")  # type: ignore[arg-type]
    db_session.add(bad_agent)

    from sqlalchemy.exc import SQLAlchemyError

    with pytest.raises(SQLAlchemyError):
        commit_or_rollback(db_session, context="test invalid insert")

    # Session must still be usable afterward (rollback actually happened).
    db_session.rollback()
    from app.models.agent import Agent as AgentModel

    assert db_session.query(AgentModel).count() == 0


def test_duplicate_regression_route_removed(client):
    """Regression: agents.py used to define its own copy of
    GET /{agent_id}/regression, silently shadowing app/api/regression.py's
    version. Only one implementation should exist now, and it must still
    respond (not a generic missing-route 404)."""
    agent_resp = client.post("/api/agents", json=AGENT_PAYLOAD)
    agent_id = agent_resp.json()["id"]

    resp = client.get(f"/api/agents/{agent_id}/regression")
    # 400 (no version/run selectors given) proves the real regression
    # handler is the one that ran, not a generic 404 from a missing route.
    assert resp.status_code == 400
