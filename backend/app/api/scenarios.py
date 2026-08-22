"""
Scenario Generation API.

    POST /api/scenarios/generate
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.llm.exceptions import LLMConfigurationError
from app.llm.factory import get_llm_provider
from app.schemas.scenario import ScenarioGenerateRequest, ScenarioGenerateResponse, ScenarioRead
from app.services import agent_service
from app.services.scenario_service import ScenarioGenerationError, generate_scenarios

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.post("/generate", response_model=ScenarioGenerateResponse)
def generate(payload: ScenarioGenerateRequest, db: Session = Depends(get_db)):
    agent = agent_service.get_agent(db, payload.agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent '{payload.agent_id}' not found")

    try:
        llm_provider = get_llm_provider()
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        scenarios = generate_scenarios(db, agent, payload.number_of_scenarios, llm_provider)
    except ScenarioGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ScenarioGenerateResponse(
        agent_id=agent.id,
        requested=payload.number_of_scenarios,
        generated=len(scenarios),
        scenarios=[ScenarioRead.from_orm_scenario(s) for s in scenarios],
    )
