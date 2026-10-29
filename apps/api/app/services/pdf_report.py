"""PDF report generation for audit results (ReportLab)."""

from io import BytesIO
from typing import Any


def render_audit_pdf(*, result: Any, job: Any, brand_name: str = "VRAV Tube Engine") -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except ImportError as exc:
        raise RuntimeError("PDF export requires reportlab: pip install reportlab") from exc

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="H1Custom", parent=styles["Heading1"], fontSize=16))
    styles.add(ParagraphStyle(name="H2Custom", parent=styles["Heading2"], fontSize=12, spaceBefore=12))
    styles.add(ParagraphStyle(name="BodyDark", parent=styles["BodyText"], fontSize=10, leading=14))

    story = []
    story.append(Paragraph(_esc(brand_name) + " — Audit Report", styles["H1Custom"]))
    story.append(Paragraph(f"Job {_esc(str(getattr(job, 'id', ''))[:8])} · {_esc(str(getattr(job, 'status', '')))}", styles["BodyDark"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Executive summary", styles["H2Custom"]))
    story.append(Paragraph(_esc(getattr(result, "executive_summary", None) or "—"), styles["BodyDark"]))
    notes = getattr(result, "confidence_notes", None)
    if notes:
        story.append(Paragraph(_esc(notes), styles["BodyDark"]))

    story.append(Paragraph("Findings", styles["H2Custom"]))
    for f in getattr(result, "findings", None) or []:
        story.append(Paragraph(f"<b>{_esc(f.title)}</b> [{_esc(f.severity)}]", styles["BodyDark"]))
        explanation = getattr(f, "description", None) or getattr(f, "explanation", None)
        if explanation:
            story.append(Paragraph(_esc(explanation), styles["BodyDark"]))
        story.append(Spacer(1, 4))

    story.append(Paragraph("SEO recommendations", styles["H2Custom"]))
    for s in getattr(result, "seo_recommendations", None) or []:
        story.append(
            Paragraph(f"<b>{_esc(s.field)}</b>: {_esc(s.proposed_value or '')}", styles["BodyDark"])
        )
        if s.explanation:
            story.append(Paragraph(_esc(s.explanation), styles["BodyDark"]))
        story.append(Spacer(1, 3))

    story.append(Paragraph("Action plan", styles["H2Custom"]))
    for a in getattr(result, "action_items", None) or []:
        story.append(
            Paragraph(
                f"P{a.priority} — {_esc(a.title)} {_esc(a.description or '')}",
                styles["BodyDark"],
            )
        )

    story.append(Spacer(1, 16))
    story.append(
        Paragraph(
            "This report is an advisory risk assessment. It does not establish YouTube "
            "monetization status, guarantee monetization approval or replace professional "
            "legal advice. Not affiliated with YouTube or Google.",
            styles["BodyDark"],
        )
    )

    doc.build(story)
    return buffer.getvalue()


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


async def generate_report_pdf(db: Any, job_id: Any) -> bytes:
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.audit import AuditJob, AuditResult

    job = await db.scalar(select(AuditJob).where(AuditJob.id == job_id))
    if not job:
        raise ValueError("Audit job not found")
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
        raise ValueError("Audit result not ready")
    return render_audit_pdf(result=result, job=job)
