"""Public enterprise contact form + admin list."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.contact import ContactLead

router = APIRouter(tags=["contact"])


class ContactCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    company: Optional[str] = Field(None, max_length=255)
    message: str = Field(min_length=10, max_length=5000)
    locale: str = Field(default="en", max_length=8)


class ContactPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: str
    company: Optional[str]
    message: str
    locale: str
    source: str
    status: str


@router.post("/contact", response_model=dict, status_code=status.HTTP_201_CREATED)
async def submit_contact(data: ContactCreate, db: DbSession) -> dict:
    """Public endpoint — no auth. Rate-limited by global middleware."""
    lead = ContactLead(
        full_name=data.full_name.strip(),
        email=str(data.email).lower(),
        company=(data.company or "").strip() or None,
        message=data.message.strip(),
        locale=data.locale[:8],
        source="enterprise_form",
        status="NEW",
    )
    db.add(lead)
    await db.commit()
    return {"status": "received", "id": str(lead.id)}


@router.get("/admin/contact-leads", response_model=list[ContactPublic])
async def list_leads(user: CurrentUser, db: DbSession) -> list[ContactLead]:
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser required")
    rows = await db.scalars(
        select(ContactLead).order_by(ContactLead.created_at.desc()).limit(200)
    )
    return list(rows.all())
