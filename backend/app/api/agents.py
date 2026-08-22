"""
Agent Configuration API.

    POST   /api/agents
    GET    /api/agents
    GET    /api/agents/{agent_id}
    PUT    /api/agents/{agent_id}
    DELETE /api/agents/{agent_id}
    POST   /api/agents/{agent_id}/tools
    GET    /api/agents/{agent_id}/tools
    GET    /api/agents/{agent_id}/scenarios

Note: GET /api/agents/{agent_id}/regression (Section 13) lives in
app/api/regression.py, not here — keeping every route for a given
resource-path prefix in one module avoids two routers silently competing
for the same path.
"""
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.agent import AgentCreate, AgentRead, AgentUpdate
from app.schemas.scenario import ScenarioRead
from app.schemas.tool import ToolCreate, ToolRead
from app.services import agent_service, scenario_service, tool_service

router = APIRouter(prefix="/api/agents", tags=["agents"])

_ID_MAX_LEN = 64  # generous bound for a UUID4 string id


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
def create_agent(payload: AgentCreate, db: Session = Depends(get_db)):
    return agent_service.create_agent(db, payload)


@router.get("", response_model=list[AgentRead])
def list_agents(db: Session = Depends(get_db)):
    return agent_service.list_agents(db)


@router.get("/{agent_id}", response_model=AgentRead)
def get_agent(agent_id: str = Path(max_length=_ID_MAX_LEN), db: Session = Depends(get_db)):
    agent = agent_service.get_agent(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return agent


@router.put("/{agent_id}", response_model=AgentRead)
def update_agent(
    agent_id: str = Path(max_length=_ID_MAX_LEN),
    payload: AgentUpdate = ...,
    db: Session = Depends(get_db),
):
    agent = agent_service.update_agent(db, agent_id, payload)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(agent_id: str = Path(max_length=_ID_MAX_LEN), db: Session = Depends(get_db)):
    deleted = agent_service.delete_agent(db, agent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")


@router.post("/{agent_id}/tools", response_model=ToolRead, status_code=status.HTTP_201_CREATED)
def create_tool(
    agent_id: str = Path(max_length=_ID_MAX_LEN),
    payload: ToolCreate = ...,
    db: Session = Depends(get_db),
):
    if not tool_service.agent_exists(db, agent_id):
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    try:
        return tool_service.create_tool(db, agent_id, payload)
    except tool_service.DuplicateToolNameError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{agent_id}/tools", response_model=list[ToolRead])
def list_tools(agent_id: str = Path(max_length=_ID_MAX_LEN), db: Session = Depends(get_db)):
    if not tool_service.agent_exists(db, agent_id):
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return tool_service.list_tools(db, agent_id)


@router.get("/{agent_id}/scenarios", response_model=list[ScenarioRead])
def list_scenarios(agent_id: str = Path(max_length=_ID_MAX_LEN), db: Session = Depends(get_db)):
    """Every scenario ever generated for this agent, persisted in the
    database and returned newest-first — so refreshing the page or coming
    back later doesn't lose scenarios the way relying on in-memory state
    from the last generate() call would."""
    if not tool_service.agent_exists(db, agent_id):
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    scenarios = scenario_service.list_scenarios(db, agent_id)
    return [ScenarioRead.from_orm_scenario(s) for s in scenarios]
