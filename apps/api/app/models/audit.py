"""Audit job, results, findings, SEO recommendations, action items."""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.video import VideoSource


class JobStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNDETERMINED = "UNDETERMINED"


class AuditJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "audit_jobs"

    video_source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("video_sources.id", ondelete="CASCADE"), index=True
    )
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    requested_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(32), default=JobStatus.QUEUED, nullable=False, index=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_stage: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cost_estimate: Mapped[Optional[float]] = mapped_column(Numeric(12, 6), nullable=True)
    actual_cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 6), nullable=True)

    video_source: Mapped["VideoSource"] = relationship("VideoSource", back_populates="audit_jobs")
    result: Mapped[Optional["AuditResult"]] = relationship(
        "AuditResult", back_populates="audit_job", uselist=False
    )


class AuditResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "audit_results"

    audit_job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("audit_jobs.id", ondelete="CASCADE"), unique=True, index=True
    )
    executive_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    model_info: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    raw_ai_response: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    audit_job: Mapped["AuditJob"] = relationship("AuditJob", back_populates="result")
    findings: Mapped[list["AuditFinding"]] = relationship(
        "AuditFinding", back_populates="audit_result", cascade="all, delete-orphan"
    )
    seo_recommendations: Mapped[list["SeoRecommendation"]] = relationship(
        "SeoRecommendation", back_populates="audit_result", cascade="all, delete-orphan"
    )
    action_items: Mapped[list["ActionItem"]] = relationship(
        "ActionItem", back_populates="audit_result", cascade="all, delete-orphan"
    )


class AuditFinding(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "audit_findings"

    audit_result_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("audit_results.id", ondelete="CASCADE"), index=True
    )
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), default=Severity.UNDETERMINED, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_ai_hypothesis: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    audit_result: Mapped["AuditResult"] = relationship("AuditResult", back_populates="findings")


class SeoRecommendation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "seo_recommendations"

    audit_result_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("audit_results.id", ondelete="CASCADE"), index=True
    )
    field: Mapped[str] = mapped_column(String(64), nullable=False)
    original_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proposed_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_ai_hypothesis: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    edited_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    edited_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    audit_result: Mapped["AuditResult"] = relationship(
        "AuditResult", back_populates="seo_recommendations"
    )


class ActionItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "action_items"

    audit_result_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("audit_results.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    related_finding_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    estimated_effort: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    assignee_user_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    audit_result: Mapped["AuditResult"] = relationship(
        "AuditResult", back_populates="action_items"
    )
