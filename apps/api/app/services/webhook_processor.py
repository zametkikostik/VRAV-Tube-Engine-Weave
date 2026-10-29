"""Idempotent payment webhook processing with DB persistence."""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import (
    PaymentTransaction,
    PaymentWebhookEvent,
    Subscription,
    SubscriptionPlan,
)
from app.services.entitlements import PLAN_LIMITS
from app.services.payments.base import WebhookEvent


async def process_verified_webhook(
    db: AsyncSession,
    event: WebhookEvent,
    *,
    organization_id: Optional[UUID] = None,
) -> dict[str, Any]:
    if not event.verified:
        return {
            "status": "rejected",
            "reason": "webhook not verified — entitlements not granted",
        }

    existing = await db.scalar(
        select(PaymentWebhookEvent).where(PaymentWebhookEvent.event_id == event.event_id)
    )
    if existing:
        return {
            "status": "duplicate",
            "event_id": event.event_id,
            "previous_result": existing.processing_result,
        }

    row = PaymentWebhookEvent(
        provider=event.provider,
        event_id=event.event_id or f"{event.provider}:{datetime.now(timezone.utc).timestamp()}",
        event_type=event.event_type,
        payload=event.payload,
        processing_result="received",
        processed_at=datetime.now(timezone.utc),
    )
    db.add(row)
    await db.flush()

    result = await _apply_event(db, event, organization_id=organization_id)
    row.processing_result = result.get("status", "processed")
    await db.flush()
    return result


async def _apply_event(
    db: AsyncSession,
    event: WebhookEvent,
    *,
    organization_id: Optional[UUID],
) -> dict[str, Any]:
    et = event.event_type or ""

    if event.provider == "stripe":
        if et in (
            "checkout.session.completed",
            "invoice.paid",
            "customer.subscription.updated",
        ):
            return await _activate_from_stripe(db, event, organization_id)
        if et in ("customer.subscription.deleted",):
            return await _mark_subscription_status(db, event, "CANCELLED")
        if et in ("invoice.payment_failed",):
            return await _mark_subscription_status(db, event, "PAST_DUE")
        return {"status": "ignored", "event_type": et}

    if event.provider == "yookassa":
        if et in ("payment.succeeded",):
            return await _activate_from_yookassa(db, event, organization_id)
        if et in ("payment.canceled",):
            return await _mark_subscription_status(db, event, "CANCELLED")
        return {"status": "ignored", "event_type": et}

    return {"status": "ignored", "event_type": et, "note": "no handler for this event type"}


async def _ensure_plan(db: AsyncSession, code: str) -> SubscriptionPlan:
    plan = await db.scalar(select(SubscriptionPlan).where(SubscriptionPlan.code == code))
    if plan:
        return plan
    limits = PLAN_LIMITS.get(code, PLAN_LIMITS.get("personal", {}))
    plan = SubscriptionPlan(code=code, name=code.title(), limits_json=dict(limits), is_active=True)
    db.add(plan)
    await db.flush()
    return plan


async def _activate_from_stripe(
    db: AsyncSession,
    event: WebhookEvent,
    organization_id: Optional[UUID],
) -> dict[str, Any]:
    data = event.payload.get("data", {}).get("object", {}) if isinstance(event.payload, dict) else {}
    meta = data.get("metadata") or {}
    org_str = meta.get("organization_id") or (str(organization_id) if organization_id else None)
    plan_code = meta.get("plan_code") or "professional"
    external_id = data.get("id") or data.get("subscription") or event.event_id

    if not org_str:
        return {
            "status": "needs_metadata",
            "note": "organization_id missing in session metadata",
        }

    org_id = UUID(org_str)
    plan = await _ensure_plan(db, plan_code)

    amount = int(data.get("amount_total") or data.get("amount") or 0)
    currency = (data.get("currency") or "usd").upper()

    db.add(
        PaymentTransaction(
            organization_id=org_id,
            provider="stripe",
            external_id=str(external_id),
            amount_cents=amount,
            currency=currency,
            status="SUCCEEDED",
            raw_payload=data if isinstance(data, dict) else None,
        )
    )

    sub = await db.scalar(
        select(Subscription).where(
            Subscription.organization_id == org_id,
            Subscription.provider == "stripe",
            Subscription.status.in_(["ACTIVE", "PAST_DUE", "PENDING"]),
        )
    )
    now = datetime.now(timezone.utc)
    if sub:
        sub.status = "ACTIVE"
        sub.plan_id = plan.id
        sub.external_subscription_id = str(data.get("subscription") or external_id)
    else:
        sub = Subscription(
            organization_id=org_id,
            plan_id=plan.id,
            status="ACTIVE",
            current_period_start=now,
            provider="stripe",
            external_subscription_id=str(data.get("subscription") or external_id),
        )
        db.add(sub)
    await db.flush()
    return {"status": "activated", "organization_id": str(org_id), "plan": plan_code}


async def _activate_from_yookassa(
    db: AsyncSession,
    event: WebhookEvent,
    organization_id: Optional[UUID],
) -> dict[str, Any]:
    obj = event.payload.get("object") or {}
    meta = obj.get("metadata") or {}
    org_str = meta.get("organization_id") or (str(organization_id) if organization_id else None)
    plan_code = meta.get("plan_code") or "professional"
    if not org_str:
        return {"status": "needs_metadata", "note": "organization_id missing in payment metadata"}

    org_id = UUID(org_str)
    plan = await _ensure_plan(db, plan_code)
    amount_obj = obj.get("amount") or {}
    value = amount_obj.get("value") or "0"
    try:
        amount_cents = int(float(value) * 100)
    except ValueError:
        amount_cents = 0
    currency = (amount_obj.get("currency") or "RUB").upper()

    db.add(
        PaymentTransaction(
            organization_id=org_id,
            provider="yookassa",
            external_id=str(obj.get("id") or event.event_id),
            amount_cents=amount_cents,
            currency=currency,
            status="SUCCEEDED",
            raw_payload=obj if isinstance(obj, dict) else None,
        )
    )
    now = datetime.now(timezone.utc)
    sub = Subscription(
        organization_id=org_id,
        plan_id=plan.id,
        status="ACTIVE",
        current_period_start=now,
        provider="yookassa",
        external_subscription_id=str(obj.get("id") or event.event_id),
    )
    db.add(sub)
    await db.flush()
    return {"status": "activated", "organization_id": str(org_id), "plan": plan_code}


async def _mark_subscription_status(
    db: AsyncSession,
    event: WebhookEvent,
    status: str,
) -> dict[str, Any]:
    data = event.payload.get("data", {}).get("object", {}) if isinstance(event.payload, dict) else {}
    if not data and event.provider == "yookassa":
        data = event.payload.get("object") or {}
    ext_id = str(data.get("id") or data.get("subscription") or "")
    if not ext_id:
        return {"status": "ignored", "reason": "no external id"}
    sub = await db.scalar(
        select(Subscription).where(Subscription.external_subscription_id == ext_id)
    )
    if not sub:
        return {"status": "not_found", "external_id": ext_id}
    sub.status = status
    await db.flush()
    return {"status": "updated", "subscription_status": status, "external_id": ext_id}
