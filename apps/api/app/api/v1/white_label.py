"""White-label settings API — tenant scoped."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.organization import OrganizationMember
from app.models.tenant import Tenant, WhiteLabelSettings
from app.services.video_service import assert_org_member

router = APIRouter(prefix="/tenants", tags=["white-label"])


class WhiteLabelUpdate(BaseModel):
    product_display_name: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=1024)
    favicon_url: Optional[str] = Field(None, max_length=1024)
    primary_color: Optional[str] = Field(None, max_length=32)
    accent_color: Optional[str] = Field(None, max_length=32)
    default_locale: Optional[str] = Field(None, pattern="^(en|ru|bg)$")
    support_email: Optional[str] = Field(None, max_length=320)
    support_url: Optional[str] = Field(None, max_length=1024)
    custom_css: Optional[str] = Field(None, max_length=50000)
    report_footer_html: Optional[str] = Field(None, max_length=10000)

    @field_validator("custom_css")
    @classmethod
    def no_js_in_css(cls, v: Optional[str]) -> Optional[str]:
        if v and ("<script" in v.lower() or "javascript:" in v.lower() or "expression(" in v.lower()):
            raise ValueError("custom_css must not contain script or javascript expressions")
        return v

    @field_validator("report_footer_html")
    @classmethod
    def no_script_in_footer(cls, v: Optional[str]) -> Optional[str]:
        if v and "<script" in v.lower():
            raise ValueError("report_footer_html must not contain script tags")
        return v


class WhiteLabelPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    product_display_name: Optional[str]
    logo_url: Optional[str]
    favicon_url: Optional[str]
    primary_color: Optional[str]
    accent_color: Optional[str]
    default_locale: str
    support_email: Optional[str]
    support_url: Optional[str]
    custom_css: Optional[str]
    report_footer_html: Optional[str]


@router.get("/{tenant_id}/white-label", response_model=WhiteLabelPublic)
async def get_white_label(
    tenant_id: UUID,
    user: CurrentUser,
    db: DbSession,
) -> WhiteLabelSettings:
    tenant = await db.scalar(select(Tenant).where(Tenant.id == tenant_id, Tenant.is_active.is_(True)))
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    try:
        await assert_org_member(db, user.id, tenant.organization_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    settings = await db.scalar(
        select(WhiteLabelSettings).where(WhiteLabelSettings.tenant_id == tenant_id)
    )
    if not settings:
        settings = WhiteLabelSettings(tenant_id=tenant_id, default_locale="en")
        db.add(settings)
        await db.flush()
    return settings


@router.put("/{tenant_id}/white-label", response_model=WhiteLabelPublic)
async def update_white_label(
    tenant_id: UUID,
    data: WhiteLabelUpdate,
    user: CurrentUser,
    db: DbSession,
) -> WhiteLabelSettings:
    tenant = await db.scalar(select(Tenant).where(Tenant.id == tenant_id, Tenant.is_active.is_(True)))
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    try:
        await assert_org_member(db, user.id, tenant.organization_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    member = await db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == tenant.organization_id,
            OrganizationMember.user_id == user.id,
        )
    )
    if not member or member.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Only owner or admin can update white-label settings")

    settings = await db.scalar(
        select(WhiteLabelSettings).where(WhiteLabelSettings.tenant_id == tenant_id)
    )
    if not settings:
        settings = WhiteLabelSettings(tenant_id=tenant_id, default_locale="en")
        db.add(settings)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)

    await db.flush()
    await db.commit()
    await db.refresh(settings)
    return settings
