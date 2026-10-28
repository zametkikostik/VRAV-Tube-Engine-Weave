"""Video source and project schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    tenant_id: UUID
    organization_id: UUID


class ProjectPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    organization_id: UUID
    name: str
    description: Optional[str]
    created_by: UUID
    created_at: datetime


class VideoSourceCreate(BaseModel):
    project_id: UUID
    source_type: str = Field(pattern="^(youtube_url|transcript_upload|manual_metadata)$")
    youtube_url: Optional[str] = Field(None, max_length=2048)
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    transcript_text: Optional[str] = None
    language_code: Optional[str] = Field(None, max_length=16)


class VideoSourcePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    source_type: str
    youtube_video_id: Optional[str]
    original_url: Optional[str]
    status: str
    duration_seconds: Optional[int]
    language_code: Optional[str]
    error_message: Optional[str]
    created_at: datetime


class AuditJobCreate(BaseModel):
    video_source_id: UUID


class AuditJobPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    video_source_id: UUID
    tenant_id: UUID
    status: str
    progress_percent: int
    current_stage: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime
