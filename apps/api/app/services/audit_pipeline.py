"""Audit analysis pipeline — structured AI findings without fabricated metrics."""

import json
import re
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit import (
    ActionItem,
    AuditFinding,
    AuditJob,
    AuditResult,
    JobStatus,
    SeoRecommendation,
    Severity,
)
from app.models.video import Transcript, VideoMetadata, VideoSource
from app.services.ai.base import ChatMessage
from app.services.ai.gateway import get_ai_gateway


SYSTEM_PROMPT = """You are an expert YouTube content auditor for the VRAV Tube Engine platform.
Analyze the provided video metadata and optional transcript.
Return ONLY valid JSON matching this schema:
{
  "executive_summary": "2-4 sentence summary",
  "seo_recommendations": [
    {
      "field": "title|description|tags|chapters|hashtags|cta|thumbnail_concept",
      "original_value": "string or null",
      "proposed_value": "string",
      "explanation": "why this helps",
      "confidence": "high|medium|low",
      "is_ai_hypothesis": true
    }
  ],
  "findings": [
    {
      "category": "metadata|seo|content|policy|other",
      "severity": "LOW|MEDIUM|HIGH|CRITICAL|UNDETERMINED",
      "title": "short title",
      "explanation": "what was observed",
      "recommendation": "what to do",
      "confidence": "high|medium|low",
      "requires_human_review": true
    }
  ],
  "action_items": [{"title": "task", "description": "details", "priority": 1}],
  "confidence_notes": "limitations of this analysis"
}
Rules:
- Never invent search volume, rankings, CPM, or monetization status.
- Label uncertain items clearly.
- Do not claim official YouTube affiliation or guaranteed outcomes.
- If transcript is missing, note which analyses could not run.
"""


