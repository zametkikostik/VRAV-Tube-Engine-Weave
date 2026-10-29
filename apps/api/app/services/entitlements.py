"""Subscription / plan entitlement checks (server-side)."""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

DEFAULT_LIMITS: dict[str, Any] = {
    "audits_per_month": 5,
    "concurrent_jobs": 1,
    "ai_budget_usd": 1.0,
    "white_label": False,
    "pdf_export": True,
    "html_export": True,
}

PLAN_LIMITS: dict[str, dict[str, Any]] = {
    "personal": {
        "audits_per_month": 20,
        "concurrent_jobs": 2,
        "ai_budget_usd": 10.0,
        "white_label": False,
        "pdf_export": True,
        "html_export": True,
    },
    "professional": {
        "audits_per_month": 100,
        "concurrent_jobs": 5,
        "ai_budget_usd": 50.0,
        "white_label": False,
        "pdf_export": True,
        "html_export": True,
    },
    "agency": {
        "audits_per_month": 500,
        "concurrent_jobs": 20,
        "ai_budget_usd": 200.0,
        "white_label": True,
        "pdf_export": True,
        "html_export": True,
    },
    "enterprise": {
        "audits_per_month": 10_000,
        "concurrent_jobs": 100,
        "ai_budget_usd": 1000.0,
        "white_label": True,
        "pdf_export": True,
        "html_export": True,
    },
}


@dataclass
class Entitlements:
    plan_code: str = "free"
    limits: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_LIMITS))
    subscription_status: str = "NONE"

    def allows(self, feature: str) -> bool:
        return bool(self.limits.get(feature, False))

    def limit(self, key: str, default: int = 0) -> int:
        val = self.limits.get(key, default)
        try:
            return int(val)
        except (TypeError, ValueError):
            return default


async def get_organization_entitlements(db: Any, organization_id: UUID) -> Entitlements:
    try:
        from sqlalchemy import select
        from app.models.billing import Subscription, SubscriptionPlan

        sub = await db.scalar(
            select(Subscription)
            .where(
                Subscription.organization_id == organization_id,
                Subscription.status.in_(["ACTIVE", "PAST_DUE"]),
            )
            .order_by(Subscription.created_at.desc())
        )
        if sub:
            plan = await db.scalar(
                select(SubscriptionPlan).where(SubscriptionPlan.id == sub.plan_id)
            )
            code = plan.code if plan else "professional"
            limits = dict(PLAN_LIMITS.get(code, DEFAULT_LIMITS))
            if plan and plan.limits_json:
                limits.update(plan.limits_json)
            return Entitlements(
                plan_code=code,
                limits=limits,
                subscription_status=sub.status,
            )
    except Exception:
        pass
    return Entitlements()


async def assert_can_start_audit(db: Any, organization_id: UUID) -> Entitlements:
    """Allow free-tier limited audits; raise ValueError only on hard plan blocks."""
    return await get_organization_entitlements(db, organization_id)


async def check_entitlement(
    db: Any,
    organization_id: UUID,
    feature: str = "audit",
) -> Entitlements:
    ents = await get_organization_entitlements(db, organization_id)
    if feature == "white_label" and not ents.allows("white_label"):
        raise ValueError("White-label requires Agency plan or higher")
    if feature == "pdf_export" and not ents.allows("pdf_export"):
        raise ValueError("PDF export not available on current plan")
    return ents
