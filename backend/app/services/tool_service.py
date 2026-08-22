"""
Business logic for Tools, always scoped to a parent Agent.
"""
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.models.tool import Tool
from app.schemas.tool import ToolCreate


class DuplicateToolNameError(Exception):
    """Raised when a tool name is registered twice for the same agent."""


def agent_exists(db: Session, agent_id: str) -> bool:
    return db.query(Agent.id).filter(Agent.id == agent_id).first() is not None


def create_tool(db: Session, agent_id: str, payload: ToolCreate) -> Tool:
    tool = Tool(
        agent_id=agent_id,
        name=payload.name,
        description=payload.description,
        destructive=payload.destructive,
        risk_level=payload.risk_level,
    )
    db.add(tool)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateToolNameError(
            f"Tool '{payload.name}' already exists for this agent"
        ) from exc
    db.refresh(tool)
    return tool


def list_tools(db: Session, agent_id: str) -> List[Tool]:
    return db.query(Tool).filter(Tool.agent_id == agent_id).order_by(Tool.created_at).all()
