"""
TestRun: one execution of a batch of Scenarios against a specific Agent
version. Aggregates into pass/fail counts and a reliability_score once
complete — this is what the Reliability Report and Regression Comparison
pages read.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    agent_id: Mapped[str] = mapped_column(
        String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    # Which agent version this run tested — enables regression comparison
    # between e.g. "v1" and "v2" of the same agent.
    version: Mapped[str] = mapped_column(String, nullable=False)
    # pending | running | completed | failed
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    total_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    passed_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reliability_score: Mapped[float] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    agent: Mapped["Agent"] = relationship(back_populates="test_runs")
    traces: Mapped[list["Trace"]] = relationship(
        back_populates="test_run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_test_runs_agent_id", "agent_id"),
        Index("ix_test_runs_status", "status"),
    )
