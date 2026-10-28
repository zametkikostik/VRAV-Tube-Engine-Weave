"""Video source and metadata models."""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.audit import AuditJob


class SourceType(StrEnum):
    YOUTUBE_URL = "youtube_url"
    YOUTUBE_OAUTH = "youtube_oauth"
    TRANSCRIPT_UPLOAD = "transcript_upload"
    SUBTITLE_FILE = "subtitle_file"
    VIDEO_FILE = "video_file"
    MANUAL_METADATA = "manual_metadata"


class SourceStatus(StrEnum):
    PENDING = "pending"
    VALIDATED = "validated"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "projects"

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    video_sources: Mapped[list["VideoSource"]] = relationship(
        "VideoSource", back_populates="project", lazy="selectin"
    )


class VideoSource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "video_sources"

    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    youtube_video_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    original_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    storage_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=SourceStatus.PENDING, nullable=False)
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="video_sources")
    metadata_row: Mapped[Optional["VideoMetadata"]] = relationship(
        "VideoMetadata", back_populates="video_source", uselist=False
    )
    transcripts: Mapped[list["Transcript"]] = relationship(
        "Transcript", back_populates="video_source"
    )
    audit_jobs: Mapped[list["AuditJob"]] = relationship(
        "AuditJob", back_populates="video_source"
    )


class VideoMetadata(Base, TimestampMixin):
    __tablename__ = "video_metadata"

    video_source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("video_sources.id", ondelete="CASCADE"),
        primary_key=True,
    )
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list[Any]]] = mapped_column(JSONB, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    view_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    like_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    chapters_json: Mapped[Optional[list[Any]]] = mapped_column(JSONB, nullable=True)
    raw_api_response: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    video_source: Mapped["VideoSource"] = relationship(
        "VideoSource", back_populates="metadata_row"
    )


class Transcript(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "transcripts"

    video_source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("video_sources.id", ondelete="CASCADE"), index=True
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    language_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    segments_json: Mapped[Optional[list[Any]]] = mapped_column(JSONB, nullable=True)
    quality_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    video_source: Mapped["VideoSource"] = relationship(
        "VideoSource", back_populates="transcripts"
    )
