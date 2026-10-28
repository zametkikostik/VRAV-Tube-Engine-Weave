"""Platform admin endpoints — superuser only."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models.audit import AuditJob
from app.models.billing import Subscription
from app.models.contact import ContactLead
from app.models.organization import Organization
from app.models.user import User
from app.models.usage import AIUsageRecord

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_superuser(user: CurrentUser) -> None:
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser required")


class AdminStats(BaseModel):
    users: int
    organizations: int
    audit_jobs: int
    active_subscriptions: int
    contact_leads_new: int
    ai_usage_records: int


class UserRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    preferred_locale: str
    created_at: Optional[datetime] = None


class OrgRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    created_at: Optional[datetime] = None


@router.get("/stats", response_model=AdminStats)
async def admin_stats(user: CurrentUser, db: DbSession) -> AdminStats:
    _require_superuser(user)
    users = await db.scalar(select(func.count()).select_from(User)) or 0
    orgs = await db.scalar(select(func.count()).select_from(Organization)) or 0
    jobs = await db.scalar(select(func.count()).select_from(AuditJob)) or 0
    subs = (
        await db.scalar(
            select(func.count()).select_from(Subscription).where(Subscription.status == "ACTIVE")
        )
        or 0
    )
    leads = (
        await db.scalar(
            select(func.count()).select_from(ContactLead).where(ContactLead.status == "NEW")
        )
        or 0
    )
    usage = await db.scalar(select(func.count()).select_from(AIUsageRecord)) or 0
    return AdminStats(
        users=users,
        organizations=orgs,
        audit_jobs=jobs,
        active_subscriptions=subs,
        contact_leads_new=leads,
        ai_usage_records=usage,
    )


@router.get("/users", response_model=list[UserRow])
async def admin_users(user: CurrentUser, db: DbSession) -> list[User]:
    _require_superuser(user)
    rows = await db.scalars(select(User).order_by(User.created_at.desc()).limit(100)
    )
    return list(rows.all())


@router.get("/organizations", response_model=list[OrgRow])
async def admin_orgs(user: CurrentUser, db: DbSession) -> list[Organization]:
    _require_superuser(user)
    rows = await db.scalars(select(Organization).order_by(Organization.created_at.desc()).limit(100))
    return list(rows.all())


class SuperuserToggle(BaseModel):
    is_superuser: bool


@router.patch("/users/{user_id}/superuser")
async def set_superuser(
    user_id: UUID,
    data: SuperuserToggle,
    user: CurrentUser,
    db: DbSession,
) -> dict:
    _require_superuser(user)
    if user_id == user.id and not data.is_superuser:
        raise HTTPException(status_code=400, detail="Cannot remove your own superuser flag")
    target = await db.scalar(select(User).where(User.id == user_id))
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.is_superuser = data.is_superuser
    await db.commit()
    return {"id": str(target.id), "is_superuser": target.is_superuser}
