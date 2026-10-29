"""Projects, video sources and audit job endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.audit import AuditJob
from app.models.video import Project, VideoSource
from app.schemas.video import (
    AuditJobCreate,
    AuditJobPublic,
    ProjectCreate,
    ProjectPublic,
    VideoSourceCreate,
    VideoSourcePublic,
)
from app.services.video_service import create_audit_job, create_project, create_video_source

router = APIRouter(tags=["projects"])


@router.post("/projects", response_model=ProjectPublic, status_code=status.HTTP_201_CREATED)
async def create_project_endpoint(
    data: ProjectCreate,
    user: CurrentUser,
    db: DbSession,
) -> Project:
    try:
        project = await create_project(db, data, user.id)
        await db.commit()
        await db.refresh(project)
        return project
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/projects/{project_id}", response_model=ProjectPublic)
async def get_project(
    project_id: UUID,
    user: CurrentUser,
    db: DbSession,
) -> Project:
    from app.services.video_service import assert_org_member

    project = await db.scalar(select(Project).where(Project.id == project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        await assert_org_member(db, user.id, project.organization_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return project


@router.post("/videos", response_model=VideoSourcePublic, status_code=status.HTTP_201_CREATED)
async def create_video_endpoint(
    data: VideoSourceCreate,
    user: CurrentUser,
    db: DbSession,
) -> VideoSource:
    try:
        source = await create_video_source(db, data, user.id)
        await db.commit()
        await db.refresh(source)
        return source
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/videos/{video_id}", response_model=VideoSourcePublic)
async def get_video(
    video_id: UUID,
    user: CurrentUser,
    db: DbSession,
) -> VideoSource:
    from app.services.video_service import assert_org_member

    source = await db.scalar(select(VideoSource).where(VideoSource.id == video_id))
    if not source:
        raise HTTPException(status_code=404, detail="Video source not found")
    project = await db.scalar(select(Project).where(Project.id == source.project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        await assert_org_member(db, user.id, project.organization_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return source


@router.post("/audits", response_model=AuditJobPublic, status_code=status.HTTP_201_CREATED)
async def create_audit_endpoint(
    data: AuditJobCreate,
    user: CurrentUser,
    db: DbSession,
) -> AuditJob:
    try:
        job = await create_audit_job(db, data.video_source_id, user.id)
        await db.commit()
        await db.refresh(job)
        return job
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/audits/{job_id}", response_model=AuditJobPublic)
async def get_audit(
    job_id: UUID,
    user: CurrentUser,
    db: DbSession,
) -> AuditJob:
    from app.services.video_service import assert_org_member

    job = await db.scalar(select(AuditJob).where(AuditJob.id == job_id))
    if not job:
        raise HTTPException(status_code=404, detail="Audit job not found")
    source = await db.scalar(select(VideoSource).where(VideoSource.id == job.video_source_id))
    if not source:
        raise HTTPException(status_code=404, detail="Video source not found")
    project = await db.scalar(select(Project).where(Project.id == source.project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        await assert_org_member(db, user.id, project.organization_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return job


@router.get("/audits/{job_id}/result", response_model=dict)
async def get_audit_result(
    job_id: UUID,
    user: CurrentUser,
    db: DbSession,
) -> dict:
    from sqlalchemy.orm import selectinload
    from app.models.audit import AuditResult
    from app.services.video_service import assert_org_member

    job = await db.scalar(select(AuditJob).where(AuditJob.id == job_id))
    if not job:
        raise HTTPException(status_code=404, detail="Audit job not found")
    source = await db.scalar(select(VideoSource).where(VideoSource.id == job.video_source_id))
    if not source:
        raise HTTPException(status_code=404, detail="Video source not found")
    project = await db.scalar(select(Project).where(Project.id == source.project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        await assert_org_member(db, user.id, project.organization_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    result = await db.scalar(
        select(AuditResult)
        .where(AuditResult.audit_job_id == job_id)
        .options(
            selectinload(AuditResult.findings),
            selectinload(AuditResult.seo_recommendations),
            selectinload(AuditResult.action_items),
        )
    )
    if not result:
        raise HTTPException(status_code=404, detail="Audit result not ready yet")

    return {
        "job": {
            "id": str(job.id),
            "status": job.status,
            "progress_percent": job.progress_percent,
            "current_stage": job.current_stage,
            "error_message": job.error_message,
        },
        "result": {
            "id": str(result.id),
            "executive_summary": result.executive_summary,
            "confidence_notes": result.confidence_notes,
            "generated_at": result.generated_at.isoformat() if result.generated_at else None,
            "model_info": result.model_info,
            "findings": [
                {
                    "id": str(f.id),
                    "category": f.category,
                    "severity": f.severity,
                    "title": f.title,
                    "explanation": getattr(f, "description", None),
                    "recommendation": None,
                    "confidence": f.confidence,
                    "requires_human_review": getattr(f, "is_ai_hypothesis", False),
                }
                for f in result.findings
            ],
            "seo_recommendations": [
                {
                    "id": str(s.id),
                    "field": s.field,
                    "original_value": s.original_value,
                    "proposed_value": s.proposed_value,
                    "explanation": s.explanation,
                    "confidence": s.confidence,
                    "is_ai_hypothesis": s.is_ai_hypothesis,
                    "status": s.status,
                }
                for s in result.seo_recommendations
            ],
            "action_items": [
                {
                    "id": str(a.id),
                    "title": a.title,
                    "description": a.description,
                    "priority": a.priority,
                    "status": a.status,
                }
                for a in result.action_items
            ],
        },
    }


@router.get("/audits/{job_id}/report.html")
async def export_audit_html(
    job_id: UUID,
    user: CurrentUser,
    db: DbSession,
):
    from fastapi.responses import HTMLResponse
    from app.services.reporting import generate_report_html
    from app.services.video_service import assert_org_member

    job = await db.scalar(select(AuditJob).where(AuditJob.id == job_id))
    if not job:
        raise HTTPException(status_code=404, detail="Audit job not found")
    source = await db.scalar(select(VideoSource).where(VideoSource.id == job.video_source_id))
    if not source:
        raise HTTPException(status_code=404, detail="Video source not found")
    project = await db.scalar(select(Project).where(Project.id == source.project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        await assert_org_member(db, user.id, project.organization_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    try:
        html = await generate_report_html(db, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return HTMLResponse(content=html)


@router.get("/audits/{job_id}/report.pdf")
async def export_audit_pdf(
    job_id: UUID,
    user: CurrentUser,
    db: DbSession,
):
    from fastapi.responses import Response
    from app.services.pdf_report import generate_report_pdf
    from app.services.video_service import assert_org_member

    job = await db.scalar(select(AuditJob).where(AuditJob.id == job_id))
    if not job:
        raise HTTPException(status_code=404, detail="Audit job not found")
    source = await db.scalar(select(VideoSource).where(VideoSource.id == job.video_source_id))
    if not source:
        raise HTTPException(status_code=404, detail="Video source not found")
    project = await db.scalar(select(Project).where(Project.id == source.project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        await assert_org_member(db, user.id, project.organization_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    try:
        pdf_bytes = await generate_report_pdf(db, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="audit-{job_id}.pdf"'},
    )
