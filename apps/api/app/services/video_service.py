"""Video source intake and project management."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditJob, JobStatus
from app.models.organization import OrganizationMember
from app.models.tenant import Tenant
from app.models.video import (
    Project,
    SourceStatus,
    SourceType,
    Transcript,
    VideoMetadata,
    VideoSource,
)
from app.schemas.video import ProjectCreate, VideoSourceCreate
from app.utils.youtube import extract_youtube_video_id


async def assert_org_member(db: AsyncSession, user_id: UUID, organization_id: UUID) -> None:
    member = await db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
    )
    if not member:
        raise PermissionError("Not a member of this organization")


async def assert_tenant_in_org(db: AsyncSession, tenant_id: UUID, organization_id: UUID) -> Tenant:
    tenant = await db.scalar(
        select(Tenant).where(
            Tenant.id == tenant_id,
            Tenant.organization_id == organization_id,
            Tenant.is_active.is_(True),
        )
    )
    if not tenant:
        raise PermissionError("Tenant not found in organization")
    return tenant


async def create_project(
    db: AsyncSession,
    data: ProjectCreate,
    user_id: UUID,
) -> Project:
    await assert_org_member(db, user_id, data.organization_id)
    await assert_tenant_in_org(db, data.tenant_id, data.organization_id)

    project = Project(
        tenant_id=data.tenant_id,
        organization_id=data.organization_id,
        name=data.name,
        description=data.description,
        created_by=user_id,
    )
    db.add(project)
    await db.flush()
    return project


async def create_video_source(
    db: AsyncSession,
    data: VideoSourceCreate,
    user_id: UUID,
) -> VideoSource:
    project = await db.scalar(select(Project).where(Project.id == data.project_id))
    if not project:
        raise ValueError("Project not found")
    await assert_org_member(db, user_id, project.organization_id)

    youtube_id: Optional[str] = None
    original_url: Optional[str] = None
    status = SourceStatus.PENDING

    if data.source_type == SourceType.YOUTUBE_URL:
        if not data.youtube_url:
            raise ValueError("youtube_url is required for youtube_url source type")
        youtube_id = extract_youtube_video_id(data.youtube_url)
        if not youtube_id:
            raise ValueError("Invalid YouTube URL or video ID")
        original_url = data.youtube_url
        status = SourceStatus.VALIDATED
    elif data.source_type == SourceType.TRANSCRIPT_UPLOAD:
        if not data.transcript_text or len(data.transcript_text.strip()) < 10:
            raise ValueError("transcript_text is required and must be non-trivial")
        status = SourceStatus.READY
    elif data.source_type == SourceType.MANUAL_METADATA:
        status = SourceStatus.READY
    else:
        raise ValueError(f"Unsupported source_type for MVP: {data.source_type}")

    source = VideoSource(
        project_id=project.id,
        source_type=data.source_type,
        youtube_video_id=youtube_id,
        original_url=original_url,
        status=status,
        language_code=data.language_code,
    )
    db.add(source)
    await db.flush()

    if data.title or data.description:
        meta = VideoMetadata(
            video_source_id=source.id,
            title=data.title,
            description=data.description,
            fetched_at=datetime.now(timezone.utc),
        )
        db.add(meta)

    if data.transcript_text:
        tr = Transcript(
            video_source_id=source.id,
            source="upload",
            language_code=data.language_code,
            content_text=data.transcript_text.strip(),
        )
        db.add(tr)

    await db.flush()
    return source


async def create_audit_job(
    db: AsyncSession,
    video_source_id: UUID,
    user_id: UUID,
) -> AuditJob:
    source = await db.scalar(select(VideoSource).where(VideoSource.id == video_source_id))
    if not source:
        raise ValueError("Video source not found")
    project = await db.scalar(select(Project).where(Project.id == source.project_id))
    if not project:
        raise ValueError("Project not found")
    await assert_org_member(db, user_id, project.organization_id)

    if source.status not in (SourceStatus.VALIDATED, SourceStatus.READY):
        raise ValueError(f"Video source is not ready for audit (status={source.status})")

    from app.services.entitlements import assert_can_start_audit

    await assert_can_start_audit(db, project.organization_id)

    job = AuditJob(
        video_source_id=source.id,
        tenant_id=project.tenant_id,
        requested_by=user_id,
        status=JobStatus.QUEUED,
        progress_percent=0,
        current_stage="queued",
    )
    db.add(job)
    await db.flush()

    try:
        from app.celery_app import run_audit_task

        async_result = run_audit_task.delay(str(job.id))
        job.celery_task_id = async_result.id
        await db.flush()
    except Exception:
        from app.services.audit_pipeline import run_audit_analysis

        await run_audit_analysis(db, job.id)

    return job
