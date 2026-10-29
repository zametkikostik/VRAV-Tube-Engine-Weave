"""HTML report generation for audit results."""

from datetime import datetime, timezone
from html import escape
from typing import Any, Optional
from uuid import UUID


def _sev_color(severity: str) -> str:
    return {
        "CRITICAL": "#b91c1c",
        "HIGH": "#dc2626",
        "MEDIUM": "#d97706",
        "LOW": "#64748b",
        "UNDETERMINED": "#94a3b8",
    }.get(severity.upper(), "#94a3b8")


def render_audit_html(
    *,
    result: Any,
    job: Any,
    brand_name: str = "VRAV Tube Engine",
    logo_url: Optional[str] = None,
    accent: str = "#0ea5e9",
) -> str:
    findings_html = ""
    for f in getattr(result, "findings", None) or []:
        explanation = getattr(f, "description", None) or getattr(f, "explanation", None) or ""
        findings_html += f"""
        <div class="card">
          <div class="row">
            <strong>{escape(f.title)}</strong>
            <span class="badge" style="background:{_sev_color(f.severity)}">{escape(f.severity)}</span>
          </div>
          <p class="muted">{escape(explanation)}</p>
        </div>
        """

    seo_html = ""
    for s in getattr(result, "seo_recommendations", None) or []:
        seo_html += f"""
        <div class="card">
          <div class="field">{escape(s.field)}</div>
          <p>{escape(s.proposed_value or "")}</p>
          <p class="muted">{escape(s.explanation or "")}</p>
        </div>
        """

    actions_html = ""
    for a in getattr(result, "action_items", None) or []:
        actions_html += f"""
        <li><strong>P{a.priority}</strong> — {escape(a.title)}
          <span class="muted">{escape(a.description or "")}</span></li>
        """

    generated_at = getattr(result, "generated_at", None)
    generated = (
        generated_at.strftime("%Y-%m-%d %H:%M UTC")
        if generated_at
        else datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    )
    logo = f'<img src="{escape(logo_url)}" alt="" class="logo"/>' if logo_url else ""
    summary = escape(getattr(result, "executive_summary", None) or "—")
    notes = escape(getattr(result, "confidence_notes", None) or "")
    job_id = escape(str(getattr(job, "id", ""))[:8])
    job_status = escape(str(getattr(job, "status", "")))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>{escape(brand_name)} — Audit Report</title>
  <style>
    body {{ font-family: system-ui, sans-serif; background:#0f172a; color:#e2e8f0; margin:0; padding:2rem; }}
    .wrap {{ max-width:800px; margin:0 auto; }}
    h1 {{ color:#fff; font-size:1.5rem; }}
    h2 {{ color:#f1f5f9; margin-top:2rem; font-size:1.15rem; border-bottom:1px solid #334155; padding-bottom:.4rem; }}
    .card {{ background:#1e293b; border:1px solid #334155; border-radius:10px; padding:1rem; margin:.75rem 0; }}
    .row {{ display:flex; justify-content:space-between; gap:1rem; align-items:start; }}
    .badge {{ font-size:.7rem; padding:.2rem .5rem; border-radius:4px; color:#fff; white-space:nowrap; }}
    .muted {{ color:#94a3b8; font-size:.9rem; }}
    .field {{ text-transform:uppercase; font-size:.7rem; color:#64748b; letter-spacing:.05em; }}
    .logo {{ height:32px; margin-bottom:1rem; }}
    .disclaimer {{ font-size:.75rem; color:#64748b; margin-top:2.5rem; border-top:1px solid #334155; padding-top:1rem; }}
    ul {{ padding-left:1.2rem; }}
    li {{ margin:.4rem 0; }}
  </style>
</head>
<body>
  <div class="wrap">
    {logo}
    <h1>{escape(brand_name)} — Audit Report</h1>
    <p class="muted">Generated {escape(generated)} · Job {job_id}… · Status {job_status}</p>
    <h2>Executive summary</h2>
    <div class="card"><p>{summary}</p><p class="muted">{notes}</p></div>
    <h2>Findings</h2>
    {findings_html or '<p class="muted">No findings</p>'}
    <h2>SEO recommendations</h2>
    {seo_html or '<p class="muted">No SEO recommendations</p>'}
    <h2>Action plan</h2>
    <ul>{actions_html or '<li class="muted">No actions</li>'}</ul>
    <p class="disclaimer">
      This report is an advisory risk assessment. It does not establish YouTube monetization status,
      guarantee monetization approval or replace professional legal advice.
      Not affiliated with YouTube or Google.
    </p>
  </div>
</body>
</html>
"""


async def generate_report_html(db: Any, job_id: UUID) -> str:
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
    return render_audit_html(result=result, job=job)
