"""Payment webhook endpoints — verified + idempotent DB processing."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import DbSession
from app.services.payments import get_payment_provider
from app.services.webhook_processor import process_verified_webhook

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(request: Request, db: DbSession) -> dict[str, Any]:
    payload = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    try:
        provider = get_payment_provider("stripe")
        event = await provider.verify_webhook(payload, headers)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    result = await process_verified_webhook(db, event)
    await db.commit()
    return result


@router.post("/yookassa")
async def yookassa_webhook(request: Request, db: DbSession) -> dict[str, Any]:
    payload = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    try:
        provider = get_payment_provider("yookassa")
        event = await provider.verify_webhook(payload, headers)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    result = await process_verified_webhook(db, event)
    await db.commit()
    return result
