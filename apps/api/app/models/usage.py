"""AI usage ledger."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin


class AIUsageRecord(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "ai_usage_records"

    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, nullable=False)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, nullable=False)
    audit_job_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    provider_reported_cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 6), nullable=True)
    internal_estimated_cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 6), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    request_outcome: Mapped[str] = mapped_column(String(32), default="success", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
