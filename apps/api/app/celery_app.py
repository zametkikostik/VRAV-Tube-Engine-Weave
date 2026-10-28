"""Celery application and audit task."""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "vrav_tube_engine",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(name="health.ping")
def ping() -> str:
    return "pong"


@celery_app.task(name="audit.run", bind=True, max_retries=2)
def run_audit_task(self, job_id: str) -> dict:
    """Run audit pipeline in worker process (sync DB session)."""
    import asyncio
    from uuid import UUID

    from app.db.session import AsyncSessionLocal
    from app.services.audit_pipeline import run_audit_analysis

    async def _run() -> dict:
        async with AsyncSessionLocal() as db:
            try:
                result = await run_audit_analysis(db, UUID(job_id))
                await db.commit()
                return {"status": "SUCCEEDED", "result_id": str(result.id)}
            except Exception as exc:
                await db.rollback()
                return {"status": "FAILED", "error": str(exc)}

    return asyncio.run(_run())
