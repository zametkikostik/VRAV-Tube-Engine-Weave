"""Health and readiness endpoints."""

from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from sqlalchemy import text

from app.db.session import AsyncSessionLocal

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    service: str
    database: str | None = None


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version="0.1.0", service="vrav-tube-engine-api")


@router.get("/ready", response_model=HealthResponse)
async def ready(response: Response) -> HealthResponse:
    db_status = "unknown"
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:
        db_status = f"error: {type(exc).__name__}"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(
            status="not_ready",
            version="0.1.0",
            service="vrav-tube-engine-api",
            database=db_status,
        )
    return HealthResponse(
        status="ready",
        version="0.1.0",
        service="vrav-tube-engine-api",
        database=db_status,
    )
