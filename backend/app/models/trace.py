"""
Trace: the complete recorded execution of one Scenario within one TestRun —
every event (LLM turns, tool calls, tool results), the agent's final
response, and the outcome. This is the raw material the Failure Classifier
reads, and what the Trace Viewer page renders.
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


class Trace(Base):
    __tablename__ = "traces"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    test_run_id: Mapped[str] = mapped_column(
        String, ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False
    )
    scenario_id: Mapped[str] = mapped_column(
        String, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False
    )
    # Ordered list of every step (LLM message / tool call / tool result) —
    # the full turn-by-turn record needed for deterministic replay.
    events: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    agent_response: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Flat list of {tool_name, params, success, data/error} — denormalized
    # from `events` for quick access without re-parsing the full event log.
    tool_calls: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # passed | failed | error | timeout
    final_status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    test_run: Mapped["TestRun"] = relationship(back_populates="traces")
    scenario: Mapped["Scenario"] = relationship(back_populates="traces")
    failures: Mapped[list["Failure"]] = relationship(
        back_populates="trace", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_traces_test_run_id", "test_run_id"),
        Index("ix_traces_scenario_id", "scenario_id"),
    )