def _safe_json_parse(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


async def run_audit_analysis(db: AsyncSession, job_id: UUID) -> AuditResult:
    """Execute audit pipeline for a job. Updates job status in place."""
    job = await db.scalar(
        select(AuditJob)
        .where(AuditJob.id == job_id)
        .options(selectinload(AuditJob.video_source))
    )
    if not job:
        raise ValueError("Audit job not found")

    job.status = JobStatus.RUNNING
    job.started_at = datetime.now(timezone.utc)
    job.progress_percent = 10
    job.current_stage = "loading_source"
    await db.flush()

    source = await db.scalar(select(VideoSource).where(VideoSource.id == job.video_source_id))
    if not source:
        job.status = JobStatus.FAILED
        job.error_message = "Video source not found"
        job.finished_at = datetime.now(timezone.utc)
        await db.flush()
        raise ValueError(job.error_message)

    meta = await db.scalar(select(VideoMetadata).where(VideoMetadata.video_source_id == source.id))
    transcript = await db.scalar(
        select(Transcript)
        .where(Transcript.video_source_id == source.id)
        .order_by(Transcript.created_at.desc())
    )

    job.progress_percent = 30
    job.current_stage = "ai_analysis"
    await db.flush()

    context_parts = [
        f"Source type: {source.source_type}",
        f"YouTube ID: {source.youtube_video_id or 'n/a'}",
        f"URL: {source.original_url or 'n/a'}",
        f"Language: {source.language_code or 'unknown'}",
    ]
    if meta:
        context_parts.append(f"Title: {meta.title or '(empty)'}")
        context_parts.append(f"Description: {(meta.description or '')[:2000]}")
        if meta.tags:
            context_parts.append(f"Tags: {meta.tags}")
    else:
        context_parts.append("Metadata: not provided")

    if transcript:
        context_parts.append(f"Transcript (truncated):\n{transcript.content_text[:12000]}")
    else:
        context_parts.append("Transcript: NOT AVAILABLE. Content-depth analysis is limited.")

    user_msg = (
        "Analyze this YouTube video context and produce the JSON audit report.\n"
        + "\n".join(context_parts)
    )

    gateway = get_ai_gateway()
    model_info: dict[str, Any] = {"providers_tried": gateway.available_providers}

    try:
        if not gateway.available_providers:
            parsed = _offline_analysis(source, meta, transcript)
            model_info["mode"] = "offline_structural"
        else:
            response = await gateway.chat(
                [
                    ChatMessage(role="system", content=SYSTEM_PROMPT),
                    ChatMessage(role="user", content=user_msg),
                ],
                task="seo_audit",
                temperature=0.2,
                max_tokens=4096,
            )
            model_info.update(
                {
                    "provider": response.provider,
                    "model": response.model,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                }
            )
            try:
                from app.models.usage import AIUsageRecord
                from app.models.video import Project

                project = await db.scalar(select(Project).where(Project.id == source.project_id))
                if project:
                    db.add(
                        AIUsageRecord(
                            tenant_id=job.tenant_id,
                            organization_id=project.organization_id,
                            audit_job_id=job.id,
                            provider=response.provider,
                            model=response.model,
                            prompt_tokens=response.usage.prompt_tokens,
                            completion_tokens=response.usage.completion_tokens,
                            provider_reported_cost=response.usage.provider_reported_cost,
                            currency=response.usage.currency or "USD",
                            request_outcome="success",
                        )
                    )
            except Exception:
                pass
            try:
                parsed = _safe_json_parse(response.content)
            except json.JSONDecodeError:
                parsed = {
                    "executive_summary": response.content[:2000],
                    "seo_recommendations": [],
                    "findings": [
                        {
                            "category": "other",
                            "severity": "UNDETERMINED",
                            "title": "AI returned non-JSON output",
                            "explanation": "Structured parse failed; raw text stored in summary.",
                            "confidence": "low",
                            "requires_human_review": True,
                        }
                    ],
                    "action_items": [],
                    "confidence_notes": "JSON parse failure",
                }

        job.progress_percent = 70
        job.current_stage = "persisting"
        await db.flush()

        result = AuditResult(
            audit_job_id=job.id,
            executive_summary=parsed.get("executive_summary"),
            confidence_notes=parsed.get("confidence_notes"),
            generated_at=datetime.now(timezone.utc),
            model_info=model_info,
            raw_ai_response=parsed,
        )
        db.add(result)
        await db.flush()

        for rec in parsed.get("seo_recommendations") or []:
            db.add(
                SeoRecommendation(
                    audit_result_id=result.id,
                    field=str(rec.get("field") or "title")[:64],
                    original_value=rec.get("original_value"),
                    proposed_value=rec.get("proposed_value"),
                    explanation=rec.get("explanation"),
                    confidence=rec.get("confidence"),
                    is_ai_hypothesis=bool(rec.get("is_ai_hypothesis", True)),
                    status="pending",
                )
            )

        for finding in parsed.get("findings") or []:
            sev = str(finding.get("severity") or "UNDETERMINED").upper()
            if sev not in {s.value for s in Severity}:
                sev = Severity.UNDETERMINED.value
            db.add(
                AuditFinding(
                    audit_result_id=result.id,
                    category=str(finding.get("category") or "other")[:64],
                    severity=sev,
                    title=str(finding.get("title") or "Finding")[:500],
                    description=finding.get("explanation"),
                    confidence=finding.get("confidence"),
                    is_ai_hypothesis=bool(finding.get("requires_human_review", True)),
                    status="open",
                )
            )

        for i, item in enumerate(parsed.get("action_items") or []):
            db.add(
                ActionItem(
                    audit_result_id=result.id,
                    title=str(item.get("title") or f"Action {i+1}")[:500],
                    description=item.get("description"),
                    priority=int(item.get("priority") or 3),
                    status="pending",
                )
            )

        job.status = JobStatus.SUCCEEDED
        job.progress_percent = 100
        job.current_stage = "done"
        job.finished_at = datetime.now(timezone.utc)
        await db.flush()
        return result

    except Exception as exc:
        job.status = JobStatus.FAILED
        job.error_message = str(exc)[:2000]
        job.finished_at = datetime.now(timezone.utc)
        job.current_stage = "failed"
        await db.flush()
        raise


def _offline_analysis(
    source: VideoSource,
    meta: Optional[VideoMetadata],
    transcript: Optional[Transcript],
) -> dict[str, Any]:
    findings = []
    seo = []
    actions = []
    title = meta.title if meta else None
    description = meta.description if meta else None

    if not title:
        findings.append(
            {
                "category": "metadata",
                "severity": "HIGH",
                "title": "Missing title",
                "explanation": "No title was provided for this video source.",
                "confidence": "high",
                "requires_human_review": False,
            }
        )
        actions.append({"title": "Add video title", "description": "Provide a descriptive title.", "priority": 1})
    else:
        if len(title) < 20:
            findings.append(
                {
                    "category": "seo",
                    "severity": "MEDIUM",
                    "title": "Title may be too short",
                    "explanation": f"Title length is {len(title)} characters.",
                    "confidence": "medium",
                    "requires_human_review": True,
                }
            )
        seo.append(
            {
                "field": "title",
                "original_value": title,
                "proposed_value": title,
                "explanation": "Offline mode — review manually.",
                "confidence": "low",
                "is_ai_hypothesis": True,
            }
        )

    if not description:
        findings.append(
            {
                "category": "metadata",
                "severity": "MEDIUM",
                "title": "Missing description",
                "explanation": "No description was provided.",
                "confidence": "high",
                "requires_human_review": False,
            }
        )

    if not transcript:
        findings.append(
            {
                "category": "content",
                "severity": "UNDETERMINED",
                "title": "No transcript available",
                "explanation": "Content analysis requires a transcript.",
                "confidence": "high",
                "requires_human_review": False,
            }
        )

    findings.append(
        {
            "category": "policy",
            "severity": "UNDETERMINED",
            "title": "Policy risk not fully assessed",
            "explanation": "Automated policy assessment requires AI and human review.",
            "confidence": "low",
            "requires_human_review": True,
        }
    )

    return {
        "executive_summary": (
            "Structural audit completed without an AI provider. "
            "Configure ROUTERAI_API_KEY or OPENROUTER_API_KEY for full AI analysis."
        ),
        "seo_recommendations": seo,
        "findings": findings,
        "action_items": actions,
        "confidence_notes": "Offline structural mode. Not an official YouTube assessment.",
    }
