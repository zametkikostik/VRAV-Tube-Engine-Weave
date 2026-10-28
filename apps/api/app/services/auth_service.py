"""Authentication and registration service."""

import re
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.organization import MemberRole, Organization, OrganizationMember
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import TokenResponse, UserRegister


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s\-]", "", text)
    text = re.sub(r"[\s\-]+", "-", text)
    return text[:80].strip("-") or "org"


async def register_user(db: AsyncSession, data: UserRegister) -> tuple[User, Organization, Tenant]:
    """Register a new user, create personal organization and default tenant."""
    existing = await db.scalar(select(User).where(User.email == data.email.lower()))
    if existing:
        raise ValueError("Email already registered")

    user = User(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        preferred_locale=data.preferred_locale,
        is_active=True,
        is_email_verified=False,
    )
    db.add(user)
    await db.flush()

    org_name = data.organization_name or (data.full_name or data.email.split("@")[0])
    base_slug = _slugify(org_name)
    slug = base_slug
    counter = 1
    while await db.scalar(select(Organization).where(Organization.slug == slug)):
        slug = f"{base_slug}-{counter}"
        counter += 1

    org = Organization(
        name=org_name,
        slug=slug,
        owner_user_id=user.id,
        billing_email=user.email,
    )
    db.add(org)
    await db.flush()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role=MemberRole.OWNER,
        accepted_at=datetime.now(timezone.utc),
    )
    db.add(member)

    tenant_slug = f"{slug}-default"
    tenant = Tenant(
        organization_id=org.id,
        name=f"{org_name} Workspace",
        slug=tenant_slug,
        is_platform_tenant=False,
    )
    db.add(tenant)
    await db.flush()

    return user, org, tenant


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    user = await db.scalar(select(User).where(User.email == email.lower()))
    if not user or not user.password_hash:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active or user.deleted_at is not None:
        return None
    user.last_login_at = datetime.now(timezone.utc)
    return user


def issue_tokens(user: User) -> TokenResponse:
    from app.core.config import get_settings

    settings = get_settings()
    access = create_access_token(
        user.id,
        extra_claims={"email": user.email, "locale": user.preferred_locale},
    )
    refresh = create_refresh_token(user.id)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    return await db.scalar(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
