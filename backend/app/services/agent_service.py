"""
Business logic for Agents. Every time an agent is created, or an update
changes its system_prompt or version, we snapshot an AgentVersion row —
this is what powers regression comparison later (diff TestRuns across two
AgentVersions of the same agent).
"""
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.core.database import commit_or_rollback
from app.models.agent import Agent, AgentVersion
from app.schemas.agent import AgentCreate, AgentUpdate


def _snapshot_version(db: Session, agent: Agent) -> None:
    db.add(
        AgentVersion(
            agent_id=agent.id,
            version=agent.version,
            system_prompt=agent.system_prompt,
        )
    )


def create_agent(db: Session, payload: AgentCreate) -> Agent:
    agent = Agent(
        name=payload.name,
        domain=payload.domain,
        system_prompt=payload.system_prompt,
        version=payload.version,
        description=payload.description,
    )
    db.add(agent)
    db.flush()  # assigns agent.id without committing yet
    _snapshot_version(db, agent)
    commit_or_rollback(db, context="creating agent")
    db.refresh(agent)
    return agent


def list_agents(db: Session) -> List[Agent]:
    return (
        db.query(Agent)
        .options(joinedload(Agent.tools))
        .order_by(Agent.created_at.desc())
        .all()
    )


def get_agent(db: Session, agent_id: str) -> Optional[Agent]:
    return (
        db.query(Agent)
        .options(joinedload(Agent.tools))
        .filter(Agent.id == agent_id)
        .first()
    )


def update_agent(db: Session, agent_id: str, payload: AgentUpdate) -> Optional[Agent]:
    agent = get_agent(db, agent_id)
    if agent is None:
        return None

    data = payload.model_dump(exclude_unset=True)
    prompt_or_version_changed = (
        "system_prompt" in data and data["system_prompt"] != agent.system_prompt
    ) or ("version" in data and data["version"] != agent.version)

    for field, value in data.items():
        setattr(agent, field, value)

    if prompt_or_version_changed:
        _snapshot_version(db, agent)

    commit_or_rollback(db, context="updating agent")
    db.refresh(agent)
    return agent


def delete_agent(db: Session, agent_id: str) -> bool:
    agent = get_agent(db, agent_id)
    if agent is None:
        return False
    db.delete(agent)
    commit_or_rollback(db, context="deleting agent")
    return True
