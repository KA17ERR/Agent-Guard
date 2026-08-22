"""
Scenario: one generated test case for an Agent — a simulated user input
plus what "correct" agent behavior looks like, used to drive an execution
in the sandbox. category/severity classify what kind of scenario this is
(e.g. category="prompt_injection", severity="high").
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    agent_id: Mapped[str] = mapped_column(
        String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    # e.g. realistic | adversarial | prompt_injection | goal_drift | destructive_bait | edge_case
    category: Mapped[str] = mapped_column(String, nullable=False)
    # low | medium | high | critical
    severity: Mapped[str] = mapped_column(String, nullable=False, default="medium")
    user_input: Mapped[str] = mapped_column(Text, nullable=False)
    expected_behavior: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Python attribute is `scenario_metadata` because `metadata` is reserved
    # by SQLAlchemy's declarative Base; the actual DB column is named
    # "metadata" so it matches the spec, and the API schema exposes it as
    # `metadata` too (see schemas/scenario.py).
    scenario_metadata: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    agent: Mapped["Agent"] = relationship(back_populates="scenarios")
    traces: Mapped[list["Trace"]] = relationship(back_populates="scenario")

    __table_args__ = (
        Index("ix_scenarios_agent_id", "agent_id"),
        Index("ix_scenarios_category", "category"),
    )
