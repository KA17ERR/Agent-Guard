"""
Failure: one classified failure found within a Trace. A single Trace can
have zero, one, or several Failures (e.g. a trace could show both a
prompt_injection susceptibility AND an unsafe_destructive_action).
category is one of the 11 failure categories from the spec:
tool_misuse, tool_loop, hallucination, goal_drift, prompt_injection,
instruction_hijacking, unsafe_destructive_action, unauthorized_action,
invalid_tool_call, task_failure, timeout.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Failure(Base):
    __tablename__ = "failures"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    trace_id: Mapped[str] = mapped_column(
        String, ForeignKey("traces.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String, nullable=False)
    # low | medium | high | critical
    severity: Mapped[str] = mapped_column(String, nullable=False, default="medium")
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    recommendation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # 0.0 - 1.0 confidence from the classifier
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    trace: Mapped["Trace"] = relationship(back_populates="failures")

    __table_args__ = (
        Index("ix_failures_trace_id", "trace_id"),
        Index("ix_failures_category", "category"),
    )
