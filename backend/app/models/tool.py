"""
Tool: one capability an Agent has access to (lookup_order, refund_order,
send_email, delete_account, ...). destructive/risk_level drive the unsafe-
action detector in the failure classifier later.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Tool(Base):
    __tablename__ = "tools"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    agent_id: Mapped[str] = mapped_column(
        String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    destructive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # low | medium | high | critical
    risk_level: Mapped[str] = mapped_column(String, nullable=False, default="low")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    agent: Mapped["Agent"] = relationship(back_populates="tools")

    __table_args__ = (
        Index("ix_tools_agent_id", "agent_id"),
        # A given agent shouldn't register the same tool name twice.
        Index("ux_tools_agent_id_name", "agent_id", "name", unique=True),
    )
