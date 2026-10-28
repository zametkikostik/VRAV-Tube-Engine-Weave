"""Organization and tenant schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: Optional[str] = Field(None, max_length=100, pattern=r"^[a-z0-9][a-z0-9\-]*[a-z0-9]$")


class OrganizationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    owner_user_id: UUID
    billing_email: Optional[str]
    is_active: bool
    created_at: datetime


class MemberPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    role: str
    accepted_at: Optional[datetime]


class TenantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: Optional[str] = Field(None, max_length=100)


class TenantPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    slug: str
    is_platform_tenant: bool
    is_active: bool
    created_at: datetime
