"""Organization and tenant endpoints with isolation checks."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession, require_org_member
from app.models.organization import Organization, OrganizationMember
from app.models.tenant import Tenant
from app.schemas.organization import (
    MemberPublic,
    OrganizationPublic,
    TenantPublic,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("/me", response_model=list[OrganizationPublic])
async def list_my_organizations(user: CurrentUser, db: DbSession) -> list[Organization]:
    result = await db.scalars(
        select(Organization)
        .join(OrganizationMember)
        .where(OrganizationMember.user_id == user.id, Organization.is_active.is_(True))
        .options(selectinload(Organization.members))
    )
    return list(result.all())


@router.get("/{organization_id}", response_model=OrganizationPublic)
async def get_organization(
    organization_id: UUID,
    user: CurrentUser,
    db: DbSession,
    _member: Annotated[OrganizationMember, Depends(require_org_member)],
) -> Organization:
    org = await db.scalar(select(Organization).where(Organization.id == organization_id))
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


@router.get("/{organization_id}/members", response_model=list[MemberPublic])
async def list_members(
    organization_id: UUID,
    user: CurrentUser,
    db: DbSession,
    _member: Annotated[OrganizationMember, Depends(require_org_member)],
) -> list[OrganizationMember]:
    result = await db.scalars(
        select(OrganizationMember).where(OrganizationMember.organization_id == organization_id)
    )
    return list(result.all())


@router.get("/{organization_id}/tenants", response_model=list[TenantPublic])
async def list_tenants(
    organization_id: UUID,
    user: CurrentUser,
    db: DbSession,
    _member: Annotated[OrganizationMember, Depends(require_org_member)],
) -> list[Tenant]:
    result = await db.scalars(
        select(Tenant).where(
            Tenant.organization_id == organization_id,
            Tenant.is_active.is_(True),
        )
    )
    return list(result.all())
