"""Audit result schemas."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FindingPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: str
    severity: str
    title: str
    explanation: Optional[str]
    recommendation: Optional[str]
    confidence: Optional[str]
    requires_human_review: bool


class SeoRecPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    field: str
    original_value: Optional[str]
    proposed_value: Optional[str]
    explanation: Optional[str]
    confidence: Optional[str]
    is_ai_hypothesis: bool
    status: str


class ActionItemPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: Optional[str]
    priority: int
    status: str


class AuditResultPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    audit_job_id: UUID
    executive_summary: Optional[str]
    confidence_notes: Optional[str]
    generated_at: Optional[datetime]
    model_info: Optional[dict[str, Any]]
    findings: list[FindingPublic] = []
    seo_recommendations: list[SeoRecPublic] = []
    action_items: list[ActionItemPublic] = []


class AuditJobDetail(BaseModel):
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
    result: Optional[AuditResultPublic] = None
