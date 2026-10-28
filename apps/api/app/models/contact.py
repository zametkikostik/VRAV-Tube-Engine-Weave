"""Enterprise contact / lead submissions."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin


class ContactLead(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "contact_leads"

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    locale: Mapped[str] = mapped_column(String(8), default="en", nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="enterprise_form", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="NEW", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
