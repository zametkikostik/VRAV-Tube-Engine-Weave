"""Billing endpoints — checkout session creation (provider-backed)."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.billing import SubscriptionPlan
from app.models.organization import OrganizationMember
from app.services.entitlements import PLAN_LIMITS, get_organization_entitlements
from app.services.payments import get_payment_provider
from app.services.video_service import assert_org_member

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    organization_id: UUID
    plan_code: str = Field(pattern="^(personal|professional|agency|enterprise)$")
    provider: str = Field(pattern="^(stripe|yookassa)$")
    currency: str = "usd"
    amount_cents: int = Field(gt=0)
    success_url: str
    cancel_url: str
    interval: str = "month"


class EntitlementsResponse(BaseModel):
    plan_code: str
    subscription_status: str
    limits: dict


@router.get("/entitlements/{organization_id}", response_model=EntitlementsResponse)
async def get_ents(
    organization_id: UUID,
    user: CurrentUser,
    db: DbSession,
) -> EntitlementsResponse:
    try:
        await assert_org_member(db, user.id, organization_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    ents = await get_organization_entitlements(db, organization_id)
    return EntitlementsResponse(
        plan_code=ents.plan_code,
        subscription_status=ents.subscription_status,
        limits=ents.limits,
    )


@router.post("/checkout")
async def create_checkout(
    data: CheckoutRequest,
    user: CurrentUser,
    db: DbSession,
):
    try:
        await assert_org_member(db, user.id, data.organization_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    member = await db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == data.organization_id,
            OrganizationMember.user_id == user.id,
        )
    )
    if not member or member.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Only owner/admin can start checkout")

    plan = await db.scalar(select(SubscriptionPlan).where(SubscriptionPlan.code == data.plan_code))
    if not plan:
        plan = SubscriptionPlan(
            code=data.plan_code,
            name=data.plan_code.title(),
            limits_json=dict(PLAN_LIMITS.get(data.plan_code, {})),
            is_active=True,
        )
        db.add(plan)
        await db.flush()

    try:
        provider = get_payment_provider(data.provider)
        session = await provider.create_checkout_session(
            amount_cents=data.amount_cents,
            currency=data.currency,
            customer_email=user.email,
            success_url=data.success_url,
            cancel_url=data.cancel_url,
            metadata={
                "organization_id": str(data.organization_id),
                "plan_code": data.plan_code,
            },
            subscription=True,
            interval=data.interval,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    await db.commit()
    return {
        "provider": session.provider,
        "session_id": session.session_id,
        "checkout_url": session.checkout_url,
        "note": "Entitlements activate only after verified webhook, not success URL.",
    }
